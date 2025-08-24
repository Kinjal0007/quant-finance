# 🚀 Quant Finance Platform

A production-ready quantitative finance platform built with FastAPI, Next.js, and Google Cloud Platform. Features Monte Carlo simulations, Markowitz portfolio optimization, Black-Scholes option pricing, and async job processing.

## ✨ Features

- **📊 Financial Models**: Monte Carlo, Markowitz, Black-Scholes, Backtesting
- **🔄 Async Processing**: Pub/Sub + Cloud Run worker pattern
- **🌐 Modern UI**: Next.js 14 + TypeScript + Tailwind CSS
- **☁️ Cloud Native**: GCP Cloud Run, BigQuery, Cloud Storage
- **🔧 Development Ready**: Fixture data + MSW mocking for local development
- **📈 Real-time Jobs**: Job creation, monitoring, and result visualization

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
│   Cloud       │    │   BigQuery     │    │   Cloud         │
│   Storage     │    │   (Data)       │    │   Storage       │
│   (Frontend)  │    │                 │    │   (Artifacts)   │
└───────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- GCP Project (optional for local development)

### 1. Clone Repository

```bash
git clone https://github.com/Kinjal0007/quant-finance.git
cd quant-finance
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env with your configuration

# Run database migrations
export USE_SQLITE=true
alembic upgrade head

# Start backend (fixture mode - no API keys needed)
export USE_FIXTURE=true
uvicorn app.main:app --reload --port 8080
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment (optional)
cp env.example .env

# Start development server
npm run dev
```

### 4. Access the Platform

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

## 🔧 Development Modes

### Mode 1: Frontend Only (MSW)

```bash
cd frontend
npm run dev
# All API calls are mocked - perfect for UI development
```

### Mode 2: Frontend + Backend (Fixtures)

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

### Mode 3: Production Mode

```bash
# Configure real API keys in .env
export USE_FIXTURE=false
# Start services with live data
```

## 📁 Project Structure

```
quant-finance-platform/
├── backend/                 # FastAPI backend
│   ├── app/                # Application code
│   │   ├── api/           # API endpoints
│   │   ├── models/        # Financial models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic
│   ├── worker/            # Async job processor
│   │   ├── fixtures/      # Demo data
│   │   └── demo_loader.py # Fixture data loader
│   ├── alembic/           # Database migrations
│   └── requirements.txt   # Python dependencies
├── frontend/               # Next.js frontend
│   ├── components/        # React components
│   ├── pages/            # Next.js pages
│   ├── mocks/            # MSW API mocking
│   ├── lib/              # Utilities
│   └── package.json      # Node.js dependencies
├── .github/               # GitHub Actions workflows
└── README.md              # This file
```

## 🎯 API Endpoints

### Jobs API

- `POST /api/v1/jobs/` - Create financial model job
- `GET /api/v1/jobs/` - List all jobs
- `GET /api/v1/jobs/{id}` - Get job details
- `DELETE /api/v1/jobs/{id}` - Cancel job

### Financial Models

- **Monte Carlo**: GBM simulations with risk metrics
- **Markowitz**: Global minimum-variance optimization
- **Black-Scholes**: Option pricing with Greeks
- **Backtesting**: Strategy evaluation framework

## 🚀 Deployment

### GitHub Actions (Recommended)

1. **Configure Secrets** in your repository:

   ```bash
   GCP_PROJECT=your-project-id
   GCP_REGION=europe-west3
   GCP_SA_KEY={"type": "service_account", ...}
   ```

2. **Push to main branch** triggers automatic deployment

### Manual Deployment

```bash
# Backend
cd backend
docker build -t quant-finance-api .
gcloud run deploy quant-finance-api --image quant-finance-api

# Frontend
cd frontend
npm run build
gsutil -m rsync -r .next gs://your-bucket/
```

## 🔒 Security

- **No API keys** in repository
- **Environment variables** for configuration
- **Service accounts** for GCP authentication
- **CORS protection** enabled
- **Input validation** with Pydantic

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

## 📚 Documentation

- [Backend README](backend/README.md) - Backend setup and API
- [Frontend README](frontend/README.md) - Frontend development
- [GitHub Actions](.github/README.md) - CI/CD workflows

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** for the backend framework
- **Next.js** for the frontend framework
- **Tailwind CSS** for styling
- **Google Cloud Platform** for infrastructure

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Kinjal0007/quant-finance/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Kinjal0007/quant-finance/discussions)

---

**Built with ❤️ for quantitative finance enthusiasts**
