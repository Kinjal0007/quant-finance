from __future__ import annotations

import base64
import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict

import pandas as pd
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from bq import get_bq_loader
from gcs import get_gcs_writer
from models import run_model

# Create FastAPI app
app = FastAPI(
    title="Quant Finance Platform Worker",
    description="Worker service for processing async financial modeling jobs",
    version="1.0.0",
)


@app.get("/")
async def root():
    """Root endpoint for basic connectivity test."""
    return {
        "service": "quant-finance-worker",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/healthz")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "quant-finance-worker",
        "version": "1.0.0",
    }


@app.post("/pubsub")
async def process_pubsub_message(request: Request):
    """
    Process Pub/Sub push message.

    This endpoint receives messages from Pub/Sub and processes financial modeling jobs.
    It verifies the Pub/Sub authentication header and processes the job.
    """
    try:
        # Verify Pub/Sub authentication (in production, this would be more robust)
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication",
            )

        # Get request body
        body = await request.json()

        # Extract message data
        message = body.get("message", {})
        data = message.get("data", "")

        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No message data"
            )

        # Decode base64 message
        try:
            decoded_data = base64.b64decode(data).decode("utf-8")
            job_data = json.loads(decoded_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid message format: {e}",
            )

        # Process the job
        await process_job(job_data)

        # Acknowledge message
        return JSONResponse(
            content={"status": "processed", "job_id": job_data.get("job_id")},
            status_code=200,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing Pub/Sub message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


async def process_job(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a financial modeling job.

    Args:
        job_data: Job data from Pub/Sub message

    Returns:
        Job processing results
    """
    job_id = job_data.get("job_id")
    job_type = job_data.get("type")
    symbols = job_data.get("symbols", [])
    start_date = job_data.get("start_date")
    end_date = job_data.get("end_date")
    interval = job_data.get("interval", "1d")
    vendor = job_data.get("vendor", "eodhd")
    adjusted = job_data.get("adjusted", True)
    params = job_data.get("params", {})

    print(f"Processing job {job_id}: {job_type} for symbols {symbols}")

    try:
        # Load data from BigQuery
        bq_loader = get_bq_loader()
        prices_df = bq_loader.load_prices(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            adjusted=adjusted,
            vendor=vendor,
        )

        print(f"Loaded {len(prices_df)} price records for {len(symbols)} symbols")

        # Run the financial model
        model_results = run_model(job_type, params, prices_df)

        # Write results to GCS
        gcs_writer = get_gcs_writer()

        # Write metrics
        metrics_path = gcs_writer.write_metrics_json(job_id, model_results["metrics"])

        # Write artifacts
        artifacts = [metrics_path]

        # Write price data
        if "prices" in model_results:
            prices_path = gcs_writer.write_artifact_dataframe(
                job_id, prices_df, "prices", "csv"
            )
            artifacts.append(prices_path)

        # Write model-specific artifacts
        if job_type == "montecarlo" and "paths" in model_results:
            # Convert paths to DataFrame
            paths_df = pd.DataFrame(model_results["paths"])
            paths_path = gcs_writer.write_artifact_dataframe(
                job_id, paths_df, "simulation_paths", "csv"
            )
            artifacts.append(paths_path)

        elif job_type == "markowitz" and "weights" in model_results:
            # Write weights
            weights_df = pd.DataFrame(model_results["weights"])
            weights_path = gcs_writer.write_artifact_dataframe(
                job_id, weights_df, "portfolio_weights", "csv"
            )
            artifacts.append(weights_path)

        # Write job summary
        gcs_writer.write_job_summary(
            job_id=job_id,
            job_type=job_type,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            metrics=model_results["metrics"],
            artifacts=artifacts,
        )

        # Generate signed URLs
        signed_urls = gcs_writer.generate_signed_urls(job_id)

        print(
            f"Job {job_id} completed successfully. "
            f"Generated {len(artifacts)} artifacts."
        )

        return {
            "job_id": job_id,
            "status": "completed",
            "artifacts": artifacts,
            "signed_urls": signed_urls,
            "metrics": model_results["metrics"],
        }

    except Exception as e:
        print(f"Error processing job {job_id}: {e}")

        # Write error to GCS
        try:
            gcs_writer = get_gcs_writer()
            error_data = {
                "job_id": job_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
            gcs_writer.write_metrics_json(job_id, error_data, "error.json")
        except Exception as gcs_error:
            print(f"Failed to write error to GCS: {gcs_error}")

        raise


@app.post("/test")
async def test_job_processing():
    """Test endpoint for job processing (development only)."""
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test endpoint not available in production",
        )

    # Test job data
    test_job = {
        "job_id": str(uuid.uuid4()),
        "type": "montecarlo",
        "symbols": ["AAPL"],
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "interval": "1d",
        "vendor": "eodhd",
        "adjusted": True,
        "params": {
            "simulations": 1000,
            "time_steps": 252,
            "risk_free_rate": 0.02,
            "confidence_level": 0.95,
        },
    }

    try:
        result = await process_job(test_job)
        return {"status": "success", "test_job": test_job, "result": result}
    except Exception as e:
        return {"status": "error", "test_job": test_job, "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
