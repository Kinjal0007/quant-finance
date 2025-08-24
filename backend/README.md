# Quant Finance Platform - Backend

FastAPI-based backend service for quantitative finance models with async job processing.

## Features

- **Financial Models**: Monte Carlo, Markowitz, Black-Scholes, Backtesting
- **Async Processing**: Pub/Sub + Cloud Run worker pattern
- **Data Sources**: EOD Historical Data + Twelve Data integration
- **Storage**: BigQuery for prices, Cloud Storage for artifacts
- **Fixture Mode**: Demo data for development without API keys

## Quick Start

### Prerequisites

- Python 3.9+
- GCP Project with required APIs enabled
- Service account with BigQuery + Cloud Storage access

### Local Development

1. **Clone and setup**:

```bash
git clone <repo>
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment variables**:

```bash
# Copy and configure
cp .env.example .env

# Required for GCP services
export GCP_PROJECT="your-project-id"
export GCP_REGION="europe-west3"

# For fixture mode (no API keys needed)
export USE_FIXTURE=true
export USE_SQLITE=true
```

3. **Database setup**:

```bash
# SQLite (local development)
export USE_SQLITE=true
alembic upgrade head

# Or PostgreSQL (production)
export USE_SQLITE=false
# Configure DATABASE_URL in .env
alembic upgrade head
```

4. **Run the service**:

```bash
# Development mode
uvicorn app.main:app --reload --port 8080

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Fixture Mode

When `USE_FIXTURE=true`, the backend uses demo data instead of vendor APIs:

- **Demo Dataset**: 3 symbols (AAPL, MSFT, GOOGL) × ~60 days
- **Financial Models**: All models run with realistic mock data
- **No API Keys**: Perfect for development and demos
- **Realistic Results**: Generated metrics match expected ranges

### Fixture Data Structure

```
backend/worker/fixtures/
└── prices_demo.csv          # OHLCV data for demo symbols
```

### Using Fixtures

```bash
# Enable fixture mode
export USE_FIXTURE=true

# Start backend
uvicorn app.main:app --reload --port 8080

# Create jobs - they'll use demo data automatically
curl -X POST http://localhost:8080/api/v1/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "montecarlo",
    "symbols": ["AAPL", "MSFT"],
    "start": "2024-01-01",
    "end": "2024-12-31",
    "interval": "1d",
    "vendor": "eodhd",
    "adjusted": true,
    "params": {
      "simulations": 1000,
      "time_steps": 252
    }
  }'
```

## API Endpoints

- `GET /health` - Health check
- `GET /docs` - Interactive API documentation
- `POST /api/v1/jobs/` - Create job
- `GET /api/v1/jobs/` - List jobs
- `GET /api/v1/jobs/{id}` - Get job details
- `DELETE /api/v1/jobs/{id}` - Cancel job

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## Deployment

### Cloud Run

```bash
# Build and deploy
gcloud run deploy quant-finance-api \
  --source . \
  --platform managed \
  --region europe-west3 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT=$GCP_PROJECT
```

### Docker

```bash
# Build image
docker build -t quant-finance-api .

# Run locally
docker run -p 8080:8080 \
  -e GCP_PROJECT=$GCP_PROJECT \
  -e USE_FIXTURE=false \
  quant-finance-api
```

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   FastAPI       │────│   Pub/Sub    │────│   Cloud Run     │
│   (API)         │    │   (Queue)    │    │   (Worker)      │
└─────────────────┘    └──────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌────────▼──────┐    ┌──────────▼──────┐    ┌──────────────▼──┐
│   SQLite/     │    │   BigQuery      │    │   Cloud         │
│   PostgreSQL  │    │   (Prices)      │    │   Storage       │
└───────────────┘    └─────────────────┘    └─────────────────┘
```

## Environment Variables

| Variable             | Description                  | Default                |
| -------------------- | ---------------------------- | ---------------------- |
| `GCP_PROJECT`        | GCP Project ID               | Required               |
| `GCP_REGION`         | GCP Region                   | `europe-west3`         |
| `USE_FIXTURE`        | Use demo data                | `false`                |
| `USE_SQLITE`         | Use SQLite for local dev     | `false`                |
| `DATABASE_URL`       | PostgreSQL connection string | Required if not SQLite |
| `BQ_DATASET_RAW`     | BigQuery raw dataset         | `market_raw`           |
| `BQ_DATASET_CURATED` | BigQuery curated dataset     | `market_curated`       |
