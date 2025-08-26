from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_active_user
from ..database import get_db
from ..models import Job, User
from ..pubsub import get_pubsub_publisher
from ..schemas import (
    CreateJobRequest,
    JobCreateResponse,
    JobListResponse,
    JobStatusResponse,
    JobType,
)

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


@router.post("/", response_model=JobCreateResponse)
async def create_job(
    job_request: CreateJobRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a new async job.

    This endpoint validates the job request, creates a job record in the database,
    and publishes a message to Pub/Sub for the worker to process.
    """
    try:
        # Create job in database
        job = Job.create_job(
            db=db,
            user_id=current_user.id,
            job_type=job_request.type.value,
            symbols=job_request.symbols,
            start_date=job_request.start,
            end_date=job_request.end,
            interval=job_request.interval.value,
            vendor=job_request.vendor.value if job_request.vendor else "eodhd",
            adjusted=job_request.adjusted,
            params=(
                job_request.params.dict()
                if hasattr(job_request.params, "dict")
                else job_request.params
            ),
        )

        # Publish to Pub/Sub
        pubsub = get_pubsub_publisher()
        message_data = {
            "job_id": str(job.id),
            "user_id": str(job.user_id),
            "type": job.type,
            "symbols": job.symbols,
            "start_date": job_request.start,
            "end_date": job_request.end,
            "interval": job.interval,
            "vendor": job.vendor,
            "adjusted": job.adjusted,
            "params": job.params_json,
        }

        pubsub.publish_job(message_data)

        # Estimate duration based on job type
        estimated_duration = _estimate_job_duration(
            job_request.type, len(job_request.symbols)
        )

        return JobCreateResponse(
            job_id=job.id,
            status=job.status,
            message="Job queued successfully",
            estimated_duration=estimated_duration,
        )

    except Exception as e:
        # Rollback database transaction
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}",
        )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get job status and results.

    Returns job information including current status, metrics, and signed URLs
    to results stored in Google Cloud Storage.
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job ID format"
        )

    job = Job.get_job(db, job_uuid)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    # Check if user owns this job (for future multi-user support)
    if str(job.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Convert to response schema
    return JobStatusResponse(
        job_id=job.id,
        user_id=job.user_id,
        type=JobType(job.type),
        status=job.status,
        symbols=job.symbols,
        start=job.start_ts.strftime("%Y-%m-%d") if job.start_ts else "",
        end=job.end_ts.strftime("%Y-%m-%d") if job.end_ts else "",
        interval=job.interval,
        vendor=job.vendor,
        adjusted=job.adjusted,
        params=job.params_json,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        metrics=job.result_refs.get("metrics") if job.result_refs else None,
        result_urls=job.result_refs.get("urls") if job.result_refs else None,
        error=job.error,
        progress=_calculate_job_progress(job),
    )


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    job_type: Optional[JobType] = Query(None, description="Filter by job type"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List user's jobs with pagination and filtering.
    """
    # Get jobs for current user
    jobs, total = Job.get_user_jobs(db, current_user.id, page, size)

    # Apply filters if provided
    if job_type or status_filter:
        filtered_jobs = []
        for job in jobs:
            if job_type and job.type != job_type.value:
                continue
            if status_filter and job.status != status_filter:
                continue
            filtered_jobs.append(job)
        jobs = filtered_jobs

    # Convert to response schema
    job_responses = []
    for job in jobs:
        job_responses.append(
            JobStatusResponse(
                job_id=job.id,
                user_id=job.user_id,
                type=JobType(job.type),
                status=job.status,
                symbols=job.symbols,
                start=job.start_ts.strftime("%Y-%m-%d") if job.start_ts else "",
                end=job.end_ts.strftime("%Y-%m-%d") if job.end_ts else "",
                interval=job.interval,
                vendor=job.vendor,
                adjusted=job.adjusted,
                params=job.params_json,
                created_at=job.created_at,
                started_at=job.started_at,
                finished_at=job.finished_at,
                metrics=job.result_refs.get("metrics") if job.result_refs else None,
                result_urls=job.result_refs.get("urls") if job.result_refs else None,
                error=job.error,
                progress=_calculate_job_progress(job),
            )
        )

    return JobListResponse(
        jobs=job_responses,
        total=total,
        page=page,
        size=size,
        has_next=(page * size) < total,
    )


@router.delete("/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Cancel a queued job.

    Only queued jobs can be cancelled. Running or completed jobs cannot be cancelled.
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job ID format"
        )

    job = Job.get_job(db, job_uuid)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    # Check if user owns this job
    if str(job.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Only queued jobs can be cancelled
    if job.status != "queued":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only queued jobs can be cancelled",
        )

    # Update job status to cancelled
    job.update_status(db, "cancelled")

    return {"message": "Job cancelled successfully"}


def _estimate_job_duration(job_type: JobType, num_symbols: int) -> int:
    """Estimate job duration in seconds."""
    base_duration = {
        JobType.MONTE_CARLO: 30,
        JobType.MARKOWITZ: 15,
        JobType.BLACK_SCHOLES: 10,
        JobType.BACKTEST: 45,
    }

    base = base_duration.get(job_type, 30)
    # Add time for data loading and processing
    symbol_factor = min(num_symbols * 2, 60)  # Cap at 60 seconds

    return base + symbol_factor


def _calculate_job_progress(job: Job) -> Optional[float]:
    """Calculate job progress as a float between 0.0 and 1.0."""
    if job.status == "queued":
        return 0.0
    elif job.status == "running":
        if job.started_at and job.created_at:
            # Estimate progress based on time elapsed
            elapsed = (job.started_at - job.created_at).total_seconds()
            estimated_duration = _estimate_job_duration(
                JobType(job.type), len(job.symbols)
            )
            return min(0.9, elapsed / estimated_duration)
        return 0.5
    elif job.status == "completed":
        return 1.0
    elif job.status == "failed":
        return 0.0
    else:
        return None
