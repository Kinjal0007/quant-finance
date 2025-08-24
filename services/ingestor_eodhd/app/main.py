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
    bq_table_corp_actions: str = Field(default_factory=lambda: os.getenv("BQ_TABLE_CORP_ACTIONS", "corporate_actions"))
    bq_table_vendor_map: str = Field(default_factory=lambda: os.getenv("BQ_TABLE_VENDOR_MAP", "vendor_symbol_map"))
    eodhd_secret_name: Optional[str] = Field(default_factory=lambda: os.getenv("EODHD_SECRET_NAME"))
    eodhd_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("EODHD_API_KEY"))
    http_timeout_seconds: int = Field(default=30)
    max_retries: int = Field(default=3)
    rps_limit: int = Field(default_factory=lambda: int(os.getenv("EODHD_RPS_LIMIT", "10")))


SETTINGS = Settings()
app = FastAPI(title="EODHD Ingestor Service", version="0.1.0")


def _get_eodhd_api_key() -> str:
    if SETTINGS.eodhd_api_key:
        return SETTINGS.eodhd_api_key
    if SETTINGS.eodhd_secret_name and secretmanager is not None:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{SETTINGS.gcp_project}/secrets/{SETTINGS.eodhd_secret_name}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("utf-8")
    raise RuntimeError("EODHD API key not configured. Set EODHD_API_KEY or EODHD_SECRET_NAME.")


def _bq_client() -> "bigquery.Client":
    if bigquery is None:
        raise RuntimeError("google-cloud-bigquery is not installed. Install it to run ingestor.")
    return bigquery.Client(project=SETTINGS.gcp_project or None)


class EODPrice(BaseModel):
    date: str
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    adjusted_close: Optional[float]
    volume: Optional[int]
    split_factor: Optional[float] = 1.0


class CorporateAction(BaseModel):
    symbol: str
    mic: str
    ex_date: str
    split_ratio: Optional[float] = None
    cash_dividend: Optional[float] = None
    adj_factor: float = 1.0


class IngestResponse(BaseModel):
    symbol: str
    mic: str
    rows_written: int
    corp_actions_written: int
    dataset: str
    table: str
    from_date: str
    to_date: str
    data_source: str = "eodhd"


def _parse_eodhd_response(data: List[Dict[str, Any]]) -> List[EODPrice]:
    """Parse EODHD API response into structured data."""
    prices = []
    for item in data:
        try:
            price = EODPrice(
                date=item.get("date", ""),
                open=float(item.get("open", 0)) if item.get("open") is not None else None,
                high=float(item.get("high", 0)) if item.get("high") is not None else None,
                low=float(item.get("low", 0)) if item.get("low") is not None else None,
                close=float(item.get("close", 0)) if item.get("close") is not None else None,
                adjusted_close=float(item.get("adjusted_close", 0)) if item.get("adjusted_close") is not None else None,
                volume=int(item.get("volume", 0)) if item.get("volume") is not None else None,
                split_factor=float(item.get("split_factor", 1.0)) if item.get("split_factor") is not None else 1.0,
            )
            prices.append(price)
        except (ValueError, TypeError) as e:
            # Log malformed data but continue processing
            print(f"Warning: Skipping malformed price data: {item}, error: {e}")
            continue
    return prices


def _prices_to_bq_rows(symbol: str, mic: str, prices: List[EODPrice]) -> List[Dict[str, Any]]:
    """Convert EOD prices to unified BigQuery rows."""
    rows = []
    ingest_time_iso = datetime.now(timezone.utc).isoformat()
    
    for price in prices:
        # Convert date string to UTC timestamp
        try:
            # EODHD returns dates in YYYY-MM-DD format, assume market close time
            date_obj = datetime.strptime(price.date, "%Y-%m-%d")
            # Set to market close time (varies by exchange, use 16:00 UTC as default)
            ts_utc = date_obj.replace(hour=16, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        except ValueError:
            # Fallback to current time if date parsing fails
            ts_utc = datetime.now(timezone.utc)
        
        row = {
            "symbol": symbol.upper(),
            "mic": mic.upper(),
            "vendor": "eodhd",
            "interval": "1d",
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


def _extract_corporate_actions(symbol: str, mic: str, prices: List[EODPrice]) -> List[Dict[str, Any]]:
    """Extract corporate actions from price data."""
    actions = []
    ingest_time_iso = datetime.now(timezone.utc).isoformat()
    
    for price in prices:
        if price.split_factor != 1.0 or (price.adjusted_close and price.close and 
                                        abs(price.adjusted_close - price.close) > 0.001):
            
            # Calculate adjustment factor
            if price.adjusted_close and price.close and price.close != 0:
                adj_factor = price.adjusted_close / price.close
            else:
                adj_factor = 1.0 / price.split_factor if price.split_factor != 1.0 else 1.0
            
            action = {
                "symbol": symbol.upper(),
                "mic": mic.upper(),
                "ex_date": price.date,
                "split_ratio": price.split_factor if price.split_factor != 1.0 else None,
                "cash_dividend": None,  # EODHD doesn't provide dividend info in basic endpoint
                "adj_factor": adj_factor,
                "vendor": "eodhd",
                "ingest_time": ingest_time_iso,
            }
            actions.append(action)
    
    return actions


def _write_to_bigquery(rows: List[Dict[str, Any]], table_name: str) -> int:
    """Write rows to BigQuery table."""
    if not rows:
        return 0
    
    client = _bq_client()
    table_id = f"{client.project}.{SETTINGS.bq_dataset_raw}.{table_name}"
    
    # Use insert_rows_json for better error handling
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        # Log first few errors for debugging
        error_details = str(errors[:3]) if len(errors) > 3 else str(errors)
        raise HTTPException(status_code=500, detail=f"BigQuery insert errors: {error_details}")
    
    return len(rows)


def _update_vendor_symbol_map(symbol: str, mic: str, exchange_name: str = None):
    """Update vendor symbol mapping table."""
    client = _bq_client()
    table_id = f"{client.project}.{SETTINGS.bq_dataset_raw}.{SETTINGS.bq_table_vendor_map}"
    
    # Check if mapping already exists
    query = f"""
    SELECT COUNT(*) as count 
    FROM `{table_id}` 
    WHERE vendor = 'eodhd' AND symbol = '{symbol}' AND mic = '{mic}'
    """
    
    try:
        query_job = client.query(query)
        results = list(query_job.result())
        exists = results[0].count > 0
        
        if not exists:
            # Insert new mapping
            row = {
                "vendor": "eodhd",
                "vendor_symbol": symbol,
                "symbol": f"{symbol}.{mic}",
                "mic": mic.upper(),
                "exchange_name": exchange_name or mic.upper(),
                "asset_type": "equity",
                "is_active": True,
                "ingest_time": datetime.now(timezone.utc).isoformat(),
            }
            
            errors = client.insert_rows_json(table_id, [row])
            if errors:
                print(f"Warning: Failed to insert vendor symbol mapping: {errors}")
                
    except Exception as e:
        print(f"Warning: Failed to update vendor symbol mapping: {e}")


async def _fetch_eodhd_data(symbol: str, mic: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
    """Fetch EOD data from EODHD API with retry logic and rate limiting."""
    api_key = _get_eodhd_api_key()
    url = "https://eodhd.com/api/eod"
    
    params = {
        "s": f"{symbol}.{mic}",
        "from": from_date,
        "to": to_date,
        "fmt": "json",
        "api_token": api_key,
    }
    
    # Rate limiting
    time.sleep(1.0 / SETTINGS.rps_limit)
    
    for attempt in range(SETTINGS.max_retries):
        try:
            async with httpx.AsyncClient(timeout=SETTINGS.http_timeout_seconds) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and "error" in data:
                        raise HTTPException(status_code=400, detail=f"EODHD API error: {data['error']}")
                    else:
                        raise HTTPException(status_code=502, detail=f"Unexpected EODHD response format: {type(data)}")
                        
                elif response.status_code == 401:
                    raise HTTPException(status_code=401, detail="EODHD API key invalid or expired")
                elif response.status_code == 429:
                    if attempt < SETTINGS.max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        time.sleep(wait_time)
                        continue
                    else:
                        raise HTTPException(status_code=429, detail="EODHD rate limit exceeded")
                else:
                    raise HTTPException(status_code=response.status_code, detail=f"EODHD error: {response.text}")
                    
        except httpx.TimeoutException:
            if attempt < SETTINGS.max_retries - 1:
                continue
            raise HTTPException(status_code=408, detail="EODHD API timeout")
        except Exception as e:
            if attempt < SETTINGS.max_retries - 1:
                continue
            raise HTTPException(status_code=500, detail=f"EODHD API error: {str(e)}")
    
    raise HTTPException(status_code=500, detail="Max retries exceeded")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "ingestor_eodhd", "version": "0.1.0"}


@app.post("/v1/ingest/eodhd/prices")
async def ingest_eodhd_prices_batch(
    symbols: List[Dict[str, str]] = Field(..., description="List of {symbol, mic, from_date, to_date}")
) -> List[IngestResponse]:
    """Batch ingest EOD prices from EODHD for multiple symbols.
    
    This endpoint processes multiple symbols in a single request to avoid URL length limits
    and provides better batching for Cloud Scheduler.
    """
    
    results = []
    
    for symbol_data in symbols:
        symbol = symbol_data.get("symbol")
        mic = symbol_data.get("mic", "US")
        from_date = symbol_data.get("from_date")
        to_date = symbol_data.get("to_date")
        
        if not all([symbol, from_date, to_date]):
            continue
            
        try:
            # Validate date format
            try:
                datetime.strptime(from_date, "%Y-%m-%d")
                datetime.strptime(to_date, "%Y-%m-%d")
            except ValueError:
                continue
            
            # Fetch data from EODHD
            raw_data = await _fetch_eodhd_data(symbol, mic, from_date, to_date)
            
            if not raw_data:
                results.append(IngestResponse(
                    symbol=symbol,
                    mic=mic,
                    rows_written=0,
                    corp_actions_written=0,
                    dataset=SETTINGS.bq_dataset_raw,
                    table=SETTINGS.bq_table_eq,
                    from_date=from_date,
                    to_date=to_date,
                ))
                continue
            
            # Parse and validate data
            prices = _parse_eodhd_response(raw_data)
            
            # Write to unified equities table
            eq_rows = _prices_to_bq_rows(symbol, mic, prices)
            eq_written = _write_to_bigquery(eq_rows, SETTINGS.bq_table_eq)
            
            # Extract and write corporate actions
            corp_actions = _extract_corporate_actions(symbol, mic, prices)
            corp_written = _write_to_bigquery(corp_actions, SETTINGS.bq_table_corp_actions)
            
            # Update vendor symbol mapping
            _update_vendor_symbol_map(symbol, mic)
            
            results.append(IngestResponse(
                symbol=symbol,
                mic=mic,
                rows_written=eq_written,
                corp_actions_written=corp_written,
                dataset=SETTINGS.bq_dataset_raw,
                table=SETTINGS.bq_table_eq,
                from_date=from_date,
                to_date=to_date,
            ))
            
        except Exception as e:
            # Log error but continue processing other symbols
            print(f"Error processing {symbol}.{mic}: {e}")
            results.append(IngestResponse(
                symbol=symbol,
                mic=mic,
                rows_written=0,
                corp_actions_written=0,
                dataset=SETTINGS.bq_dataset_raw,
                table=SETTINGS.bq_table_eq,
                from_date=from_date,
                to_date=to_date,
            ))
    
    return results


@app.get("/v1/ingest/eodhd/prices")
async def ingest_eodhd_prices_single(
    symbol: str = Query(..., description="Stock symbol, e.g., AAPL"),
    mic: str = Query("US", description="Market Identifier Code, e.g., US, LSE, ASX"),
    from_date: str = Query(..., description="Start date YYYY-MM-DD"),
    to_date: str = Query(..., description="End date YYYY-MM-DD"),
) -> IngestResponse:
    """Single symbol ingest endpoint for backward compatibility."""
    
    # Validate date format
    try:
        datetime.strptime(from_date, "%Y-%m-%d")
        datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Fetch data from EODHD
    raw_data = await _fetch_eodhd_data(symbol, mic, from_date, to_date)
    
    if not raw_data:
        return IngestResponse(
            symbol=symbol,
            mic=mic,
            rows_written=0,
            corp_actions_written=0,
            dataset=SETTINGS.bq_dataset_raw,
            table=SETTINGS.bq_table_eq,
            from_date=from_date,
            to_date=to_date,
        )
    
    # Parse and validate data
    prices = _parse_eodhd_response(raw_data)
    
    # Write to unified equities table
    eq_rows = _prices_to_bq_rows(symbol, mic, prices)
    eq_written = _write_to_bigquery(eq_rows, SETTINGS.bq_table_eq)
    
    # Extract and write corporate actions
    corp_actions = _extract_corporate_actions(symbol, mic, prices)
    corp_written = _write_to_bigquery(corp_actions, SETTINGS.bq_table_corp_actions)
    
    # Update vendor symbol mapping
    _update_vendor_symbol_map(symbol, mic)
    
    return IngestResponse(
        symbol=symbol,
        mic=mic,
        rows_written=eq_written,
        corp_actions_written=corp_written,
        dataset=SETTINGS.bq_dataset_raw,
        table=SETTINGS.bq_table_eq,
        from_date=from_date,
        to_date=to_date,
    )


@app.get("/v1/symbols/search")
async def search_symbols(
    query: str = Query(..., description="Symbol or company name to search"),
    mic: Optional[str] = Query(None, description="Filter by Market Identifier Code"),
) -> Dict[str, Any]:
    """Search for symbols available on EODHD."""
    api_key = _get_eodhd_api_key()
    url = "https://eodhd.com/api/exchange-symbol-list"
    
    params = {"api_token": api_key}
    if mic:
        params["fmt"] = "json"
        params["exchange"] = mic
    
    try:
        async with httpx.AsyncClient(timeout=SETTINGS.http_timeout_seconds) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                # Filter results by query
                if isinstance(data, list):
                    filtered = [item for item in data if query.upper() in item.get("Code", "").upper() or 
                               query.upper() in item.get("Name", "").upper()]
                    return {"results": filtered[:50], "total": len(filtered)}
                else:
                    return {"results": [], "total": 0, "error": "Unexpected response format"}
            else:
                raise HTTPException(status_code=response.status_code, detail=f"EODHD search error: {response.text}")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


# Entrypoint for local run: uvicorn app.main:app --reload --port 8080
