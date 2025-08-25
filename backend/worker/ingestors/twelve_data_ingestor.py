#!/usr/bin/env python3
"""
Twelve Data Ingestor

Fetches intraday prices, FX rates, and crypto data from Twelve Data API.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
import pandas as pd
from google.cloud import bigquery, secretmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwelveDataIngestor:
    """Ingestor for Twelve Data API."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT")
        self.dataset_raw = os.getenv("BQ_DATASET_RAW", "market_raw")
        self.table_eq = os.getenv("BQ_TABLE_EQ", "eq_ohlcv")
        self.table_fx = os.getenv("BQ_TABLE_FX", "fx_ohlcv")
        self.table_crypto = os.getenv("BQ_TABLE_CRYPTO", "crypto_ohlcv")
        self.table_vendor_map = os.getenv("BQ_TABLE_VENDOR_MAP", "vendor_symbol_map")
        
        # Initialize clients
        self.bq_client = bigquery.Client(project=self.project_id)
        self.secret_client = secretmanager.SecretManagerServiceClient()
        
        # Get API key from Secret Manager
        self.api_key = self._get_secret("TWELVE_DATA_API_KEY")
        self.base_url = "https://api.twelvedata.com"
        
    def _get_secret(self, secret_name: str) -> str:
        """Get secret from Secret Manager."""
        try:
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = self.secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Failed to get secret {secret_name}: {e}")
            return os.getenv(secret_name, "")
    
    async def fetch_prices(self, symbols: List[str], interval: str = "1h", 
                          start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Fetch OHLCV prices for given symbols."""
        all_data = []
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        
        async with httpx.AsyncClient() as client:
            for symbol in symbols:
                try:
                    url = f"{self.base_url}/time_series"
                    params = {
                        "symbol": symbol,
                        "interval": interval,
                        "start_date": start_date,
                        "end_date": end_date,
                        "apikey": self.api_key,
                        "format": "JSON"
                    }
                    
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    
                    data = response.json()
                    if data.get("status") == "ok" and data.get("values"):
                        df = pd.DataFrame(data["values"])
                        df['symbol'] = symbol
                        df['interval'] = interval
                        df['vendor'] = 'twelvedata'
                        df['created_at'] = datetime.utcnow()
                        all_data.append(df)
                        
                    logger.info(f"Fetched {len(data.get('values', []))} records for {symbol}")
                    
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
            'datetime': 'date',
            'open': 'open',
            'high': 'high', 
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'interval']
        for col in required_columns:
            if col not in df.columns:
                if col == 'adjusted_close':
                    df[col] = df['close']
                else:
                    df[col] = None
        
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Convert string values to float
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df[required_columns + ['vendor', 'created_at']]
    
    async def fetch_fx_rates(self, pairs: List[str], interval: str = "1h") -> pd.DataFrame:
        """Fetch FX rates for given currency pairs."""
        all_data = []
        
        async with httpx.AsyncClient() as client:
            for pair in pairs:
                try:
                    url = f"{self.base_url}/time_series"
                    params = {
                        "symbol": pair,
                        "interval": interval,
                        "apikey": self.api_key,
                        "format": "JSON"
                    }
                    
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    
                    data = response.json()
                    if data.get("status") == "ok" and data.get("values"):
                        df = pd.DataFrame(data["values"])
                        df['symbol'] = pair
                        df['interval'] = interval
                        df['vendor'] = 'twelvedata'
                        df['created_at'] = datetime.utcnow()
                        all_data.append(df)
                        
                    logger.info(f"Fetched {len(data.get('values', []))} FX records for {pair}")
                    
                except Exception as e:
                    logger.error(f"Failed to fetch FX rates for {pair}: {e}")
                    continue
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            return self._standardize_fx_data(combined_df)
        return pd.DataFrame()
    
    def _standardize_fx_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize FX data format."""
        # Rename columns to match our schema
        column_mapping = {
            'datetime': 'date',
            'open': 'open',
            'high': 'high', 
            'low': 'low',
            'close': 'close'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'interval']
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
        
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Convert string values to float
        numeric_columns = ['open', 'high', 'low', 'close']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df[required_columns + ['vendor', 'created_at']]
    
    async def fetch_crypto_data(self, symbols: List[str], interval: str = "1h") -> pd.DataFrame:
        """Fetch crypto data for given symbols."""
        all_data = []
        
        async with httpx.AsyncClient() as client:
            for symbol in symbols:
                try:
                    url = f"{self.base_url}/time_series"
                    params = {
                        "symbol": symbol,
                        "interval": interval,
                        "apikey": self.api_key,
                        "format": "JSON"
                    }
                    
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    
                    data = response.json()
                    if data.get("status") == "ok" and data.get("values"):
                        df = pd.DataFrame(data["values"])
                        df['symbol'] = symbol
                        df['interval'] = interval
                        df['vendor'] = 'twelvedata'
                        df['created_at'] = datetime.utcnow()
                        all_data.append(df)
                        
                    logger.info(f"Fetched {len(data.get('values', []))} crypto records for {symbol}")
                    
                except Exception as e:
                    logger.error(f"Failed to fetch crypto data for {symbol}: {e}")
                    continue
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            return self._standardize_crypto_data(combined_df)
        return pd.DataFrame()
    
    def _standardize_crypto_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize crypto data format."""
        # Rename columns to match our schema
        column_mapping = {
            'datetime': 'date',
            'open': 'open',
            'high': 'high', 
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'interval']
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
        
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Convert string values to float
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
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
    
    async def run_ingestion(self, symbols: List[str] = None, fx_pairs: List[str] = None, 
                           crypto_symbols: List[str] = None, interval: str = "1h"):
        """Run complete ingestion process."""
        logger.info("Starting Twelve Data ingestion")
        
        # Default symbols if none provided
        if not symbols:
            symbols = ["AAPL", "MSFT", "GOOGL"]
        if not fx_pairs:
            fx_pairs = ["EUR/USD", "GBP/USD", "USD/JPY"]
        if not crypto_symbols:
            crypto_symbols = ["BTC/USD", "ETH/USD"]
        
        # Fetch and load equity prices
        if symbols:
            prices_df = await self.fetch_prices(symbols, interval)
            if not prices_df.empty:
                self.load_to_bigquery(prices_df, self.table_eq)
        
        # Fetch and load FX rates
        if fx_pairs:
            fx_df = await self.fetch_fx_rates(fx_pairs, interval)
            if not fx_df.empty:
                self.load_to_bigquery(fx_df, self.table_fx)
        
        # Fetch and load crypto data
        if crypto_symbols:
            crypto_df = await self.fetch_crypto_data(crypto_symbols, interval)
            if not crypto_df.empty:
                self.load_to_bigquery(crypto_df, self.table_crypto)
        
        logger.info("Twelve Data ingestion completed")

async def main():
    """Main function for standalone execution."""
    ingestor = TwelveDataIngestor()
    
    # Example symbols and intervals
    symbols = ["AAPL", "MSFT", "GOOGL"]
    fx_pairs = ["EUR/USD", "GBP/USD"]
    crypto_symbols = ["BTC/USD", "ETH/USD"]
    
    await ingestor.run_ingestion(symbols, fx_pairs, crypto_symbols, "1h")

if __name__ == "__main__":
    asyncio.run(main())
