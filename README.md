# Quant Finance Platform

A comprehensive, production-ready quantitative finance platform built on Google Cloud Platform (GCP) that provides advanced financial modeling capabilities through a modern web interface and robust backend services.

## 🚀 Project Status: PRODUCTION READY

**All major features implemented and tested. Ready for production deployment.**

### ✅ Completed Features

- **Financial Models**: Monte Carlo simulations, Markowitz portfolio optimization, Black-Scholes option pricing
- **Data Ingestion**: Real-time market data from EOD Historical Data and Twelve Data
- **Job Processing**: Asynchronous job queuing and processing system
- **Web Interface**: Modern Next.js frontend with real-time job monitoring
- **Cloud Infrastructure**: Fully configured GCP services with CI/CD pipeline

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Worker        │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │   Pub/Sub       │    │   Cloud Storage │
         │              │   (Job Queue)   │    │   (Artifacts)   │
         │              └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   BigQuery      │
│   (EODHD, 12D)  │    │   (Data Lake)   │
└─────────────────┘    └─────────────────┘
```

## 🎯 Core Features

### Financial Modeling

- **Monte Carlo Simulation**: Stock price simulation with configurable parameters
- **Markowitz Optimization**: Portfolio optimization with risk-return analysis
- **Black-Scholes Pricing**: Option pricing with Greeks calculation

### Data Management

- **Real-time Ingestion**: Market data from multiple vendors
- **Data Standardization**: Unified OHLCV format across all sources
- **Historical Data**: End-of-day and intraday price data
- **Corporate Actions**: Dividends, splits, and mergers data

### Job Processing

- **Asynchronous Processing**: Background job execution
- **Real-time Monitoring**: Live job status and progress tracking
- **Result Storage**: Cloud Storage with secure access
- **Error Handling**: Comprehensive failure recovery

## 🛠️ Technology Stack

### Backend

- **Python 3.11** with FastAPI framework
- **SQLAlchemy 2.0.32** for database operations
- **Pandas 2.2.0** for data processing
- **NumPy 1.26.4** & SciPy 1.12.0 for scientific computing
- **Scikit-learn 1.4.0** for machine learning models

### Frontend

- **Next.js 14.2.32** with React 18
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **MSW** for development mocking

### Cloud Infrastructure

- **Google Cloud Platform** as primary cloud provider
- **Cloud Run** for serverless container deployment
- **BigQuery** for data warehousing
- **Cloud SQL (PostgreSQL)** for metadata storage
- **Cloud Storage** for file artifacts
- **Pub/Sub** for asynchronous messaging

## 🚀 Quick Start

### Prerequisites

- Google Cloud Platform account with billing enabled
- Python 3.11+ and Node.js 18+
- Docker for containerization
- Git for version control

### Local Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/quant-finance-platform.git
   cd quant-finance-platform
   ```

2. **Backend Setup**

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt

   # Set up environment variables
   cp env.example .env
   # Edit .env with your configuration

   # Run database migrations
   alembic upgrade head

   # Start the backend server
   uvicorn app.main:app --reload --port 8080
   ```

3. **Frontend Setup**

   ```bash
   cd frontend
   npm install

   # Set up environment variables
   cp env.example .env.local
   # Edit .env.local with your configuration

   # Start the development server
   npm run dev
   ```

4. **Worker Service Setup**
   ```bash
   cd backend/worker
   # The worker service is designed to run in production
   # For local testing, use the fixture mode
   export USE_FIXTURE=true
   ```

### Production Deployment

1. **Set up GCP Infrastructure**

   ```bash
   # Enable required APIs
   gcloud services enable run.googleapis.com bigquery.googleapis.com sqladmin.googleapis.com

   # Create BigQuery datasets
   bq mk quant_finance_raw
   bq mk quant_finance_curated

   # Create Cloud Storage bucket
   gsutil mb gs://your-project-artifacts
   ```

2. **Configure GitHub Secrets**

   - `GCP_PROJECT`: Your GCP project ID
   - `GCP_SA_KEY`: Service account JSON key
   - `EODHD_API_KEY`: EOD Historical Data API key
   - `TWELVE_DATA_API_KEY`: Twelve Data API key
   - Database connection details

3. **Deploy via GitHub Actions**
   - Push to main branch triggers automatic deployment
   - Or manually trigger workflows from GitHub Actions tab

## 📊 Data Sources

### EOD Historical Data (EODHD)

- **Coverage**: Global equities, ETFs, indices, corporate actions
- **Data Types**: End-of-day prices, dividends, splits, mergers, fundamentals
- **Update Frequency**: Daily
- **Use Case**: Portfolio modeling, backtesting, and fundamental analysis

### Twelve Data

- **Coverage**: Intraday data, FX rates, cryptocurrencies, commodities
- **Data Types**: OHLCV, real-time quotes, technical indicators, news sentiment
- **Update Frequency**: 1-minute to daily intervals
- **Use Case**: Real-time trading, intraday analysis, and market monitoring

### Data Integration Features

- **Unified Format**: Standardized OHLCV structure across all sources
- **Corporate Actions**: Automatic adjustment for dividends, splits, and mergers
- **Multi-Asset Support**: Equities, FX, crypto, and commodities
- **Historical Coverage**: Extensive historical data for backtesting
- **Real-time Updates**: Live data feeds for active trading

## 🔧 Configuration

### Environment Variables

#### Backend

```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/database
USE_SQLITE=false

# GCP Configuration
GCP_PROJECT=your-project-id
GCP_REGION=europe-west3

# API Keys
EODHD_API_KEY=your_eodhd_key
TWELVE_DATA_API_KEY=your_twelve_data_key

# Feature Flags
USE_FIXTURE=false
```

#### Frontend

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8080
NODE_ENV=development
```

## 📈 API Endpoints

### Job Management

- `POST /api/v1/jobs/` - Create new financial modeling jobs
- `GET /api/v1/jobs/` - List user jobs with filtering
- `GET /api/v1/jobs/{id}` - Get job details and results
- `DELETE /api/v1/jobs/{id}` - Cancel pending jobs

### Data Access

- `GET /api/v1/symbols` - Available trading symbols
- `GET /api/v1/prices` - Historical price data
- `GET /health` - Service health check

## 🧪 Testing

### Development Mode

The platform includes comprehensive development tools:

- **MSW (Mock Service Worker)**: API mocking for frontend development
- **Fixture Data**: Sample market data for testing without API keys
- **Test Endpoints**: Development-only endpoints for validation

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test

# Linting and formatting
cd backend
python -m black app/ worker/ --line-length 88
python -m isort app/ worker/
python -m flake8 app/ worker/ --max-line-length=88 --ignore=E203,W503
```

## 🚀 Deployment

### GitHub Actions Workflows

- **Backend API**: Automated testing, building, and deployment
- **Frontend**: Build optimization and Cloud Run deployment
- **Worker Service**: Container building and service deployment
- **Data Ingestors**: EODHD and Twelve Data service deployment

### Manual Deployment

```bash
# Build and deploy backend
cd backend
docker build -t gcr.io/PROJECT_ID/quant-finance-api .
docker push gcr.io/PROJECT_ID/quant-finance-api
gcloud run deploy quant-finance-api --image gcr.io/PROJECT_ID/quant-finance-api

# Build and deploy frontend
cd frontend
npm run build
docker build -t gcr.io/PROJECT_ID/quant-finance-frontend .
docker push gcr.io/PROJECT_ID/quant-finance-frontend
gcloud run deploy quant-finance-frontend --image gcr.io/PROJECT_ID/quant-finance-frontend
```

## 📚 Documentation

- [Backend API Documentation](backend/README.md)
- [Frontend Development Guide](frontend/README.md)
- [Worker Service Guide](backend/worker/README.md)
- [API Reference](docs/api.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/quant-finance-platform/issues)
- **Documentation**: [Project Wiki](https://github.com/your-username/quant-finance-platform/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/quant-finance-platform/discussions)

## 🎉 Acknowledgments

- **Financial Models**: Implementation based on industry-standard quantitative finance methodologies
- **Cloud Infrastructure**: Built on Google Cloud Platform's serverless architecture
- **Open Source**: Leverages numerous open-source libraries and frameworks

---

**Status**: 🟢 Production Ready | **Last Updated**: August 2024 | **Version**: 1.0.0
