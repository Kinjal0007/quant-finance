# 🚀 Quant Finance Platform

A comprehensive quantitative finance platform built with FastAPI, Next.js, and Google Cloud Platform. Features Monte Carlo simulations, Markowitz portfolio optimization, Black-Scholes option pricing, and real-time financial data processing.

## ✨ Features

- **📊 Financial Models**: Monte Carlo, Markowitz, Black-Scholes, Backtesting
- **🔄 Async Processing**: Pub/Sub + Cloud Run worker pattern
- **🌐 Modern UI**: Next.js 14 + TypeScript + Tailwind CSS
- **☁️ Cloud Native**: GCP Cloud Run, BigQuery, Cloud Storage
- **🔧 Development Ready**: Fixture data + MSW mocking for development
- **📈 Real-time Data**: EOD Historical Data + Twelve Data integration

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Frontend      │────│   Backend    │────│   Pub/Sub       │
│   (Next.js)     │    │   (FastAPI)  │    │   (Message Q)   │
│   Port 3000     │    │   Port 8080  │    │                 │
└─────────────────┘    └──────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌────────▼──────┐    ┌──────────▼──────┐    ┌──────────────▼──┐
│   Cloud       │    │   Cloud Run     │    │   BigQuery      │
│   Storage     │    │   (Worker)      │    │   (Data)        │
└───────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** with pip
- **Node.js 18+** with npm
- **GCP Project** with required APIs enabled
- **Docker** (for production deployment)

### Local Development

1. **Clone the repository**

```bash
git clone https://github.com/Kinjal0007/quant-finance.git
cd quant-finance
```

2. **Backend Setup**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Enable fixture mode (no API keys needed)
export USE_FIXTURE=true
export USE_SQLITE=true

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8080
```

3. **Frontend Setup**

```bash
cd frontend
npm install
npm run dev
```

4. **Open your browser**

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080/docs

## 🎯 Development Modes

### 1. **Frontend Only (MSW)**

```bash
cd frontend
npm run dev
# All API calls are mocked - perfect for UI development
```

### 2. **Frontend + Backend Fixture Mode**

```bash
# Terminal 1: Backend with demo data
cd backend
export USE_FIXTURE=true
uvicorn app.main:app --reload --port 8080

# Terminal 2: Frontend
cd frontend
npm run dev
# API calls hit real backend with demo data
```

### 3. **Production Mode**

```bash
# Configure real API keys and disable fixtures
export USE_FIXTURE=false
# Start backend and frontend as above
```

## 📁 Project Structure

```
quant-finance-platform/
├── backend/                    # FastAPI backend
│   ├── app/                   # Application code
│   │   ├── api/              # API endpoints
│   │   ├── models/           # Financial models
│   │   ├── schemas/          # Pydantic schemas
│   │   └── worker/           # Async worker
│   ├── worker/
│   │   ├── fixtures/         # Demo data
│   │   ├── demo_loader.py    # Fixture loader
│   │   ├── bq.py            # BigQuery integration
│   │   └── models.py        # Financial models
│   ├── alembic/              # Database migrations
│   └── requirements.txt      # Python dependencies
├── frontend/                  # Next.js frontend
│   ├── components/           # React components
│   ├── pages/                # Next.js pages
│   ├── mocks/                # MSW API mocking
│   ├── lib/                  # Utilities
│   └── package.json          # Node.js dependencies
├── .github/                   # GitHub Actions workflows
└── README.md                  # This file
```

## 🔧 API Endpoints

### Core Endpoints

- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

### Jobs API

- `POST /api/v1/jobs/` - Create financial model job
- `GET /api/v1/jobs/` - List jobs
- `GET /api/v1/jobs/{id}` - Get job details
- `DELETE /api/v1/jobs/{id}` - Cancel job

### Financial Models

- **Monte Carlo**: GBM simulations with risk metrics
- **Markowitz**: Portfolio optimization with Ledoit-Wolf covariance
- **Black-Scholes**: Option pricing with Greeks
- **Backtesting**: Strategy evaluation framework

## 🚀 Deployment

### GCP Cloud Run

```bash
# Backend API
gcloud run deploy quant-finance-api \
  --source ./backend \
  --platform managed \
  --region europe-west3 \
  --allow-unauthenticated

# Worker Service
gcloud run deploy quant-finance-worker \
  --source ./backend/worker \
  --platform managed \
  --region europe-west3 \
  --no-allow-unauthenticated
```

### Frontend (Cloud Storage)

```bash
# Build and deploy
cd frontend
npm run build
gsutil -m rsync -r -d .next gs://your-bucket/.next
gsutil web set -m index.html gs://your-bucket
```

## 🔐 Environment Variables

### Backend

```bash
GCP_PROJECT=your-project-id
GCP_REGION=europe-west3
USE_FIXTURE=true  # For development
USE_SQLITE=true   # For local development
```

### Frontend

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8080
```

## 🧪 Testing

### Backend

```bash
cd backend
pytest -v
```

### Frontend

```bash
cd frontend
npm test
npm run type-check
```

## 📊 Fixture Data

When `USE_FIXTURE=true`, the platform uses demo data:

- **3 Symbols**: AAPL, MSFT, GOOGL
- **~60 Days**: Realistic price data
- **All Models**: Work without vendor API keys

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** for the modern Python web framework
- **Next.js** for the React framework
- **Tailwind CSS** for the utility-first CSS framework
- **Google Cloud Platform** for the cloud infrastructure
- **EOD Historical Data** and **Twelve Data** for financial data

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Kinjal0007/quant-finance/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Kinjal0007/quant-finance/discussions)

---

**Built with ❤️ for quantitative finance enthusiasts**
