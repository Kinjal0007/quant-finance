# EODHD Ingestor Service (Cloud Run)

Ingest end-of-day historical prices from EODHD (EOD Historical Data) and write to unified BigQuery tables. Supports global equities with splits, dividends, and corporate actions tracking.

## Features

- **Global Coverage**: US, LSE, ASX, and 50+ exchanges
- **Unified Schema**: Single `eq_ohlcv` table for all equities data
- **Corporate Actions**: Automatic tracking of splits, dividends, and adjustments
- **Symbol Mapping**: Vendor symbol to canonical symbol mapping
- **Batch Processing**: Process multiple symbols in single request
- **UTC Timestamps**: Proper timezone handling for global markets

## Endpoints

- `GET /health` – Health check
- `POST /v1/ingest/eodhd/prices` – Batch ingest EOD prices (preferred)
- `GET /v1/ingest/eodhd/prices` – Single symbol ingest (backward compatibility)
- `GET /v1/symbols/search` – Search available symbols

## Environment Variables

- `GCP_PROJECT` – GCP project id
- `GCP_REGION` – Region (default: europe-west3)
- `BQ_DATASET_RAW` – Raw dataset name (default: market_raw)
- `BQ_TABLE_EQ` – Unified equities table (default: eq_ohlcv)
- `BQ_TABLE_CORP_ACTIONS` – Corporate actions table (default: corporate_actions)
- `BQ_TABLE_VENDOR_MAP` – Vendor symbol mapping (default: vendor_symbol_map)
- `EODHD_API_KEY` – EODHD API key (or set `EODHD_SECRET_NAME`)
- `EODHD_SECRET_NAME` – Secret Manager secret name containing API key
- `EODHD_RPS_LIMIT` – Rate limit in requests per second (default: 10)

## Local Run

```bash
# From repo root
cd services/ingestor_eodhd

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GCP_PROJECT=quant-finance-469720
export GCP_REGION=europe-west3
export BQ_DATASET_RAW=market_raw
export BQ_TABLE_EQ=eq_ohlcv
export BQ_TABLE_CORP_ACTIONS=corporate_actions
export BQ_TABLE_VENDOR_MAP=vendor_symbol_map
export EODHD_API_KEY=your_eodhd_api_key_here
export EODHD_RPS_LIMIT=10

# Run service locally
uvicorn app.main:app --reload --port 8080
```

## Test Endpoints

```bash
# Health check
curl http://localhost:8080/health

# Search for AAPL symbol
curl "http://localhost:8080/v1/symbols/search?query=AAPL&mic=US"

# Single symbol ingest (backward compatibility)
curl "http://localhost:8080/v1/ingest/eodhd/prices?symbol=AAPL&mic=US&from_date=2024-01-01&to_date=2024-01-31"

# Batch ingest (preferred for Cloud Scheduler)
curl -X POST "http://localhost:8080/v1/ingest/eodhd/prices" \
  -H "Content-Type: application/json" \
  -d '[
    {"symbol": "AAPL", "mic": "US", "from_date": "2024-01-01", "to_date": "2024-01-31"},
    {"symbol": "MSFT", "mic": "US", "from_date": "2024-01-01", "to_date": "2024-01-31"},
    {"symbol": "BMW", "mic": "XETR", "from_date": "2024-01-01", "to_date": "2024-01-31"}
  ]'
```

## BigQuery Schema

The service writes to three tables:

### **`eq_ohlcv`** - Unified Equities Table

- `symbol`: Stock ticker (AAPL, MSFT, BMW)
- `mic`: Market Identifier Code (US, XETR, LSE)
- `vendor`: Data source (eodhd)
- `interval`: Time interval (1d for EOD data)
- `ts_utc`: UTC timestamp (market close time)
- `open`, `high`, `low`, `close`, `volume`: OHLCV data
- Partitioned by date, clustered by symbol + interval + vendor

### **`corporate_actions`** - Corporate Actions Table

- `symbol`, `mic`: Stock identifier
- `ex_date`: Ex-dividend date
- `split_ratio`: Stock split ratio
- `cash_dividend`: Dividend per share
- `adj_factor`: Cumulative adjustment factor
- Partitioned by ex_date, clustered by symbol + mic

### **`vendor_symbol_map`** - Symbol Mapping

- `vendor`: Data provider (eodhd)
- `vendor_symbol`: Symbol as known by vendor
- `symbol`: Canonical symbol (TICKER.MIC)
- `mic`: Market Identifier Code
- `asset_type`: equity, fx, crypto

## Build and Deploy (Cloud Run)

```bash
SERVICE=ingestor-eodhd
GCP_PROJECT=quant-finance-469720
GCP_REGION=europe-west3

# Build and push image
cd services/ingestor_eodhd
gcloud builds submit --tag gcr.io/$GCP_PROJECT/$SERVICE ./

# Deploy to Cloud Run (PRIVATE - no public access)
gcloud run deploy $SERVICE \
  --image gcr.io/$GCP_PROJECT/$SERVICE \
  --project $GCP_PROJECT \
  --region $GCP_REGION \
  --no-allow-unauthenticated \
  --set-env-vars GCP_PROJECT=$GCP_PROJECT,BQ_DATASET_RAW=market_raw,BQ_TABLE_EQ=eq_ohlcv,BQ_TABLE_CORP_ACTIONS=corporate_actions,BQ_TABLE_VENDOR_MAP=vendor_symbol_map \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
```

## Cloud Scheduler with OIDC Auth

Create scheduled jobs using OIDC authentication (recommended):

```bash
GCP_PROJECT=quant-finance-469720
GCP_REGION=europe-west3
SERVICE_URL=$(gcloud run services describe ingestor-eodhd --project $GCP_PROJECT --region $GCP_REGION --format 'value(status.url)')

# Create service account for scheduler
gcloud iam service-accounts create eodhd-scheduler \
  --display-name="EODHD Scheduler Service Account" \
  --project $GCP_PROJECT

# Grant Cloud Run invoker role
gcloud run services add-iam-policy-binding ingestor-eodhd \
  --member="serviceAccount:eodhd-scheduler@$GCP_PROJECT.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --project $GCP_PROJECT \
  --region $GCP_REGION

# Daily EOD ingestion for major indices (22:30 UTC)
gcloud scheduler jobs create http ingest-sp500-daily \
  --project $GCP_PROJECT \
  --schedule "30 22 * * *" \
  --uri "$SERVICE_URL/v1/ingest/eodhd/prices" \
  --http-method POST \
  --oidc-service-account-email="eodhd-scheduler@$GCP_PROJECT.iam.gserviceaccount.com" \
  --oidc-token-audience="$SERVICE_URL" \
  --headers="Content-Type=application/json" \
  --message-body='[
    {"symbol": "SPY", "mic": "US", "from_date": "2024-01-01", "to_date": "2024-01-31"},
    {"symbol": "QQQ", "mic": "US", "from_date": "2024-01-01", "to_date": "2024-01-31"},
    {"symbol": "IWM", "mic": "US", "from_date": "2024-01-01", "to_date": "2024-01-31"}
  ]' \
  --time-zone "Etc/UTC"

# Weekly full market update (Sunday 23:00 UTC)
gcloud scheduler jobs create http ingest-full-market-weekly \
  --project $GCP_PROJECT \
  --schedule "0 23 * * 0" \
  --uri "$SERVICE_URL/v1/ingest/eodhd/prices" \
  --http-method POST \
  --oidc-service-account-email="eodhd-scheduler@$GCP_PROJECT.iam.gserviceaccount.com" \
  --oidc-token-audience="$SERVICE_URL" \
  --headers="Content-Type=application/json" \
  --message-body='[
    {"symbol": "AAPL", "mic": "US", "from_date": "2020-01-01", "to_date": "2024-12-31"},
    {"symbol": "MSFT", "mic": "US", "from_date": "2020-01-01", "to_date": "2024-12-31"},
    {"symbol": "GOOGL", "mic": "US", "from_date": "2020-01-01", "to_date": "2024-12-31"}
  ]' \
  --time-zone "Etc/UTC"
```

## Data Sources

- **EODHD**: End-of-day historical data with splits/dividends
- **Coverage**: 50+ exchanges, 100,000+ symbols
- **Quality**: Professional-grade data used by institutional clients

## Rate Limiting

- **Default**: 10 requests per second (configurable via `EODHD_RPS_LIMIT`)
- **Batch Processing**: Process 50-100 symbols per request
- **Cloud Scheduler**: Use POST with JSON body to avoid URL length limits

## Acceptance Checklist

- [x] DDL applied successfully; unified tables exist
- [x] Service deploys to Cloud Run as private service
- [x] `/health` returns ok (authenticated access only)
- [x] Symbol search returns results for known symbols
- [x] Single ingest writes to unified `eq_ohlcv` table
- [x] Batch ingest processes multiple symbols
- [x] Corporate actions extracted and stored
- [x] Vendor symbol mapping updated
- [x] UTC timestamps properly handled
- [x] Secrets handled via env or Secret Manager
- [x] GitHub Actions CI passes
- [x] Cloud Scheduler uses OIDC auth
