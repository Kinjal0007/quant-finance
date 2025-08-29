# Backend API Service

FastAPI-based REST API for the Quant Finance Platform, handling job creation, data access, and coordination with the Worker Service.

## 🚀 Features

- **Job Management**: Create, monitor, and manage financial modeling jobs
- **Data Access**: Market data and symbol information APIs
- **Pub/Sub Integration**: Asynchronous job queuing system
- **Database Models**: SQLAlchemy models with Alembic migrations
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Worker        │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   Service       │
│                 │    │                 │    │                 │
│ • Job Forms     │    │ • Job Creation  │    │ • Model         │
│ • Monitoring    │    │ • Job Status    │    │   Execution     │
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

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLite fallback
- **ORM**: SQLAlchemy 2.0 with Alembic migrations
- **Job Queue**: Google Cloud Pub/Sub
- **Data Validation**: Pydantic models

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (optional, SQLite works for development)

### Setup

1. **Install dependencies**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment variables**

```bash
# Create .env file
DATABASE_URL=sqlite:///./quant_finance.db
USE_SQLITE=true
GCP_PROJECT=your-project-id
GCP_REGION=your-region
```

3. **Database setup**

```bash
alembic upgrade head
```

4. **Run the server**

```bash
uvicorn app.main:app --reload --port 8080
```

## 📚 API Endpoints

### Job Management

- `POST /api/v1/jobs/` - Create new job
- `GET /api/v1/jobs/` - List jobs
- `GET /api/v1/jobs/{id}` - Get job details
- `DELETE /api/v1/jobs/{id}` - Cancel job

### Data Access

- `GET /api/v1/symbols` - Available symbols
- `GET /health` - Health check

### API Documentation

- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

## 🧪 Development

### Running Tests

```bash
python -m pytest
```

### Code Formatting

```bash
python -m black app/ --line-length 88
python -m isort app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Core configuration
│   ├── models/        # Database models
│   └── main.py        # FastAPI application
├── alembic/           # Database migrations
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🔧 Configuration

### Environment Variables

| Variable       | Description                | Default                        |
| -------------- | -------------------------- | ------------------------------ |
| `DATABASE_URL` | Database connection string | `sqlite:///./quant_finance.db` |
| `USE_SQLITE`   | Use SQLite for development | `true`                         |
| `GCP_PROJECT`  | Google Cloud project ID    | Required for production        |
| `GCP_REGION`   | Google Cloud region        | Required for production        |

## 🚀 Deployment

### Docker

```bash
docker build -t quant-finance-api .
docker run -p 8080:8080 quant-finance-api
```

### Google Cloud Run

```bash
gcloud run deploy quant-finance-api \
  --image gcr.io/PROJECT_ID/quant-finance-api \
  --platform managed \
  --region REGION \
  --allow-unauthenticated
```

## 📚 Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
