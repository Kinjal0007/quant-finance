# Quant Finance Platform

A quantitative finance platform for financial modeling and analysis, built with modern web technologies and cloud infrastructure.

## 🚀 Features

- **Financial Models**: Monte Carlo simulation, Markowitz portfolio optimization, Black-Scholes option pricing
- **Data Integration**: Market data from EOD Historical Data and Twelve Data
- **Job Processing**: Asynchronous job execution with real-time monitoring
- **Modern UI**: Responsive web interface built with Next.js and TypeScript
- **Cloud-Native**: Built for Google Cloud Platform with auto-scaling

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Worker        │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   Service       │
│                 │    │                 │    │                 │
│ • Job Forms     │    │ • Job Creation  │    │ • Model         │
│ • Monitoring    │    │ • Job Status    │    │ • Job Execution │
│ • Results       │    │ • User Mgmt     │    │ • Data          │
│ • Navigation    │    │ • Auth          │    │   Processing    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
           │                       │                       │
           │                       ▼                       │
           │              ┌─────────────────┐              │
           │              │   Pub/Sub       │              │
           │              │   (Job Queue)   │              │
           │              │                 │              │
           │              │ • Async Jobs    │              │
           │              │ • Status Updates│              │
           │              │ • Error Handling│              │
           │              └─────────────────┘              │
           │                       │                       │
           ▼                       ▼                       ▼
  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
  │   BigQuery      │    │   Cloud         │    │   EODHD &       │
  │   (Data         │    │   Storage       │    │   Twelve Data   │
  │   Warehouse)    │    │   (Artifacts)   │    │   (Market Data) │
  └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 Data Sources

### EOD Historical Data (EODHD)

- **Coverage**: Global equities, ETFs, indices
- **Data Types**: End-of-day prices, corporate actions
- **Update Frequency**: Daily
- **Use Case**: Portfolio modeling and analysis

### Twelve Data

- **Coverage**: Intraday data, FX rates, cryptocurrencies
- **Data Types**: OHLCV, real-time quotes
- **Update Frequency**: 1-minute to daily intervals
- **Use Case**: Real-time trading and intraday analysis

## 🛠️ Tech Stack

### Backend

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLite fallback
- **ORM**: SQLAlchemy 2.0 with Alembic migrations
- **Job Queue**: Google Cloud Pub/Sub
- **Data Processing**: Pandas, NumPy, SciPy

### Frontend

- **Framework**: Next.js 14 with TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React hooks
- **API Mocking**: MSW for development

### Infrastructure

- **Cloud**: Google Cloud Platform
- **Compute**: Cloud Run (serverless)
- **Database**: Cloud SQL (PostgreSQL)
- **Data Warehouse**: BigQuery
- **Storage**: Cloud Storage
- **CI/CD**: GitHub Actions

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker
- Google Cloud SDK

### Local Development

1. **Clone and setup**

```bash
git clone https://github.com/Kinjal0007/quant-finance.git
cd quant-finance
```

2. **Backend setup**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

3. **Frontend setup**

```bash
cd frontend
npm install
npm run dev
```

4. **Worker service**

```bash
cd backend/worker
python main.py
```

### Environment Variables

Create `.env` files in each service directory:

**Backend** (`.env`):

```bash
DATABASE_URL=sqlite:///./quant_finance.db
USE_SQLITE=true
GCP_PROJECT=your-project-id
GCP_REGION=your-region
```

**Frontend** (`.env.local`):

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8080
```

## 📚 Documentation

- [Backend API](backend/README.md)
- [Frontend Development](frontend/README.md)
- [Worker Service](backend/worker/README.md)
- [Data Ingestors](services/ingestor_eodhd/README.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This is a development project for educational and portfolio purposes. Not intended for production financial trading or investment decisions.
