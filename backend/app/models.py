from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class Job(Base):
    """Job model for storing async job information."""
    
    __tablename__ = "jobs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User identification (for future multi-user support)
    user_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    
    # Job metadata
    type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="queued", index=True)
    
    # Job parameters
    params_json = Column(JSON, nullable=False)
    symbols = Column(JSON, nullable=False)  # List of symbols
    
    # Data parameters
    start_ts = Column(DateTime(timezone=True), nullable=False)
    end_ts = Column(DateTime(timezone=True), nullable=False)
    interval = Column(String(20), nullable=False)
    vendor = Column(String(20), nullable=False)
    adjusted = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    
    # Results
    result_refs = Column(JSON, nullable=True)  # GCS object references
    error = Column(Text, nullable=True)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_jobs_user_created', 'user_id', 'created_at'),
        Index('idx_jobs_status_created', 'status', 'created_at'),
        Index('idx_jobs_type_status', 'type', 'status'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'type': self.type,
            'status': self.status,
            'params_json': self.params_json,
            'symbols': self.symbols,
            'start_ts': self.start_ts.isoformat() if self.start_ts else None,
            'end_ts': self.end_ts.isoformat() if self.end_ts else None,
            'interval': self.interval,
            'vendor': self.vendor,
            'adjusted': self.adjusted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'result_refs': self.result_refs,
            'error': self.error,
        }
    
    @classmethod
    def create_job(
        cls,
        db: Session,
        user_id: uuid.UUID,
        job_type: str,
        symbols: List[str],
        start_date: str,
        end_date: str,
        interval: str,
        vendor: str,
        adjusted: bool,
        params: Dict[str, Any]
    ) -> Job:
        """Create a new job."""
        # Parse dates
        start_ts = datetime.strptime(start_date, "%Y-%m-%d")
        end_ts = datetime.strptime(end_date, "%Y-%m-%d")
        
        job = cls(
            user_id=user_id,
            type=job_type,
            status="queued",
            params_json=params,
            symbols=symbols,
            start_ts=start_ts,
            end_ts=end_ts,
            interval=interval,
            vendor=vendor,
            adjusted=adjusted,
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        return job
    
    @classmethod
    def get_job(cls, db: Session, job_id: uuid.UUID) -> Optional[Job]:
        """Get job by ID."""
        return db.query(cls).filter(cls.id == job_id).first()
    
    @classmethod
    def get_user_jobs(
        cls,
        db: Session,
        user_id: uuid.UUID,
        page: int = 1,
        size: int = 50
    ) -> tuple[List[Job], int]:
        """Get paginated jobs for a user."""
        offset = (page - 1) * size
        
        jobs = db.query(cls).filter(
            cls.user_id == user_id
        ).order_by(
            cls.created_at.desc()
        ).offset(offset).limit(size).all()
        
        total = db.query(cls).filter(cls.user_id == user_id).count()
        
        return jobs, total
    
    @classmethod
    def get_pending_jobs(cls, db: Session, limit: int = 10) -> List[Job]:
        """Get jobs that are queued or running."""
        return db.query(cls).filter(
            cls.status.in_(["queued", "running"])
        ).order_by(
            cls.created_at.asc()
        ).limit(limit).all()
    
    def update_status(self, db: Session, status: str, **kwargs) -> None:
        """Update job status and optional fields."""
        self.status = status
        
        if status == "running" and not self.started_at:
            self.started_at = datetime.utcnow()
        elif status in ["completed", "failed"] and not self.finished_at:
            self.finished_at = datetime.utcnow()
        
        # Update other fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        db.commit()
    
    def set_error(self, db: Session, error: str) -> None:
        """Set job error and mark as failed."""
        self.error = error
        self.update_status(db, "failed")
    
    def set_results(self, db: Session, result_refs: Dict[str, Any]) -> None:
        """Set job results and mark as completed."""
        self.result_refs = result_refs
        self.update_status(db, "completed")


class User(Base):
    """User model for future authentication."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': str(self.id),
            'email': self.email,
            'name': self.name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
