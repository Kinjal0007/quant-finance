from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import jobs
from .database import check_db_connection, init_db
from .pubsub import get_pubsub_publisher


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Starting Quant Finance Platform API...")

    # Initialize database
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")

    # Check connections
    db_status = "connected" if check_db_connection() else "disconnected"
    pubsub_status = "connected" if get_pubsub_publisher().publisher else "disconnected"

    print(f"Database: {db_status}")
    print(f"Pub/Sub: {pubsub_status}")

    yield

    # Shutdown
    print("Shutting down Quant Finance Platform API...")


# Create FastAPI app
app = FastAPI(
    title="Quant Finance Platform API",
    description="Async financial modeling and analysis API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Quant Finance Platform API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    db_status = "connected" if check_db_connection() else "disconnected"
    pubsub_status = "connected" if get_pubsub_publisher().publisher else "disconnected"

    return {
        "status": "ok",
        "timestamp": "2024-01-15T12:00:00Z",
        "version": "1.0.0",
        "database": db_status,
        "pubsub": pubsub_status,
    }


@app.get("/api/health")
async def api_health():
    """API health check endpoint."""
    return await health()
