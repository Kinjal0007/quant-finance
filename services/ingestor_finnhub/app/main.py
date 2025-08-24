from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

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
    gcp_region: str = Field(default_factory=lambda: os.getenv("GCP_REGION", "us-central1"))
    bq_dataset_raw: str = Field(default_factory=lambda: os.getenv("BQ_DATASET_RAW", "market_raw"))
    bq_table_raw: str = Field(default_factory=lambda: os.getenv("BQ_TABLE_RAW", "eq_ohlcv"))
    finnhub_secret_name: Optional[str] = Field(default_factory=lambda: os.getenv("FINNHUB_SECRET_NAME"))
    finnhub_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("FINNHUB_API_KEY"))
    http_timeout_seconds: int = Field(default=30)


SETTINGS = Settings()
app = FastAPI(title="Finnhub Ingestor Service", version="0.1.0")


def _get_finnhub_api_key() -> str:
    if SETTINGS.finnhub_api_key:
        return SETTINGS.finnhub_api_key
    if SETTINGS.finnhub_secret_name and secretmanager is not None:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{SETTINGS.gcp_project}/secrets/{SETTINGS.finnhub_secret_name}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("utf-8")
    raise RuntimeError("Finnhub API key not configured. Set FINNHUB_API_KEY or FINNHUB_SECRET_NAME.")


def _bq_client() -> "bigquery.Client":
    if bigquery is None:
        raise RuntimeError("google-cloud-bigquery is not installed. Install it to run ingestor.")
    return bigquery.Client(project=SETTINGS.gcp_project or None)


class IngestResponse(BaseModel):
    symbol: str
    resolution: str
    rows_written: int
    dataset: str
    table: str
    from_ts: int
    to_ts: int


def _to_unix(dt: datetime) -> int:
    return int(dt.replace(tzinfo=timezone.utc).timestamp())


async def _fetch_candles(symbol: str, resolution: str, from_ts: int, to_ts: int) -> Dict[str, Any]:
    api_key = _get_finnhub_api_key()
    url = "https://finnhub.io/api/v1/stock/candle"
    params = {"symbol": symbol, "resolution": resolution, "from": from_ts, "to": to_ts, "token": api_key}
    async with httpx.AsyncClient(timeout=SETTINGS.http_timeout_seconds) as client:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Finnhub error: {resp.text}")
        data = resp.json()
    if data.get("s") != "ok":
        raise HTTPException(status_code=502, detail=f"Finnhub returned status: {data.get('s')}")
    return data


def _candles_to_rows(symbol: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    timestamps = data.get("t", [])
    opens = data.get("o", [])
    highs = data.get("h", [])
    lows = data.get("l", [])
    closes = data.get("c", [])
    volumes = data.get("v", [])
    ingest_time_iso = datetime.now(timezone.utc).isoformat()

    rows: List[Dict[str, Any]] = []
    for i in range(len(timestamps)):
        ts_seconds = timestamps[i]
        row = {
            "symbol": symbol,
            "ts": datetime.fromtimestamp(ts_seconds, tz=timezone.utc).isoformat(),
            "open": float(opens[i]) if i < len(opens) else None,
            "high": float(highs[i]) if i < len(highs) else None,
            "low": float(lows[i]) if i < len(lows) else None,
            "close": float(closes[i]) if i < len(closes) else None,
            "volume": float(volumes[i]) if i < len(volumes) else None,
            "source": "finnhub",
            "ingest_time": ingest_time_iso,
        }
        rows.append(row)
    return rows


def _write_to_bigquery(rows: List[Dict[str, Any]]) -> int:
    if not rows:
        return 0
    client = _bq_client()
    table_id = f"{client.project}.{SETTINGS.bq_dataset_raw}.{SETTINGS.bq_table_raw}"
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        # Consolidate and surface the first error for brevity
        raise HTTPException(status_code=500, detail=f"BigQuery insert errors: {errors}")
    return len(rows)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "ingestor_finnhub"}


@app.get("/v1/ingest/finnhub/candles", response_model=IngestResponse)
async def ingest_finnhub_candles(
    symbol: str = Query(..., description="Ticker symbol, e.g., AAPL"),
    resolution: str = Query("D", description="Finnhub resolution: 1,5,15,30,60,D,W,M"),
    days: int = Query(7, ge=1, le=365, description="Lookback in days if from/to not provided"),
    from_ts: Optional[int] = Query(None, description="Unix seconds"),
    to_ts: Optional[int] = Query(None, description="Unix seconds"),
) -> IngestResponse:
    """Ingest candles for the given symbol and write to BigQuery raw dataset.

    This endpoint is idempotent as it writes by timestamp; duplicates will be stored unless you add BQ
    deduplication on read or a MERGE step in curated tables.
    """

    now = datetime.now(timezone.utc)
    if to_ts is None:
        to_ts = _to_unix(now)
    if from_ts is None:
        from_ts = _to_unix(now - timedelta(days=days))

    data = await _fetch_candles(symbol=symbol, resolution=resolution, from_ts=from_ts, to_ts=to_ts)
    rows = _candles_to_rows(symbol, data)
    written = _write_to_bigquery(rows)

    return IngestResponse(
        symbol=symbol,
        resolution=resolution,
        rows_written=written,
        dataset=SETTINGS.bq_dataset_raw,
        table=SETTINGS.bq_table_raw,
        from_ts=from_ts,
        to_ts=to_ts,
    )


# Entrypoint for local run: uvicorn app.main:app --reload --port 8080

