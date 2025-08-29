# Worker Service

FastAPI-based microservice for processing financial modeling jobs asynchronously. Receives jobs via Pub/Sub, executes financial models, and stores results.

## 🚀 Features

- **Financial Models**: Monte Carlo, Markowitz, and Black-Scholes implementations
- **Asynchronous Processing**: Pub/Sub integration for job queuing
- **Data Ingestion**: EOD Historical Data and Twelve Data integration
- **Result Storage**: Cloud Storage for artifacts and BigQuery for metrics
- **Fixture Mode**: Demo data support for development

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
- **Markowitz Portfolio Optimization**: Global minimum-variance portfolio optimization
- **Black-Scholes Option Pricing**: European option pricing with Greeks calculation

### Job Processing

- **Asynchronous Execution**: Non-blocking job processing
- **Progress Tracking**: Job status updates
- **Result Generation**: Metrics and visualization data
- **Error Handling**: Failure handling and recovery

### Data Management

- **Multi-Source Ingestion**: EOD Historical Data and Twelve Data integration
- **Data Standardization**: Unified OHLCV format
- **Historical Data**: End-of-day and intraday price data
- **Corporate Actions**: Dividends, splits, and mergers data

## 🛠️ Tech Stack

- **Framework**: FastAPI with Python 3.11+
- **Data Processing**: Pandas, NumPy, SciPy, Scikit-learn
- **Cloud Integration**: BigQuery, Cloud Storage, Pub/Sub
- **Containerization**: Docker with Cloud Run deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud SDK
- BigQuery and Cloud Storage access

### Setup

1. **Install dependencies**

```bash
cd backend/worker
pip install -r requirements.txt
```

2. **Environment variables**

```bash
# Create .env file
GCP_PROJECT=your-project-id
GCP_REGION=your-region
EODHD_API_KEY=your_eodhd_key
TWELVE_DATA_API_KEY=your_twelve_data_key
USE_FIXTURE=true  # For development without API keys
```

3. **Run the service**

```bash
python main.py
```

## 🔧 Configuration

### Environment Variables

| Variable              | Description                   | Required                   |
| --------------------- | ----------------------------- | -------------------------- |
| `GCP_PROJECT`         | Google Cloud project ID       | Yes                        |
| `GCP_REGION`          | Google Cloud region           | Yes                        |
| `EODHD_API_KEY`       | EOD Historical Data API key   | No (if using fixture mode) |
| `TWELVE_DATA_API_KEY` | Twelve Data API key           | No (if using fixture mode) |
| `USE_FIXTURE`         | Use demo data for development | No (default: false)        |

### Fixture Mode

For development without vendor API keys, set `USE_FIXTURE=true`. This will use sample data from `fixtures/prices_demo.csv`.

## 📚 API Endpoints

### Health Check

- `GET /health` - Service health status

### Job Processing

- Jobs are processed via Pub/Sub messages
- Results stored in BigQuery and Cloud Storage
- Status updates sent back to main API

## 🧪 Development

### Running Locally

```bash
# With fixture mode (no API keys needed)
export USE_FIXTURE=true
python main.py

# With real API keys
export USE_FIXTURE=false
export EODHD_API_KEY=your_key
export TWELVE_DATA_API_KEY=your_key
python main.py
```

### Testing

```bash
# Run tests (when implemented)
python -m pytest

# Check code quality
python -m black . --line-length 88
python -m isort .
```

## 🚀 Deployment

### Docker

```bash
docker build -t quant-finance-worker .
docker run -p 8000:8000 quant-finance-worker
```

### Google Cloud Run

```bash
gcloud run deploy quant-finance-worker \
  --image gcr.io/PROJECT_ID/quant-finance-worker \
  --platform managed \
  --region REGION \
  --allow-unauthenticated
```

## 📊 Financial Models

### Monte Carlo Simulation

- **Purpose**: Stock price simulation and risk analysis
- **Parameters**: Initial price, drift, volatility, time steps, simulations
- **Output**: Price distribution, percentiles, risk metrics

### Markowitz Portfolio Optimization

- **Purpose**: Optimal portfolio allocation
- **Parameters**: Asset symbols, time period, risk tolerance
- **Output**: Optimal weights, expected return, volatility, Sharpe ratio

### Black-Scholes Option Pricing

- **Purpose**: European option valuation
- **Parameters**: Stock price, strike price, time to expiry, risk-free rate, volatility
- **Output**: Option price, Greeks (delta, gamma, theta, vega, rho)

## 🔍 Troubleshooting

### Common Issues

1. **GCP Authentication**: Ensure service account has proper permissions
2. **BigQuery Access**: Check dataset and table permissions
3. **API Rate Limits**: Monitor vendor API usage
4. **Memory Issues**: Adjust Cloud Run memory allocation

### Logs

- Check Cloud Run logs for detailed error information
- Monitor Pub/Sub message processing
- Verify BigQuery and Cloud Storage operations

## 📚 Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Cloud Pub/Sub](https://cloud.google.com/pubsub/docs)
- [BigQuery Python Client](https://googleapis.dev/python/bigquery/latest/index.html)
- [Cloud Storage Python Client](https://googleapis.dev/python/storage/latest/index.html)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
