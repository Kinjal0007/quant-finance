#!/usr/bin/env python3
"""
EOD Historical Data (EODHD) Ingestor

Fetches end-of-day prices, corporate actions, and fundamentals from EODHD API.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
import pandas as pd
from google.cloud import bigquery, secretmanager
from google.cloud.exceptions import NotFound

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EODHDIngestor:
    """Ingestor for EOD Historical Data API."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT")
        self.dataset_raw = os.getenv("BQ_DATASET_RAW", "market_raw")
        self.table_eq = os.getenv("BQ_TABLE_EQ", "eq_ohlcv")
        self.table_corp_actions = os.getenv("BQ_TABLE_CORP_ACTIONS", "corporate_actions")
        self.table_vendor_map = os.getenv("BQ_TABLE_VENDOR_MAP", "vendor_symbol_map")
        
        # Initialize clients
        self.bq_client = bigquery.Client(project=self.project_id)
        self.secret_client = secretmanager.SecretManagerServiceClient()
        
        # Get API key from Secret Manager
        self.api_key = self._get_secret("EODHD_API_KEY")
        self.base_url = "https://eodhd.com/api"
        
    def _get_secret(self, secret_name: str) -> str:
        """Get secret from Secret Manager."""
        try:
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = self.secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Failed to get secret {secret_name}: {e}")
            return os.getenv(secret_name, "")
    
    async def fetch_prices(self, symbols: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch OHLCV prices for given symbols."""
        all_data = []
        
        async with httpx.AsyncClient() as client:
            for symbol in symbols:
                try:
                    url = f"{self.base_url}/eod/{symbol}"
                    params = {
                        "from": start_date,
                        "to": end_date,
                        "api_token": self.api_key,
                        "fmt": "json"
                    }
                    
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    
                    data = response.json()
                    if data:
                        df = pd.DataFrame(data)
                        df['symbol'] = symbol
                        df['vendor'] = 'eodhd'
                        df['created_at'] = datetime.utcnow()
                        all_data.append(df)
                        
                    logger.info(f"Fetched {len(data)} records for {symbol}")
                    
                except Exception as e:
                    logger.error(f"Failed to fetch prices for {symbol}: {e}")
                    continue
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            return self._standardize_prices(combined_df)
        return pd.DataFrame()
    
    def _standardize_prices(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize price data format."""
        # Rename columns to match our schema
        column_mapping = {
            'date': 'date',
            'open': 'open',
            'high': 'high', 
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
            'adjusted_close': 'adjusted_close'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'adjusted_close']
        for col in required_columns:
            if col not in df.columns:
                if col == 'adjusted_close':
                    df[col] = df['close']
                else:
                    df[col] = None
        
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        return df[required_columns + ['vendor', 'created_at']]
    
    async def fetch_corporate_actions(self, symbols: List[str]) -> pd.DataFrame:
        """Fetch corporate actions for given symbols."""
        all_data = []
        
        async with httpx.AsyncClient() as client:
            for symbol in symbols:
                try:
                    url = f"{self.base_url}/div/{symbol}"
                    params = {
                        "api_token": self.api_key,
                        "fmt": "json"
                    }
                    
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    
                    data = response.json()
                    if data:
                        df = pd.DataFrame(data)
                        df['symbol'] = symbol
                        df['vendor'] = 'eodhd'
                        df['created_at'] = datetime.utcnow()
                        all_data.append(df)
                        
                    logger.info(f"Fetched {len(data)} corporate actions for {symbol}")
                    
                except Exception as e:
                    logger.error(f"Failed to fetch corporate actions for {symbol}: {e}")
                    continue
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            return self._standardize_corporate_actions(combined_df)
        return pd.DataFrame()
    
    def _standardize_corporate_actions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize corporate actions data format."""
        # Rename columns to match our schema
        column_mapping = {
            'date': 'date',
            'amount': 'amount',
            'currency': 'currency',
            'type': 'action_type'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_columns = ['date', 'symbol', 'amount', 'currency', 'action_type']
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
        
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        return df[required_columns + ['vendor', 'created_at']]
    
    def load_to_bigquery(self, df: pd.DataFrame, table_name: str) -> bool:
        """Load data to BigQuery."""
        try:
            table_id = f"{self.project_id}.{self.dataset_raw}.{table_name}"
            
            # Configure load job
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                schema_update_options=[
                    bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION
                ]
            )
            
            # Load data
            job = self.bq_client.load_table_from_dataframe(
                df, table_id, job_config=job_config
            )
            job.result()  # Wait for job to complete
            
            logger.info(f"Successfully loaded {len(df)} rows to {table_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load data to BigQuery: {e}")
            return False
    
    async def run_ingestion(self, symbols: List[str], start_date: str, end_date: str):
        """Run complete ingestion process."""
        logger.info(f"Starting EODHD ingestion for {len(symbols)} symbols")
        
        # Fetch and load prices
        prices_df = await self.fetch_prices(symbols, start_date, end_date)
        if not prices_df.empty:
            self.load_to_bigquery(prices_df, self.table_eq)
        
        # Fetch and load corporate actions
        corp_actions_df = await self.fetch_corporate_actions(symbols)
        if not corp_actions_df.empty:
            self.load_to_bigquery(corp_actions_df, self.table_corp_actions)
        
        logger.info("EODHD ingestion completed")

async def main():
    """Main function for standalone execution."""
    ingestor = EODHDIngestor()
    
    # Example symbols and dates
    symbols = ["AAPL", "MSFT", "GOOGL"]
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    await ingestor.run_ingestion(symbols, start_date, end_date)

if __name__ == "__main__":
    asyncio.run(main())
