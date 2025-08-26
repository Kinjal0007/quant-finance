from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator


class JobType(str, Enum):
    """Supported job types for financial modeling."""

    MONTE_CARLO = "montecarlo"
    MARKOWITZ = "markowitz"
    BLACK_SCHOLES = "blackscholes"
    BACKTEST = "backtest"


class JobStatus(str, Enum):
    """Job execution status."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DataInterval(str, Enum):
    """Supported data intervals."""

    ONE_MIN = "1min"
    FIVE_MIN = "5min"
    FIFTEEN_MIN = "15min"
    THIRTY_MIN = "30min"
    FORTY_FIVE_MIN = "45min"
    ONE_HOUR = "1h"
    TWO_HOUR = "2h"
    FOUR_HOUR = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1week"
    ONE_MONTH = "1month"


class DataVendor(str, Enum):
    """Supported data vendors."""

    EODHD = "eodhd"
    TWELVE_DATA = "twelvedata"


class MonteCarloParams(BaseModel):
    """Monte Carlo simulation parameters."""

    simulations: int = Field(
        10000, ge=1000, le=100000, description="Number of simulations"
    )
    time_steps: int = Field(252, ge=30, le=1000, description="Number of time steps")
    risk_free_rate: float = Field(
        0.02, ge=0.0, le=0.5, description="Risk-free rate (annualized)"
    )
    confidence_level: float = Field(
        0.95, ge=0.8, le=0.99, description="Confidence level for VaR"
    )


class MarkowitzParams(BaseModel):
    """Markowitz portfolio optimization parameters."""

    target_return: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Target portfolio return"
    )
    risk_aversion: float = Field(
        1.0, ge=0.1, le=10.0, description="Risk aversion parameter"
    )
    max_weight: float = Field(
        0.3, ge=0.1, le=1.0, description="Maximum weight per asset"
    )
    min_weight: float = Field(
        0.0, ge=0.0, le=0.1, description="Minimum weight per asset"
    )
    covariance_method: str = Field(
        "ledoit_wolf", description="Covariance estimation method"
    )


class BlackScholesParams(BaseModel):
    """Black-Scholes option pricing parameters."""

    option_type: str = Field(
        ..., pattern="^(call|put)$", description="Option type: call or put"
    )
    strike_price: float = Field(..., gt=0, description="Strike price")
    time_to_expiry: float = Field(
        ..., gt=0, le=10, description="Time to expiry in years"
    )
    risk_free_rate: float = Field(
        0.02, ge=0.0, le=0.5, description="Risk-free rate (annualized)"
    )
    volatility: Optional[float] = Field(
        None, ge=0.01, le=5.0, description="Volatility (annualized)"
    )


class BacktestParams(BaseModel):
    """Backtesting parameters."""

    strategy: str = Field(..., description="Strategy name")
    rebalance_frequency: str = Field("monthly", description="Rebalancing frequency")
    transaction_costs: float = Field(
        0.001, ge=0.0, le=0.1, description="Transaction costs as fraction"
    )
    slippage: float = Field(0.0005, ge=0.0, le=0.01, description="Slippage as fraction")


class CreateJobRequest(BaseModel):
    """Request to create a new job."""

    type: JobType = Field(..., description="Job type")
    symbols: List[str] = Field(
        ..., min_items=1, max_items=100, description="List of symbols to analyze"
    )
    start: str = Field(..., description="Start date in ISO format (YYYY-MM-DD)")
    end: str = Field(..., description="End date in ISO format (YYYY-MM-DD)")
    interval: DataInterval = Field(DataInterval.ONE_DAY, description="Data interval")
    vendor: Optional[DataVendor] = Field(
        DataVendor.EODHD, description="Data vendor preference"
    )
    adjusted: bool = Field(True, description="Use adjusted prices (for equities)")
    params: Union[
        MonteCarloParams,
        MarkowitzParams,
        BlackScholesParams,
        BacktestParams,
        Dict[str, Any],
    ] = Field(..., description="Job-specific parameters")

    @validator("start", "end")
    def validate_dates(cls, v):
        """Validate date format and logic."""
        try:
            date_obj = datetime.strptime(v, "%Y-%m-%d")
            if date_obj > datetime.now():
                raise ValueError("Date cannot be in the future")
            return v
        except ValueError as e:
            if "Date cannot be in the future" in str(e):
                raise e
            raise ValueError("Date must be in YYYY-MM-DD format")

    @validator("end")
    def validate_date_range(cls, v, values):
        """Validate that end date is after start date."""
        if "start" in values and v <= values["start"]:
            raise ValueError("End date must be after start date")
        return v

    @validator("symbols")
    def validate_symbols(cls, v):
        """Validate symbol format and uniqueness."""
        if len(set(v)) != len(v):
            raise ValueError("Symbols must be unique")

        for symbol in v:
            if not symbol or len(symbol) > 20:
                raise ValueError("Symbol must be 1-20 characters")
            if not symbol.replace(".", "").replace("-", "").replace("/", "").isalnum():
                raise ValueError("Symbol contains invalid characters")

        return v

    @validator("params")
    def validate_params_type(cls, v, values):
        """Validate that params match the job type."""
        if "type" not in values:
            return v

        job_type = values["type"]
        if job_type == JobType.MONTE_CARLO and not isinstance(v, MonteCarloParams):
            raise ValueError("Monte Carlo jobs require MonteCarloParams")
        elif job_type == JobType.MARKOWITZ and not isinstance(v, MarkowitzParams):
            raise ValueError("Markowitz jobs require MarkowitzParams")
        elif job_type == JobType.BLACK_SCHOLES and not isinstance(
            v, BlackScholesParams
        ):
            raise ValueError("Black-Scholes jobs require BlackScholesParams")
        elif job_type == JobType.BACKTEST and not isinstance(v, BacktestParams):
            raise ValueError("Backtest jobs require BacktestParams")

        return v


class JobStatusResponse(BaseModel):
    """Job status response."""

    job_id: UUID = Field(..., description="Unique job identifier")
    user_id: UUID = Field(..., description="User who created the job")
    type: JobType = Field(..., description="Job type")
    status: JobStatus = Field(..., description="Current job status")
    symbols: List[str] = Field(..., description="Symbols being analyzed")
    start: str = Field(..., description="Start date")
    end: str = Field(..., description="End date")
    interval: DataInterval = Field(..., description="Data interval")
    vendor: DataVendor = Field(..., description="Data vendor used")
    adjusted: bool = Field(..., description="Whether adjusted prices were used")
    params: Dict[str, Any] = Field(..., description="Job parameters")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    finished_at: Optional[datetime] = Field(
        None, description="Job completion timestamp"
    )
    metrics: Optional[Dict[str, Any]] = Field(None, description="Job results/metrics")
    result_urls: Optional[List[str]] = Field(None, description="Signed URLs to results")
    error: Optional[str] = Field(None, description="Error message if failed")
    progress: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Job progress (0.0 to 1.0)"
    )


class JobListResponse(BaseModel):
    """List of jobs response."""

    jobs: List[JobStatusResponse] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")
    page: int = Field(1, description="Current page number")
    size: int = Field(50, description="Page size")
    has_next: bool = Field(False, description="Whether there are more pages")


class JobCreateResponse(BaseModel):
    """Response when creating a job."""

    job_id: UUID = Field(..., description="Created job identifier")
    status: JobStatus = Field(..., description="Initial job status")
    message: str = Field("Job queued successfully", description="Status message")
    estimated_duration: Optional[int] = Field(
        None, description="Estimated duration in seconds"
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field("ok", description="Service status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Health check timestamp"
    )
    version: str = Field("1.0.0", description="API version")
    database: str = Field("connected", description="Database connection status")
    pubsub: str = Field("connected", description="Pub/Sub connection status")
