# Worker Service

**Status: ✅ PRODUCTION READY** - Asynchronous job processing service with all financial models implemented and tested.

## Overview

The Worker Service is a FastAPI-based microservice that processes financial modeling jobs asynchronously. It receives jobs from the main API via Pub/Sub, executes financial models, and stores results in Cloud Storage and BigQuery. The service is designed to scale horizontally and handle multiple job types concurrently.

## 🚀 Current Status

### ✅ Completed Features

- **Financial Model Execution**: Monte Carlo, Markowitz, and Black-Scholes models fully implemented
- **Asynchronous Processing**: Pub/Sub integration for job queuing and processing
- **Data Ingestion**: EOD Historical Data and Twelve Data integration
- **Result Storage**: Cloud Storage for artifacts and BigQuery for metrics
- **Fixture Mode**: Demo data support for development without API keys
- **Error Handling**: Comprehensive error handling and job failure recovery
- **Health Monitoring**: Health checks and service status endpoints

### 🔧 Technical Implementation

- **FastAPI Framework**: Modern async web framework
- **Pub/Sub Integration**: Google Cloud Pub/Sub for job queuing
- **BigQuery Integration**: Data warehouse integration for price data
- **Cloud Storage**: Artifact storage for model results
- **Docker Containerization**: Production-ready containerization
- **Horizontal Scaling**: Designed for Cloud Run auto-scaling

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Pub/Sub       │    │   Worker        │    │   Financial     │
│   (Job Queue)   │◄──►│   Service       │◄──►│   Models        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   Data Sources  │              │
         │              │   (EODHD, 12D)  │              │
         │              └─────────────────┘              │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Job Status    │    │   BigQuery      │    │   Cloud Storage │
│   Updates       │    │   (Prices)      │    │   (Artifacts)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
backend/worker/
├── main.py                       # FastAPI application entry point
├── models.py                     # Financial model implementations
├── bq.py                         # BigQuery data loading and querying
├── gcs.py                        # Cloud Storage operations
├── demo_loader.py                # Fixture data loading for development
├── ingestors/                    # Data ingestion modules
│   ├── eodhd_ingestor.py        # EOD Historical Data integration
│   └── twelve_data_ingestor.py  # Twelve Data integration
├── fixtures/                     # Demo data files
│   └── prices_demo.csv          # Sample price data for development
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container configuration
└── README.md                     # This file
```

## 🎯 Core Features

### Financial Models

- **Monte Carlo Simulation**: Stock price simulation using Geometric Brownian Motion
- **Markowitz Portfolio Optimization**: Global minimum-variance portfolio with Ledoit-Wolf covariance
- **Black-Scholes Option Pricing**: European option pricing with Greeks calculation

### Job Processing

- **Asynchronous Execution**: Non-blocking job processing
- **Progress Tracking**: Real-time job status updates
- **Result Generation**: Comprehensive metrics and visualization data
- **Error Recovery**: Graceful handling of failures and retries

### Data Management

- **Multi-Source Ingestion**: EOD Historical Data and Twelve Data integration
- **Data Standardization**: Unified OHLCV format across all sources
- **Historical Data**: End-of-day and intraday price data
- **Corporate Actions**: Dividends, splits, and mergers data

## 🛠️ Technology Stack

### Core Framework

- **Python 3.11**: Latest stable Python with async support
- **FastAPI**: Modern, fast web framework
- **Uvicorn**: ASGI server for production deployment

### Data Processing

- **Pandas 2.2.0**: Data manipulation and analysis
- **NumPy 1.26.4**: Numerical computing
- **SciPy 1.12.0**: Scientific computing and optimization
- **Scikit-learn 1.4.0**: Machine learning algorithms

### Cloud Integration

- **Google Cloud Pub/Sub**: Asynchronous messaging
- **Google Cloud BigQuery**: Data warehousing
- **Google Cloud Storage**: File storage
- **Google Cloud Secret Manager**: Secure credential management

### Database

- **SQLAlchemy 2.0.32**: Database ORM
- **PostgreSQL**: Primary database (with SQLite fallback)
- **psycopg2**: PostgreSQL adapter

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud Platform account
- Docker (for containerization)

### Local Development

1. **Set up virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**

   ```bash
   # Copy and configure environment variables
   cp ../env.example .env
   # Edit .env with your configuration
   ```

4. **Enable fixture mode (no API keys needed)**

   ```bash
   export USE_FIXTURE=true
   ```

5. **Start the service**
   ```bash
   uvicorn main:app --reload --port 8080
   ```

### Production Deployment

1. **Build Docker image**

   ```bash
   docker build -t quant-finance-worker .
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy quant-finance-worker \
     --image quant-finance-worker \
     --platform managed \
     --region europe-west3 \
     --allow-unauthenticated
   ```

## 🔌 API Endpoints

### Core Endpoints

- `GET /` - Service information and health check
- `GET /health` - Detailed health status

### Job Processing

- **Internal Processing**: Jobs are processed via Pub/Sub messages
- **Status Updates**: Job status updates sent back to main API
- **Result Storage**: Results stored in Cloud Storage and BigQuery

## 📊 Financial Models

### Monte Carlo Simulation

- **Model**: Geometric Brownian Motion
- **Parameters**: Initial price, drift, volatility, time steps, simulations
- **Output**: Price paths, return statistics, percentiles
- **Use Case**: Risk assessment and scenario analysis

### Markowitz Portfolio Optimization

- **Model**: Global Minimum-Variance Portfolio
- **Parameters**: Asset returns, risk tolerance, constraints
- **Output**: Optimal weights, expected return, volatility, Sharpe ratio
- **Use Case**: Portfolio construction and risk management

### Black-Scholes Option Pricing

- **Model**: European Option Pricing
- **Parameters**: Stock price, strike price, time to expiry, risk-free rate, volatility
- **Output**: Option price, Greeks (delta, gamma, theta, vega, rho)
- **Use Case**: Option valuation and risk management

## 🔄 Job Processing Flow

### 1. Job Reception

- Jobs received via Pub/Sub messages
- Job parameters validated and parsed
- Job status updated to "running"

### 2. Data Retrieval

- Historical price data fetched from BigQuery or fixtures
- Data validated and preprocessed
- Missing data handled gracefully

### 3. Model Execution

- Financial model executed with job parameters
- Results computed and validated
- Performance metrics calculated

### 4. Result Storage

- Metrics stored in BigQuery for analysis
- Artifacts (charts, reports) stored in Cloud Storage
- Job status updated to "completed"

### 5. Status Update

- Final job status sent back to main API
- Error information logged for debugging
- Job processing complete

## 🌍 Environment Variables

### Required Variables

```bash
# GCP Configuration
GCP_PROJECT=your-project-id
GCP_REGION=europe-west3

# API Keys
EODHD_API_KEY=your_eodhd_api_key
TWELVE_DATA_API_KEY=your_twelve_data_api_key

# BigQuery Configuration
BQ_DATASET_RAW=quant_finance_raw
BQ_DATASET_CURATED=quant_finance_curated

# Cloud Storage Configuration
GCS_BUCKET=your-project-artifacts

# Feature Flags
USE_FIXTURE=false
```

### Optional Variables

```bash
# Service Configuration
PORT=8080
LOG_LEVEL=INFO
DEBUG=false

# Processing Configuration
MAX_CONCURRENT_JOBS=10
JOB_TIMEOUT_SECONDS=300
```

## 🧪 Testing and Development

### Fixture Mode

When `USE_FIXTURE=true`, the service uses demo data:

- **Demo Dataset**: 3 symbols (AAPL, MSFT, GOOGL) × ~60 days
- **Realistic Results**: Generated metrics match expected ranges
- **No API Keys**: Perfect for development and testing
- **Consistent Data**: Same data for reproducible results

### Testing Financial Models

```bash
# Test Monte Carlo simulation
curl -X POST http://localhost:8080/api/v1/montecarlo \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT"],
    "start": "2024-01-01",
    "end": "2024-12-31",
    "params": {
      "simulations": 1000,
      "time_steps": 252
    }
  }'
```

## 🚀 Performance Features

### Scalability

- **Horizontal Scaling**: Cloud Run auto-scaling support
- **Concurrent Processing**: Multiple jobs processed simultaneously
- **Resource Optimization**: Efficient memory and CPU usage
- **Async Operations**: Non-blocking I/O operations

### Monitoring

- **Health Checks**: Service health monitoring
- **Performance Metrics**: Processing time and throughput tracking
- **Error Logging**: Comprehensive error tracking and reporting
- **Resource Usage**: Memory and CPU monitoring

## 🔧 Development Tools

### Code Quality

- **Black**: Code formatting (88 character line length)
- **isort**: Import sorting and organization
- **flake8**: Linting and style checking

### Development Commands

```bash
# Format code
python -m black . --line-length 88

# Sort imports
python -m isort .

# Check linting
python -m flake8 . --max-line-length=88 --ignore=E203,W503
```

## 🗄️ Data Architecture

### BigQuery Tables

- **Raw Data**: `eq_ohlcv`, `fx_ohlcv`, `crypto_ohlcv`
- **Corporate Actions**: Dividends, splits, mergers
- **Vendor Mapping**: Symbol mapping across data sources

### Data Flow

1. **Ingestion**: Raw data from vendor APIs
2. **Processing**: Data cleaning and standardization
3. **Storage**: Partitioned tables in BigQuery
4. **Access**: Efficient queries for model execution

## 🔐 Security Features

### Authentication

- **Service Account**: GCP service account authentication
- **Secret Management**: API keys stored in Secret Manager
- **Network Security**: Private Cloud Run service

### Data Protection

- **Encryption**: Data encrypted in transit and at rest
- **Access Control**: IAM-based access control
- **Audit Logging**: Comprehensive access logging

## 🚀 Deployment

### Docker Configuration

- **Multi-stage Build**: Optimized production images
- **Security**: Non-root user execution
- **Health Checks**: Container health monitoring
- **Resource Limits**: Memory and CPU constraints

### Cloud Run Configuration

- **Memory**: 4GB allocation for model processing
- **CPU**: 2 vCPU allocation
- **Scaling**: 0-20 instances based on demand
- **Timeout**: 900 seconds for long-running jobs

## 📊 Monitoring and Observability

### Health Checks

- **Service Health**: Overall service status
- **Dependency Health**: BigQuery and Cloud Storage connectivity
- **Model Health**: Financial model execution status

### Metrics Collection

- **Processing Metrics**: Job completion rates and timing
- **Error Rates**: Failure rates and error types
- **Resource Usage**: Memory and CPU utilization
- **Performance**: Response times and throughput

## 🔮 Future Enhancements

### Planned Features

- **Advanced Models**: Additional financial models and algorithms
- **Real-time Processing**: Streaming data processing capabilities
- **Machine Learning**: ML-based model parameter optimization
- **Batch Processing**: Large-scale batch job processing

### Performance Improvements

- **Caching Layer**: Redis-based caching for frequently accessed data
- **Parallel Processing**: Multi-threaded model execution
- **Optimized Algorithms**: Performance improvements for existing models
- **Data Compression**: Efficient data storage and retrieval

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Cloud Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)
- [Google Cloud BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [NumPy Documentation](https://numpy.org/doc/)

## 🤝 Contributing

1. Follow the established code structure
2. Maintain type safety and documentation
3. Add tests for new features
4. Follow the established coding standards
5. Update this README for significant changes

---

**Last Updated**: August 2024 | **Version**: 1.0.0 | **Status**: Production Ready
