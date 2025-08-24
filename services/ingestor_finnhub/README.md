# Finnhub Ingestor Service (Cloud Run)

Ingest OHLCV candles from Finnhub and write to BigQuery raw dataset.

## Endpoints
- `GET /health` – Health check
- `GET /v1/ingest/finnhub/candles?symbol=AAPL&resolution=D&days=7` – Ingest candles into BigQuery

## Environment Variables
- `GCP_PROJECT` – GCP project id
- `GCP_REGION` – Region (e.g., us-central1)
- `BQ_DATASET_RAW` – Raw dataset name (default: market_raw)
- `BQ_TABLE_RAW` – Raw table name (default: eq_ohlcv)
- `FINNHUB_API_KEY` – Finnhub API key (or set `FINNHUB_SECRET_NAME`)
- `FINNHUB_SECRET_NAME` – Secret Manager secret name containing API key

## Local Run
```bash
# From repo root
cd services/ingestor_finnhub
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GCP_PROJECT=your-project
export BQ_DATASET_RAW=market_raw
export BQ_TABLE_RAW=eq_ohlcv
export FINNHUB_API_KEY=your_key
uvicorn app.main:app --reload --port 8080
```

## BigQuery DDL
Apply the schema:
```bash
# Replace placeholders
GCP_PROJECT=your-project \
BQ_DATASET_RAW=market_raw \
BQ_DATASET_CURATED=market_curated \
BQ_TABLE_RAW=eq_ohlcv \
  envsubst < ../../infra/bigquery/ddl.sql | bq query --location=US --nouse_legacy_sql
```

## Build and Deploy (Cloud Run)
```bash
SERVICE=ingestor-finnhub
GCP_PROJECT=your-project
GCP_REGION=us-central1

gcloud builds submit --tag gcr.io/$GCP_PROJECT/$SERVICE ./

gcloud run deploy $SERVICE \
  --image gcr.io/$GCP_PROJECT/$SERVICE \
  --project $GCP_PROJECT \
  --region $GCP_REGION \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT=$GCP_PROJECT,BQ_DATASET_RAW=market_raw,BQ_TABLE_RAW=eq_ohlcv
```

## Cloud Scheduler (Optional)
Create a scheduled job to ingest daily EOD candles:
```bash
GCP_PROJECT=your-project
GCP_REGION=us-central1
SERVICE_URL=$(gcloud run services describe ingestor-finnhub --project $GCP_PROJECT --region $GCP_REGION --format 'value(status.url)')

# Example: AAPL daily at 22:30 UTC
gcloud scheduler jobs create http ingest-aapl-daily \
  --project $GCP_PROJECT \
  --schedule "30 22 * * *" \
  --uri "$SERVICE_URL/v1/ingest/finnhub/candles?symbol=AAPL&resolution=D&days=7" \
  --http-method GET \
  --time-zone "Etc/UTC"
```

## Acceptance Checklist
- [ ] DDL applied successfully; datasets and table exist
- [ ] Service deploys to Cloud Run and `/health` returns ok
- [ ] Ingest call writes rows to BigQuery with expected schema
- [ ] Secrets handled via env or Secret Manager
- [ ] GitHub Actions CI passes
