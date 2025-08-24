from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, continue without it

try:
    from google.cloud import bigquery
    from google.cloud import secretmanager
except Exception:  # pragma: no cover - local dev without GCP libs
    bigquery = None
    secretmanager = None


class Settings(BaseModel):
    gcp_project: str = Field(default_factory=lambda: os.getenv("GCP_PROJECT", ""))
    gcp_region: str = Field(default_factory=lambda: os.getenv("GCP_REGION", "europe-west3"))
    bq_dataset_raw: str = Field(default_factory=lambda: os.getenv("BQ_DATASET_RAW", "market_raw"))
    bq_table_eq: str = Field(default_factory=lambda: os.getenv("BQ_TABLE_EQ", "eq_ohlcv"))
    bq_table_fx: str = Field(default_factory=lambda: os.getenv("BQ_TABLE_FX", "fx_ohlcv"))
    bq_table_crypto: str = Field(default_factory=lambda: os.getenv("BQ_TABLE_CRYPTO", "crypto_ohlcv"))
    bq_table_vendor_map: str = Field(default_factory=lambda: os.getenv("BQ_TABLE_VENDOR_MAP", "vendor_symbol_map"))
    twelve_secret_name: Optional[str] = Field(default_factory=lambda: os.getenv("TWELVE_SECRET_NAME"))
    twelve_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("TWELVE_API_KEY"))
    http_timeout_seconds: int = Field(default=30)
    max_retries: int = Field(default=3)
    rps_limit: int = Field(default_factory=lambda: int(os.getenv("TWELVEDATA_RPS_LIMIT", "8")))


SETTINGS = Settings()
app = FastAPI(title="Twelve Data Ingestor Service", version="0.1.0")


def _get_twelve_api_key() -> str:
    if SETTINGS.twelve_api_key:
        return SETTINGS.twelve_api_key
    if SETTINGS.twelve_secret_name and secretmanager is not None:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{SETTINGS.gcp_project}/secrets/{SETTINGS.twelve_secret_name}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("utf-8")
    raise RuntimeError("Twelve Data API key not configured. Set TWELVE_API_KEY or TWELVE_SECRET_NAME.")


def _bq_client() -> "bigquery.Client":
    if bigquery is None:
        raise RuntimeError("google-cloud-bigquery is not installed. Install it to run ingestor.")
    return bigquery.Client(project=SETTINGS.gcp_project or None)


class IntradayPrice(BaseModel):
    datetime: str
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[int]


class FXRate(BaseModel):
    datetime: str
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]


class CryptoPrice(BaseModel):
    datetime: str
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[float]


class IngestResponse(BaseModel):
    symbol: str
    interval: str
    rows_written: int
    dataset: str
    table: str
    from_datetime: str
    to_datetime: str
    data_source: str = "twelve_data"


def _parse_intraday_response(data: Dict[str, Any]) -> List[IntradayPrice]:
    """Parse Twelve Data intraday API response."""
    prices = []
    values = data.get("values", [])
    
    for item in values:
        try:
            price = IntradayPrice(
                datetime=item.get("datetime", ""),
                open=float(item.get("open", 0)) if item.get("open") is not None else None,
                high=float(item.get("high", 0)) if item.get("high") is not None else None,
                low=float(item.get("low", 0)) if item.get("low") is not None else None,
                close=float(item.get("close", 0)) if item.get("close") is not None else None,
                volume=int(item.get("volume", 0)) if item.get("volume") is not None else None,
            )
            prices.append(price)
        except (ValueError, TypeError) as e:
            print(f"Warning: Skipping malformed intraday data: {item}, error: {e}")
            continue
    
    return prices


def _parse_fx_response(data: Dict[str, Any]) -> List[FXRate]:
    """Parse Twelve Data FX API response."""
    rates = []
    values = data.get("values", [])
    
    for item in values:
        try:
            rate = FXRate(
                datetime=item.get("datetime", ""),
                open=float(item.get("open", 0)) if item.get("open") is not None else None,
                high=float(item.get("high", 0)) if item.get("high") is not None else None,
                low=float(item.get("low", 0)) if item.get("low") is not None else None,
                close=float(item.get("close", 0)) if item.get("close") is not None else None,
            )
            rates.append(rate)
        except (ValueError, TypeError) as e:
            print(f"Warning: Skipping malformed FX data: {item}, error: {e}")
            continue
    
    return rates


def _parse_crypto_response(data: Dict[str, Any]) -> List[CryptoPrice]:
    """Parse Twelve Data crypto API response."""
    prices = []
    values = data.get("values", [])
    
    for item in values:
        try:
            price = CryptoPrice(
                datetime=item.get("datetime", ""),
                open=float(item.get("open", 0)) if item.get("open") is not None else None,
                high=float(item.get("high", 0)) if item.get("high") is not None else None,
                low=float(item.get("low", 0)) if item.get("low") is not None else None,
                close=float(item.get("close", 0)) if item.get("close") is not None else None,
                volume=float(item.get("volume", 0)) if item.get("volume") is not None else None,
            )
            prices.append(price)
        except (ValueError, TypeError) as e:
            print(f"Warning: Skipping malformed crypto data: {item}, error: {e}")
            continue
    
    return prices


def _intraday_to_bq_rows(symbol: str, interval: str, prices: List[IntradayPrice]) -> List[Dict[str, Any]]:
    """Convert intraday prices to unified BigQuery rows."""
    rows = []
    ingest_time_iso = datetime.now(timezone.utc).isoformat()
    
    for price in prices:
        # Parse datetime string to UTC timestamp
        try:
            # Twelve Data returns datetime in various formats, try to parse
            if 'T' in price.datetime:
                # ISO format: 2024-01-15T09:30:00
                ts_utc = datetime.fromisoformat(price.datetime.replace('Z', '+00:00'))
            else:
                # Standard format: 2024-01-15 09:30:00
                ts_utc = datetime.strptime(price.datetime, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            # Fallback to current time if parsing fails
            ts_utc = datetime.now(timezone.utc)
        
        row = {
            "symbol": symbol.upper(),
            "mic": "US",  # Default to US for Twelve Data equities
            "vendor": "twelve_data",
            "interval": interval,
            "ts_utc": ts_utc.isoformat(),
            "open": price.open,
            "high": price.high,
            "low": price.low,
            "close": price.close,
            "volume": price.volume,
            "ingest_time": ingest_time_iso,
        }
        rows.append(row)
    
    return rows


def _fx_to_bq_rows(symbol: str, interval: str, rates: List[FXRate]) -> List[Dict[str, Any]]:
    """Convert FX rates to BigQuery rows."""
    rows = []
    ingest_time_iso = datetime.now(timezone.utc).isoformat()
    
    for rate in rates:
        # Parse datetime string to UTC timestamp
        try:
            if 'T' in rate.datetime:
                ts_utc = datetime.fromisoformat(rate.datetime.replace('Z', '+00:00'))
            else:
                ts_utc = datetime.strptime(rate.datetime, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            ts_utc = datetime.now(timezone.utc)
        
        row = {
            "symbol": symbol.upper(),
            "vendor": "twelve_data",
            "interval": interval,
            "ts_utc": ts_utc.isoformat(),
            "open": rate.open,
            "high": rate.high,
            "low": rate.low,
            "close": rate.close,
            "ingest_time": ingest_time_iso,
        }
        rows.append(row)
    
    return rows


def _crypto_to_bq_rows(symbol: str, interval: str, prices: List[CryptoPrice]) -> List[Dict[str, Any]]:
    """Convert crypto prices to BigQuery rows."""
    rows = []
    ingest_time_iso = datetime.now(timezone.utc).isoformat()
    
    for price in prices:
        # Parse datetime string to UTC timestamp
        try:
            if 'T' in price.datetime:
                ts_utc = datetime.fromisoformat(price.datetime.replace('Z', '+00:00'))
            else:
                ts_utc = datetime.strptime(price.datetime, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            ts_utc = datetime.now(timezone.utc)
        
        row = {
            "symbol": symbol.upper(),
            "vendor": "twelve_data",
            "interval": interval,
            "ts_utc": ts_utc.isoformat(),
            "open": price.open,
            "high": price.high,
            "low": price.low,
            "close": price.close,
            "volume": price.volume,
            "ingest_time": ingest_time_iso,
        }
        rows.append(row)
    
    return rows


def _update_vendor_symbol_map(symbol: str, asset_type: str, mic: str = "US"):
    """Update vendor symbol mapping table."""
    client = _bq_client()
    table_id = f"{client.project}.{SETTINGS.bq_dataset_raw}.{SETTINGS.bq_table_vendor_map}"
    
    # Check if mapping already exists
    query = f"""
    SELECT COUNT(*) as count 
    FROM `{table_id}` 
    WHERE vendor = 'twelve_data' AND symbol = '{symbol}' AND asset_type = '{asset_type}'
    """
    
    try:
        query_job = client.query(query)
        results = list(query_job.result())
        exists = results[0].count > 0
        
        if not exists:
            # Insert new mapping
            row = {
                "vendor": "twelve_data",
                "vendor_symbol": symbol,
                "symbol": f"{symbol}.{mic}" if asset_type == "equity" else symbol,
                "mic": mic.upper() if asset_type == "equity" else "N/A",
                "exchange_name": "Twelve Data",
                "asset_type": asset_type,
                "is_active": True,
                "ingest_time": datetime.now(timezone.utc).isoformat(),
            }
            
            errors = client.insert_rows_json(table_id, [row])
            if errors:
                print(f"Warning: Failed to insert vendor symbol mapping: {errors}")
                
    except Exception as e:
        print(f"Warning: Failed to update vendor symbol mapping: {e}")


async def _fetch_twelve_data(
    symbol: str, 
    interval: str, 
    start_date: str, 
    end_date: str,
    data_type: str = "time_series"
) -> Dict[str, Any]:
    """Fetch data from Twelve Data API with retry logic and rate limiting."""
    api_key = _get_twelve_api_key()
    url = "https://api.twelvedata.com/time_series"
    
    params = {
        "symbol": symbol,
        "interval": interval,
        "start_date": start_date,
        "end_date": end_date,
        "apikey": api_key,
        "format": "JSON",
    }
    
    # Rate limiting
    time.sleep(1.0 / SETTINGS.rps_limit)
    
    for attempt in range(SETTINGS.max_retries):
        try:
            async with httpx.AsyncClient(timeout=SETTINGS.http_timeout_seconds) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check for API errors
                    if "status" in data and data["status"] == "error":
                        raise HTTPException(status_code=400, detail=f"Twelve Data API error: {data.get('message', 'Unknown error')}")
                    
                    if "values" not in data:
                        raise HTTPException(status_code=502, detail="Unexpected Twelve Data response format")
                    
                    return data
                    
                elif response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Twelve Data API key invalid or expired")
                elif response.status_code == 429:
                    if attempt < SETTINGS.max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        time.sleep(wait_time)
                        continue
                    else:
                        raise HTTPException(status_code=429, detail="Twelve Data rate limit exceeded")
                else:
                    raise HTTPException(status_code=response.status_code, detail=f"Twelve Data error: {response.text}")
                    
        except httpx.TimeoutException:
            if attempt < SETTINGS.max_retries - 1:
                continue
            raise HTTPException(status_code=408, detail="Twelve Data API timeout")
        except Exception as e:
            if attempt < SETTINGS.max_retries - 1:
                continue
            raise HTTPException(status_code=500, detail=f"Twelve Data API error: {str(e)}")
    
    raise HTTPException(status_code=500, detail="Max retries exceeded")


def _write_to_bigquery(rows: List[Dict[str, Any]], table_name: str) -> int:
    """Write rows to BigQuery table."""
    if not rows:
        return 0
    
    client = _bq_client()
    table_id = f"{client.project}.{SETTINGS.bq_dataset_raw}.{table_name}"
    
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        error_details = str(errors[:3]) if len(errors) > 3 else str(errors)
        raise HTTPException(status_code=500, detail=f"BigQuery insert errors: {error_details}")
    
    return len(rows)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "ingestor_twelve", "version": "0.1.0"}


@app.post("/v1/ingest/twelve/intraday")
async def ingest_intraday_prices_batch(
    symbols: List[Dict[str, str]] = Field(..., description="List of {symbol, interval, start_date, end_date}")
) -> List[IngestResponse]:
    """Batch ingest intraday prices from Twelve Data for multiple symbols."""
    
    results = []
    
    for symbol_data in symbols:
        symbol = symbol_data.get("symbol")
        interval = symbol_data.get("interval", "1min")
        start_date = symbol_data.get("start_date")
        end_date = symbol_data.get("end_date")
        
        if not all([symbol, start_date, end_date]):
            continue
            
        try:
            # Validate date format
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                continue
            
            # Fetch data from Twelve Data
            raw_data = await _fetch_twelve_data(symbol, interval, start_date, end_date)
            
            if not raw_data.get("values"):
                results.append(IngestResponse(
                    symbol=symbol,
                    interval=interval,
                    rows_written=0,
                    dataset=SETTINGS.bq_dataset_raw,
                    table=SETTINGS.bq_table_eq,
                    from_datetime=start_date,
                    to_datetime=end_date,
                ))
                continue
            
            # Parse and validate data
            prices = _parse_intraday_response(raw_data)
            
            # Write to BigQuery
            rows = _intraday_to_bq_rows(symbol, interval, prices)
            written = _write_to_bigquery(rows, SETTINGS.bq_table_eq)
            
            # Update vendor symbol mapping
            _update_vendor_symbol_map(symbol, "equity")
            
            results.append(IngestResponse(
                symbol=symbol,
                interval=interval,
                rows_written=written,
                dataset=SETTINGS.bq_dataset_raw,
                table=SETTINGS.bq_table_eq,
                from_datetime=start_date,
                to_datetime=end_date,
            ))
            
        except Exception as e:
            print(f"Error processing {symbol} {interval}: {e}")
            results.append(IngestResponse(
                symbol=symbol,
                interval=interval,
                rows_written=0,
                dataset=SETTINGS.bq_dataset_raw,
                table=SETTINGS.bq_table_eq,
                from_datetime=start_date,
                to_datetime=end_date,
            ))
    
    return results


@app.get("/v1/ingest/twelve/intraday")
async def ingest_intraday_prices_single(
    symbol: str = Query(..., description="Stock symbol, e.g., AAPL"),
    interval: str = Query("1min", description="Interval: 1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month"),
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
) -> IngestResponse:
    """Single symbol intraday ingest endpoint for backward compatibility."""
    
    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Fetch data from Twelve Data
    raw_data = await _fetch_twelve_data(symbol, interval, start_date, end_date)
    
    if not raw_data.get("values"):
        return IngestResponse(
            symbol=symbol,
            interval=interval,
            rows_written=0,
            dataset=SETTINGS.bq_dataset_raw,
            table=SETTINGS.bq_table_eq,
            from_datetime=start_date,
            to_datetime=end_date,
        )
    
    # Parse and validate data
    prices = _parse_intraday_response(raw_data)
    
    # Write to BigQuery
    rows = _intraday_to_bq_rows(symbol, interval, prices)
    written = _write_to_bigquery(rows, SETTINGS.bq_table_eq)
    
    # Update vendor symbol mapping
    _update_vendor_symbol_map(symbol, "equity")
    
    return IngestResponse(
        symbol=symbol,
        interval=interval,
        rows_written=written,
        dataset=SETTINGS.bq_dataset_raw,
        table=SETTINGS.bq_table_eq,
        from_datetime=start_date,
        to_datetime=end_date,
    )


@app.post("/v1/ingest/twelve/fx")
async def ingest_fx_rates_batch(
    symbols: List[Dict[str, str]] = Field(..., description="List of {symbol, interval, start_date, end_date}")
) -> List[IngestResponse]:
    """Batch ingest FX rates from Twelve Data for multiple symbols."""
    
    results = []
    
    for symbol_data in symbols:
        symbol = symbol_data.get("symbol")
        interval = symbol_data.get("interval", "1h")
        start_date = symbol_data.get("start_date")
        end_date = symbol_data.get("end_date")
        
        if not all([symbol, start_date, end_date]):
            continue
            
        try:
            # Validate date format
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                continue
            
            # Fetch data from Twelve Data
            raw_data = await _fetch_twelve_data(symbol, interval, start_date, end_date)
            
            if not raw_data.get("values"):
                results.append(IngestResponse(
                    symbol=symbol,
                    interval=interval,
                    rows_written=0,
                    dataset=SETTINGS.bq_dataset_raw,
                    table=SETTINGS.bq_table_fx,
                    from_datetime=start_date,
                    to_datetime=end_date,
                ))
                continue
            
            # Parse and validate data
            rates = _parse_fx_response(raw_data)
            
            # Write to BigQuery
            rows = _fx_to_bq_rows(symbol, interval, rates)
            written = _write_to_bigquery(rows, SETTINGS.bq_table_fx)
            
            # Update vendor symbol mapping
            _update_vendor_symbol_map(symbol, "fx")
            
            results.append(IngestResponse(
                symbol=symbol,
                interval=interval,
                rows_written=written,
                dataset=SETTINGS.bq_dataset_raw,
                table=SETTINGS.bq_table_fx,
                from_datetime=start_date,
                to_datetime=end_date,
            ))
            
        except Exception as e:
            print(f"Error processing FX {symbol} {interval}: {e}")
            results.append(IngestResponse(
                symbol=symbol,
                interval=interval,
                rows_written=0,
                dataset=SETTINGS.bq_dataset_raw,
                table=SETTINGS.bq_table_fx,
                from_datetime=start_date,
                to_datetime=end_date,
            ))
    
    return results


@app.get("/v1/ingest/twelve/fx")
async def ingest_fx_rates_single(
    symbol: str = Query(..., description="FX pair, e.g., EUR/USD"),
    interval: str = Query("1h", description="Interval: 1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month"),
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
) -> IngestResponse:
    """Single FX pair ingest endpoint for backward compatibility."""
    
    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Fetch data from Twelve Data
    raw_data = await _fetch_twelve_data(symbol, interval, start_date, end_date)
    
    if not raw_data.get("values"):
        return IngestResponse(
            symbol=symbol,
            interval=interval,
            rows_written=0,
            dataset=SETTINGS.bq_dataset_raw,
            table=SETTINGS.bq_table_fx,
            from_datetime=start_date,
            to_datetime=end_date,
        )
    
    # Parse and validate data
    rates = _parse_fx_response(raw_data)
    
    # Write to BigQuery
    rows = _fx_to_bq_rows(symbol, interval, rates)
    written = _write_to_bigquery(rows, SETTINGS.bq_table_fx)
    
    # Update vendor symbol mapping
    _update_vendor_symbol_map(symbol, "fx")
    
    return IngestResponse(
        symbol=symbol,
        interval=interval,
        rows_written=written,
        dataset=SETTINGS.bq_dataset_raw,
        table=SETTINGS.bq_table_fx,
        from_datetime=start_date,
        to_datetime=end_date,
    )


@app.post("/v1/ingest/twelve/crypto")
async def ingest_crypto_prices_batch(
    symbols: List[Dict[str, str]] = Field(..., description="List of {symbol, interval, start_date, end_date}")
) -> List[IngestResponse]:
    """Batch ingest crypto prices from Twelve Data for multiple symbols."""
    
    results = []
    
    for symbol_data in symbols:
        symbol = symbol_data.get("symbol")
        interval = symbol_data.get("interval", "1h")
        start_date = symbol_data.get("start_date")
        end_date = symbol_data.get("end_date")
        
        if not all([symbol, start_date, end_date]):
            continue
            
        try:
            # Validate date format
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                continue
            
            # Fetch data from Twelve Data
            raw_data = await _fetch_twelve_data(symbol, interval, start_date, end_date)
            
            if not raw_data.get("values"):
                results.append(IngestResponse(
                    symbol=symbol,
                    interval=interval,
                    rows_written=0,
                    dataset=SETTINGS.bq_dataset_raw,
                    table=SETTINGS.bq_table_crypto,
                    from_datetime=start_date,
                    to_datetime=end_date,
                ))
                continue
            
            # Parse and validate data
            prices = _parse_crypto_response(raw_data)
            
            # Write to BigQuery
            rows = _crypto_to_bq_rows(symbol, interval, prices)
            written = _write_to_bigquery(rows, SETTINGS.bq_table_crypto)
            
            # Update vendor symbol mapping
            _update_vendor_symbol_map(symbol, "crypto")
            
            results.append(IngestResponse(
                symbol=symbol,
                interval=interval,
                rows_written=written,
                dataset=SETTINGS.bq_dataset_raw,
                table=SETTINGS.bq_table_crypto,
                from_datetime=start_date,
                to_datetime=end_date,
            ))
            
        except Exception as e:
            print(f"Error processing crypto {symbol} {interval}: {e}")
            results.append(IngestResponse(
                symbol=symbol,
                interval=interval,
                rows_written=0,
                dataset=SETTINGS.bq_dataset_raw,
                table=SETTINGS.bq_table_crypto,
                from_datetime=start_date,
                to_datetime=end_date,
            ))
    
    return results


@app.get("/v1/ingest/twelve/crypto")
async def ingest_crypto_prices_single(
    symbol: str = Query(..., description="Crypto symbol, e.g., BTC/USD"),
    interval: str = Query("1h", description="Interval: 1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month"),
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
) -> IngestResponse:
    """Single crypto symbol ingest endpoint for backward compatibility."""
    
    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Fetch data from Twelve Data
    raw_data = await _fetch_twelve_data(symbol, interval, start_date, end_date)
    
    if not raw_data.get("values"):
        return IngestResponse(
            symbol=symbol,
            interval=interval,
            rows_written=0,
            dataset=SETTINGS.bq_dataset_raw,
            table=SETTINGS.bq_table_crypto,
            from_datetime=start_date,
            to_datetime=end_date,
        )
    
    # Parse and validate data
    prices = _parse_crypto_response(raw_data)
    
    # Write to BigQuery
    rows = _crypto_to_bq_rows(symbol, interval, prices)
    written = _write_to_bigquery(rows, SETTINGS.bq_table_crypto)
    
    # Update vendor symbol mapping
    _update_vendor_symbol_map(symbol, "crypto")
    
    return IngestResponse(
        symbol=symbol,
        interval=interval,
        rows_written=written,
        dataset=SETTINGS.bq_dataset_raw,
        table=SETTINGS.bq_table_crypto,
        from_datetime=start_date,
        to_datetime=end_date,
    )


# Entrypoint for local run: uvicorn app.main:app --reload --port 8080
