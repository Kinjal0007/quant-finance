# Quant Finance Platform

A production-ready quantitative finance platform built on GCP with Monte Carlo simulations, portfolio optimization, and option pricing.

## Architecture

- **Backend**: FastAPI with async job processing
- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **Data**: BigQuery for prices, GCS for artifacts, Cloud SQL for metadata
- **Processing**: Cloud Run services with Pub/Sub for job queuing
- **Data Sources**: EOD Historical Data (EODHD) and Twelve Data

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- GCP Project with billing enabled
- Docker

### Local Development

#### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
cp env.example .env
# Edit .env with your values

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --port 8080 --host 127.0.0.1
```

#### Frontend Setup

```bash
cd frontend
npm install

# Set environment variables
cp env.example .env.local
# Edit .env.local with your values

# Start development server
npm run dev
```

### Environment Variables

#### Backend (.env)

- `DATABASE_URL`: PostgreSQL connection string
- `USE_SQLITE`: Use SQLite for local development
- `GCP_PROJECT`: GCP Project ID
- `EODHD_API_KEY`: EOD Historical Data API key
- `TWELVE_DATA_API_KEY`: Twelve Data API key
- `USE_FIXTURE`: Use mock data for development

#### Frontend (.env.local)

- `NEXT_PUBLIC_API_BASE`: Backend API URL

## Deployment

### GCP Setup

1. Enable required APIs:

   - Cloud Run
   - BigQuery
   - Cloud SQL
   - Cloud Storage
   - Pub/Sub
   - Secret Manager

2. Create service account with required permissions

3. Set GitHub Secrets:
   - `GCP_SA_KEY`: Service account JSON key
   - `GCP_PROJECT`: Project ID
   - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Database credentials
   - `QFP_ARTIFACTS_BUCKET`: GCS bucket for artifacts
   - `FRONTEND_ORIGIN`: Frontend domain for CORS
   - `FRONTEND_API_BASE`: Backend API URL

### CI/CD

GitHub Actions automatically deploy on push to main:

- **Backend**: FastAPI service
- **Frontend**: Next.js application
- **Worker**: Job processing service
- **Ingestors**: Data ingestion services

## Features

### Financial Models

- Monte Carlo Simulation (Geometric Brownian Motion)
- Markowitz Portfolio Optimization
- Black-Scholes Option Pricing
- Backtesting Framework

### Data Pipeline

- Real-time and historical price data
- Corporate actions and fundamentals
- Automated data ingestion and processing
- BigQuery data warehouse

### Job System

- Async job processing with Pub/Sub
- Progress tracking and result storage
- GCS artifact management
- Scalable worker architecture

## API Endpoints

- `POST /api/v1/jobs/`: Create new job
- `GET /api/v1/jobs/`: List user jobs
- `GET /api/v1/jobs/{id}`: Get job details
- `DELETE /api/v1/jobs/{id}`: Cancel job

## Development

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Code Quality

```bash
# Backend
flake8 app/
black app/
isort app/

# Frontend
npm run lint
npm run type-check
```

## License

MIT License
