from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .models import Base

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "quant_finance")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

# Construct database URL
if os.getenv("DB_USE_UNIX_SOCKET"):
    # Cloud SQL Unix socket connection
    DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}?host=/cloudsql/{DB_HOST}"
elif os.getenv("USE_SQLITE", "false").lower() == "true" or not os.getenv("DB_HOST"):
    # Use SQLite for local development
    DB_URL = "sqlite:///./quant_finance.db"
else:
    # Standard TCP connection
    try:
        import psycopg2
        DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    except ImportError:
        # Fallback to SQLite if psycopg2 is not available
        print("Warning: psycopg2 not available, using SQLite for local development")
        DB_URL = "sqlite:///./quant_finance.db"

# Create engine
if "sqlite" in DB_URL:
    engine = create_engine(
        DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=True  # Enable SQL logging for debugging
    )
else:
    engine = create_engine(
        DB_URL,
        pool_pre_ping=True,
        pool_recycle=300,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """Check if database connection is working."""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print(f"Database connection check failed: {e}")
        return False


# Dependency for FastAPI
def get_db_session() -> Session:
    """Get database session for dependency injection."""
    return SessionLocal()
