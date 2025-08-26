from __future__ import annotations

import os
from datetime import datetime
from typing import List

import pandas as pd

try:
    from google.cloud import bigquery

    BQ_AVAILABLE = True
except ImportError:
    BQ_AVAILABLE = False
    print(
        "Warning: google-cloud-bigquery not available. BigQuery functionality disabled."
    )

try:
    from .demo_loader import load_fixture_prices, should_use_fixture

    FIXTURE_AVAILABLE = True
except ImportError:
    FIXTURE_AVAILABLE = False
    print("Warning: demo_loader not available. Fixture functionality disabled.")


class BigQueryLoader:
    """Loader for BigQuery data in the worker service."""

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT")
        self.dataset_raw = os.getenv("BQ_DATASET_RAW", "market_raw")
        self.dataset_curated = os.getenv("BQ_DATASET_CURATED", "market_curated")

        if not self.project_id:
            raise ValueError("GCP_PROJECT environment variable is required")

        if BQ_AVAILABLE:
            self.client = bigquery.Client(project=self.project_id)
        else:
            self.client = None

    def load_prices(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        interval: str = "1d",
        adjusted: bool = True,
        vendor: str = "eodhd",
    ) -> pd.DataFrame:
        """
        Load price data from BigQuery or fixture data.

        Args:
            symbols: List of symbols to load
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval (1d, 1min, 5min, etc.)
            adjusted: Whether to use adjusted prices (for equities)
            vendor: Data vendor preference

        Returns:
            DataFrame with prices in wide format (symbols as columns)
        """
        # Check if fixture mode is enabled
        if FIXTURE_AVAILABLE and should_use_fixture():
            try:
                print(f"Using fixture data for symbols: {symbols}")
                return load_fixture_prices(
                    symbols, start_date, end_date, interval, adjusted
                )
            except Exception as e:
                print(
                    f"Warning: Failed to load fixture data: {e}. "
                    f"Falling back to BigQuery."
                )

        # Fall back to BigQuery
        if not self.client:
            raise RuntimeError("BigQuery client not available")

        # Convert dates to datetime
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Build query based on data type and interval
        if interval == "1d" and adjusted:
            # Use adjusted prices view for daily data
            query = self._build_adjusted_prices_query(symbols, start_dt, end_dt, vendor)
        else:
            # Use raw prices table
            query = self._build_raw_prices_query(
                symbols, start_dt, end_dt, interval, vendor
            )

        try:
            # Execute query
            df = self.client.query(query).to_dataframe()

            if df.empty:
                raise ValueError(
                    f"No data found for symbols {symbols} in date range "
                    f"{start_date} to {end_date}"
                )

            # Pivot to wide format
            df_wide = self._pivot_to_wide_format(df, interval)

            return df_wide

        except Exception as e:
            raise RuntimeError(f"Failed to load prices from BigQuery: {e}")

    def _build_adjusted_prices_query(
        self, symbols: List[str], start_dt: datetime, end_dt: datetime, vendor: str
    ) -> str:
        """Build query for adjusted prices view."""
        symbols_str = ", ".join([f"'{s}'" for s in symbols])

        query = f"""
        SELECT
            ts_utc,
            symbol,
            adj_close as close
        FROM `{self.project_id}.{self.dataset_curated}.v_adjusted_prices`
        WHERE symbol IN ({symbols_str})
        AND vendor = '{vendor}'
        AND ts_utc >= TIMESTAMP('{start_dt.isoformat()}')
        AND ts_utc <= TIMESTAMP('{end_dt.isoformat()}')
        ORDER BY ts_utc, symbol
        """

        return query

    def _build_raw_prices_query(
        self,
        symbols: List[str],
        start_dt: datetime,
        end_dt: datetime,
        interval: str,
        vendor: str,
    ) -> str:
        """Build query for raw prices table."""
        symbols_str = ", ".join([f"'{s}'" for s in symbols])

        query = f"""
        SELECT
            ts_utc,
            symbol,
            close
        FROM `{self.project_id}.{self.dataset_raw}.eq_ohlcv`
        WHERE symbol IN ({symbols_str})
        AND vendor = '{vendor}'
        AND interval = '{interval}'
        AND ts_utc >= TIMESTAMP('{start_dt.isoformat()}')
        AND ts_utc <= TIMESTAMP('{end_dt.isoformat()}')
        ORDER BY ts_utc, symbol
        """

        return query

    def _pivot_to_wide_format(self, df: pd.DataFrame, interval: str) -> pd.DataFrame:
        """Convert long format DataFrame to wide format with symbols as columns."""
        # Ensure ts_utc is datetime
        df["ts_utc"] = pd.to_datetime(df["ts_utc"])

        # Pivot to wide format
        df_wide = df.pivot(index="ts_utc", columns="symbol", values="close")

        # Forward fill missing values (for intraday data)
        if interval != "1d":
            df_wide = df_wide.fillna(method="ffill")

        # Drop rows with all NaN values
        df_wide = df_wide.dropna(how="all")

        # Sort by timestamp
        df_wide = df_wide.sort_index()

        return df_wide

    def to_returns(self, df_prices: pd.DataFrame, method: str = "log") -> pd.DataFrame:
        """
        Convert prices to returns.

        Args:
            df_prices: DataFrame with prices (timestamps as index, symbols as columns)
            method: Return calculation method ('log' or 'simple')

        Returns:
            DataFrame with returns
        """
        if method == "log":
            # Log returns: log(P_t / P_{t-1})
            returns = df_prices.pct_change().dropna()
        elif method == "simple":
            # Simple returns: (P_t - P_{t-1}) / P_{t-1}
            returns = df_prices.pct_change().dropna()
        else:
            raise ValueError("Method must be 'log' or 'simple'")

        return returns

    def get_symbol_info(self, symbols: List[str]) -> pd.DataFrame:
        """Get basic information about symbols."""
        if not self.client:
            raise RuntimeError("BigQuery client not available")

        symbols_str = ", ".join([f"'{s}'" for s in symbols])

        query = f"""
        SELECT
            symbol,
            mic,
            vendor,
            asset_type,
            is_active
        FROM `{self.project_id}.{self.dataset_raw}.vendor_symbol_map`
        WHERE symbol IN ({symbols_str})
        AND is_active = true
        """

        try:
            df = self.client.query(query).to_dataframe()
            return df
        except Exception as e:
            print(f"Warning: Failed to get symbol info: {e}")
            return pd.DataFrame()


# Global loader instance
bq_loader = BigQueryLoader()


def get_bq_loader() -> BigQueryLoader:
    """Get BigQuery loader instance."""
    return bq_loader
