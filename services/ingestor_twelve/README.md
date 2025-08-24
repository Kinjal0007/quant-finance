# Twelve Data Ingestor Service (Cloud Run)

Ingest intraday prices, FX rates, and crypto data from Twelve Data and write to unified BigQuery tables. Supports real-time and historical data across multiple asset classes with proper UTC timestamps.

## Features

- **Unified Schema**: Single `eq_ohlcv` table for all equities data
- **Intraday Data**: 1-minute to monthly intervals for equities
- **FX Rates**: Major and minor currency pairs
- **Crypto**: Bitcoin, Ethereum, and 100+ cryptocurrencies
- **Batch Processing**: Process multiple symbols in single request
- **UTC Timestamps**: Proper timezone handling for global markets
- **Symbol Mapping**: Vendor symbol to canonical symbol mapping

## Endpoints

- `GET /health` – Health check
- `POST /v1/ingest/twelve/intraday` – Batch ingest intraday prices (preferred)
- `GET /v1/ingest/twelve/intraday` – Single symbol intraday (backward compatibility)
- `POST /v1/ingest/twelve/fx` – Batch ingest FX rates (preferred)
- `GET /v1/ingest/twelve/fx` – Single FX pair (backward compatibility)
- `POST /v1/ingest/twelve/crypto` – Batch ingest crypto prices (preferred)
- `GET /v1/ingest/twelve/crypto` – Single crypto symbol (backward compatibility)

## Environment Variables

- `GCP_PROJECT` – GCP project id
- `GCP_REGION` – Region (default: europe-west3)
- `BQ_DATASET_RAW` – Raw dataset name (default: market_raw)
- `BQ_TABLE_EQ` – Unified equities table (default: eq_ohlcv)
- `BQ_TABLE_FX` – FX rates table (default: fx_ohlcv)
- `BQ_TABLE_CRYPTO` – Crypto prices table (default: crypto_ohlcv)
- `BQ_TABLE_VENDOR_MAP` – Vendor symbol mapping (default: vendor_symbol_map)
- `TWELVE_API_KEY` – Twelve Data API key (or set `TWELVE_SECRET_NAME`)
- `TWELVE_SECRET_NAME` – Secret Manager secret name containing API key
- `TWELVEDATA_RPS_LIMIT` – Rate limit in requests per second (default: 8)

## Local Run

```bash
# From repo root
cd services/ingestor_twelve

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
export BQ_TABLE_FX=fx_ohlcv
export BQ_TABLE_CRYPTO=crypto_ohlcv
export BQ_TABLE_VENDOR_MAP=vendor_symbol_map
export TWELVE_API_KEY=your_twelve_api_key_here
export TWELVEDATA_RPS_LIMIT=8

# Run service locally
uvicorn app.main:app --reload --port 8080
```

## Test Endpoints

```bash
# Health check
curl http://localhost:8080/health

# Single symbol intraday (backward compatibility)
curl "http://localhost:8080/v1/ingest/twelve/intraday?symbol=AAPL&interval=1min&start_date=2024-01-15&end_date=2024-01-15"

# Batch intraday ingest (preferred for Cloud Scheduler)
curl -X POST "http://localhost:8080/v1/ingest/twelve/intraday" \
  -H "Content-Type: application/json" \
  -d '[
    {"symbol": "AAPL", "interval": "1min", "start_date": "2024-01-15", "end_date": "2024-01-15"},
    {"symbol": "MSFT", "interval": "5min", "start_date": "2024-01-15", "end_date": "2024-01-15"},
    {"symbol": "GOOGL", "interval": "15min", "start_date": "2024-01-15", "end_date": "2024-01-15"}
  ]'

# Single FX pair (backward compatibility)
curl "http://localhost:8080/v1/ingest/twelve/fx?symbol=EUR/USD&interval=1h&start_date=2024-01-15&end_date=2024-01-15"

# Batch FX ingest
curl -X POST "http://localhost:8080/v1/ingest/twelve/fx" \
  -H "Content-Type: application/json" \
  -d '[
    {"symbol": "EUR/USD", "interval": "1h", "start_date": "2024-01-15", "end_date": "2024-01-15"},
    {"symbol": "GBP/USD", "interval": "1h", "start_date": "2024-01-15", "end_date": "2024-01-15"}
  ]'

# Single crypto (backward compatibility)
curl "http://localhost:8080/v1/ingest/twelve/crypto?symbol=BTC/USD&interval=1h&start_date=2024-01-15&end_date=2024-01-15"

# Batch crypto ingest
curl -X POST "http://localhost:8080/v1/ingest/twelve/crypto" \
  -H "Content-Type: application/json" \
  -d '[
    {"symbol": "BTC/USD", "interval": "1h", "start_date": "2024-01-15", "end_date": "2024-01-15"},
    {"symbol": "ETH/USD", "interval": "1h", "start_date": "2024-01-15", "end_date": "2024-01-15"}
  ]'
```

## Supported Intervals

- **Intraday**: 1min, 5min, 15min, 30min, 45min
- **Hourly**: 1h, 2h, 4h
- **Daily**: 1day, 1week, 1month

## BigQuery Schema

The service writes to three tables:

### **`eq_ohlcv`** - Unified Equities Table

- `symbol`: Stock ticker (AAPL, MSFT, GOOGL)
- `mic`: Market Identifier Code (US for Twelve Data)
- `vendor`: Data source (twelve_data)
- `interval`: Time interval (1min, 5min, 15min, etc.)
- `ts_utc`: UTC timestamp
- `open`, `high`, `low`, `close`, `volume`: OHLCV data
- Partitioned by date, clustered by symbol + interval + vendor

### **`fx_ohlcv`** - FX Rates Table

- `symbol`: Currency pair (EUR/USD, GBP/USD)
- `vendor`: Data source (twelve_data)
- `interval`: Time interval
- `ts_utc`: UTC timestamp
- `open`, `high`, `low`, `close`: OHLC data
- Partitioned by date, clustered by symbol + interval + vendor

### **`crypto_ohlcv`** - Crypto Prices Table

- `symbol`: Crypto pair (BTC/USD, ETH/USD)
- `vendor`: Data source (twelve_data)
- `interval`: Time interval
- `ts_utc`: UTC timestamp
- `open`, `high`, `low`, `close`, `volume`: OHLCV data
- Partitioned by date, clustered by symbol + interval + vendor

### **`vendor_symbol_map`** - Symbol Mapping

- `vendor`: Data provider (twelve_data)
- `vendor_symbol`: Symbol as known by vendor
- `symbol`: Canonical symbol (TICKER.MIC for equities, original for FX/crypto)
- `mic`: Market Identifier Code (US for equities, N/A for FX/crypto)
- `asset_type`: equity, fx, crypto

## Build and Deploy (Cloud Run)

```bash
SERVICE=ingestor-twelve
GCP_PROJECT=quant-finance-469720
GCP_REGION=europe-west3

# Build and push image
cd services/ingestor_twelve
gcloud builds submit --tag gcr.io/$GCP_PROJECT/$SERVICE ./

# Deploy to Cloud Run (PRIVATE - no public access)
gcloud run deploy $SERVICE \
  --image gcr.io/$GCP_PROJECT/$SERVICE \
  --project $GCP_PROJECT \
  --region $GCP_REGION \
  --no-allow-unauthenticated \
  --set-env-vars GCP_PROJECT=$GCP_PROJECT,BQ_DATASET_RAW=market_raw,BQ_TABLE_EQ=eq_ohlcv,BQ_TABLE_FX=fx_ohlcv,BQ_TABLE_CRYPTO=crypto_ohlcv,BQ_TABLE_VENDOR_MAP=vendor_symbol_map \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
```

## Cloud Scheduler with OIDC Auth

Create scheduled jobs using OIDC authentication (recommended):

```bash
GCP_PROJECT=quant-finance-469720
GCP_REGION=europe-west3
SERVICE_URL=$(gcloud run services describe ingestor-twelve --project $GCP_PROJECT --region $GCP_REGION --format 'value(status.url)')

# Create service account for scheduler
gcloud iam service-accounts create twelve-scheduler \
  --display-name="Twelve Data Scheduler Service Account" \
  --project $GCP_PROJECT

# Grant Cloud Run invoker role
gcloud run services add-iam-policy-binding ingestor-twelve \
  --member="serviceAccount:twelve-scheduler@$GCP_PROJECT.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --project $GCP_PROJECT \
  --region $GCP_REGION

# Intraday data every 15 minutes during market hours (9:30-16:00 ET)
gcloud scheduler jobs create http ingest-intraday-15min \
  --project $GCP_PROJECT \
  --schedule "*/15 14-21 * * 1-5" \
  --uri "$SERVICE_URL/v1/ingest/twelve/intraday" \
  --http-method POST \
  --oidc-service-account-email="twelve-scheduler@$GCP_PROJECT.iam.gserviceaccount.com" \
  --oidc-token-audience="$SERVICE_URL" \
  --headers="Content-Type=application/json" \
  --message-body='[
    {"symbol": "AAPL", "interval": "15min", "start_date": "2024-01-15", "end_date": "2024-01-15"},
    {"symbol": "MSFT", "interval": "15min", "start_date": "2024-01-15", "end_date": "2024-01-15"},
    {"symbol": "GOOGL", "interval": "15min", "start_date": "2024-01-15", "end_date": "2024-01-15"}
  ]' \
  --time-zone "America/New_York"

# FX rates every hour
gcloud scheduler jobs create http ingest-fx-hourly \
  --project $GCP_PROJECT \
  --schedule "0 * * * *" \
  --uri "$SERVICE_URL/v1/ingest/twelve/fx" \
  --http-method POST \
  --oidc-service-account-email="twelve-scheduler@$GCP_PROJECT.iam.gserviceaccount.com" \
  --oidc-token-audience="$SERVICE_URL" \
  --headers="Content-Type=application/json" \
  --message-body='[
    {"symbol": "EUR/USD", "interval": "1h", "start_date": "2024-01-15", "end_date": "2024-01-15"},
    {"symbol": "GBP/USD", "interval": "1h", "start_date": "2024-01-15", "end_date": "2024-01-15"},
    {"symbol": "USD/JPY", "interval": "1h", "start_date": "2024-01-15", "end_date": "2024-01-15"}
  ]' \
  --time-zone "Etc/UTC"

# Crypto prices every 5 minutes
gcloud scheduler jobs create http ingest-crypto-5min \
  --project $GCP_PROJECT \
  --schedule "*/5 * * * *" \
  --uri "$SERVICE_URL/v1/ingest/twelve/crypto" \
  --http-method POST \
  --oidc-service-account-email="twelve-scheduler@$GCP_PROJECT.iam.gserviceaccount.com" \
  --oidc-token-audience="$SERVICE_URL" \
  --headers="Content-Type=application/json" \
  --message-body='[
    {"symbol": "BTC/USD", "interval": "5min", "start_date": "2024-01-15", "end_date": "2024-01-15"},
    {"symbol": "ETH/USD", "interval": "5min", "start_date": "2024-01-15", "end_date": "2024-01-15"},
    {"symbol": "ADA/USD", "interval": "5min", "start_date": "2024-01-15", "end_date": "2024-01-15"}
  ]' \
  --time-zone "Etc/UTC"
```

## Data Sources

- **Twelve Data**: Professional market data provider
- **Coverage**: 50+ exchanges, 100+ cryptocurrencies, major FX pairs
- **Quality**: Real-time and historical data with millisecond precision

## Rate Limits

- **Free Tier**: 800 requests/day
- **Starter**: 8,000 requests/day
- **Professional**: 100,000+ requests/day
- **Service Rate Limit**: 8 requests per second (configurable via `TWELVEDATA_RPS_LIMIT`)

## Batch Processing

- **Recommended**: Use POST endpoints with JSON body for multiple symbols
- **Batch Size**: 50-100 symbols per request for optimal performance
- **Cloud Scheduler**: Avoid URL length limits by using POST with JSON payload

## Acceptance Checklist

- [x] DDL applied successfully; unified tables exist
- [x] Service deploys to Cloud Run as private service
- [x] `/health` returns ok (authenticated access only)
- [x] Single intraday ingest writes to unified `eq_ohlcv` table
- [x] Batch intraday ingest processes multiple symbols
- [x] Single FX ingest writes to `fx_ohlcv` table
- [x] Batch FX ingest processes multiple pairs
- [x] Single crypto ingest writes to `crypto_ohlcv` table
- [x] Batch crypto ingest processes multiple symbols
- [x] Vendor symbol mapping updated for all asset types
- [x] UTC timestamps properly handled
- [x] Secrets handled via env or Secret Manager
- [x] GitHub Actions CI passes
- [x] Cloud Scheduler uses OIDC auth
