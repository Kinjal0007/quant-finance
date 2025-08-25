"""
Data Ingestors Package

Contains ingestor classes for various data vendors:
- EODHD: End-of-day prices and corporate actions
- Twelve Data: Intraday, FX, and crypto data
"""

from .eodhd_ingestor import EODHDIngestor
from .twelve_data_ingestor import TwelveDataIngestor

__all__ = ["EODHDIngestor", "TwelveDataIngestor"]
