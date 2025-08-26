"""
Demo data loader for local development without vendor API keys.

This module provides fixture price data when USE_FIXTURE=true,
allowing the application to run fully functional demos.
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


def should_use_fixture() -> bool:
    """Check if fixture mode is enabled."""
    return os.getenv("USE_FIXTURE", "false").lower() == "true"


def load_fixture_prices(
    symbols: List[str],
    start_date: str,
    end_date: str,
    interval: str = "1d",
    adjusted: bool = True,
) -> pd.DataFrame:
    """
    Load fixture price data from CSV file.

    Args:
        symbols: List of stock symbols
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        interval: Data interval (1d, 1h, 1min)
        adjusted: Whether to use adjusted prices

    Returns:
        DataFrame with OHLCV data in wide format
    """
    if not should_use_fixture():
        raise ValueError("Fixture mode not enabled. Set USE_FIXTURE=true")

    # Load the fixture CSV
    fixture_path = os.path.join(
        os.path.dirname(__file__), "fixtures", "prices_demo.csv"
    )

    if not os.path.exists(fixture_path):
        raise FileNotFoundError(f"Fixture file not found: {fixture_path}")

    # Read CSV and filter by symbols
    df = pd.read_csv(fixture_path)
    df["date"] = pd.to_datetime(df["date"])

    # Filter by date range
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]

    # Filter by symbols
    df = df[df["symbol"].isin(symbols)]

    if df.empty:
        raise ValueError(
            f"No data found for symbols {symbols} in date range "
            f"{start_date} to {end_date}"
        )

    # Convert to wide format (one column per symbol)
    wide_df = df.pivot(
        index="date", columns="symbol", values="adjusted_close" if adjusted else "close"
    )

    # Sort by date
    wide_df = wide_df.sort_index()

    # Forward fill any missing values
    wide_df = wide_df.fillna(method="ffill")

    return wide_df


def get_fixture_symbols() -> List[str]:
    """Get list of available symbols in fixture data."""
    fixture_path = os.path.join(
        os.path.dirname(__file__), "fixtures", "prices_demo.csv"
    )

    if not os.path.exists(fixture_path):
        return []

    df = pd.read_csv(fixture_path)
    return sorted(df["symbol"].unique().tolist())


def generate_fixture_metrics(
    job_type: str, symbols: List[str], params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate realistic fixture metrics for different job types.

    Args:
        job_type: Type of financial model
        symbols: List of symbols used
        params: Model parameters

    Returns:
        Dictionary with metrics and result data
    """
    if not should_use_fixture():
        raise ValueError("Fixture mode not enabled. Set USE_FIXTURE=true")

    # Load fixture data for calculations
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    try:
        prices_df = load_fixture_prices(symbols, start_date, end_date)
    except Exception:
        # Fallback to mock data if fixture loading fails
        prices_df = None

    if job_type == "montecarlo":
        return _generate_monte_carlo_metrics(symbols, params, prices_df)
    elif job_type == "markowitz":
        return _generate_markowitz_metrics(symbols, params, prices_df)
    elif job_type == "blackscholes":
        return _generate_black_scholes_metrics(symbols, params, prices_df)
    else:
        return {"error": f"Unknown job type: {job_type}"}


def _generate_monte_carlo_metrics(
    symbols: List[str], params: Dict[str, Any], prices_df: Optional[pd.DataFrame]
) -> Dict[str, Any]:
    """Generate Monte Carlo simulation metrics."""
    num_simulations = params.get("simulations", 1000)
    time_steps = params.get("time_steps", 252)

    # Generate realistic simulation results
    np.random.seed(42)  # For reproducible results

    # Simulate returns
    returns = np.random.normal(0.0008, 0.02, (num_simulations, time_steps))
    cumulative_returns = np.cumprod(1 + returns, axis=1)

    # Calculate metrics
    final_returns = cumulative_returns[:, -1] - 1
    mean_return = np.mean(final_returns)
    std_return = np.std(final_returns)

    # Percentiles
    percentiles = {
        "p5": np.percentile(final_returns, 5),
        "p25": np.percentile(final_returns, 25),
        "p50": np.percentile(final_returns, 50),
        "p75": np.percentile(final_returns, 75),
        "p95": np.percentile(final_returns, 95),
    }

    return {
        "num_simulations": num_simulations,
        "time_steps": time_steps,
        "mean_return": float(mean_return),
        "std_return": float(std_return),
        "percentiles": percentiles,
        "simulation_paths": cumulative_returns.tolist()[
            :10
        ],  # First 10 paths for visualization
    }


def _generate_markowitz_metrics(
    symbols: List[str], params: Dict[str, Any], prices_df: Optional[pd.DataFrame]
) -> Dict[str, Any]:
    """Generate Markowitz portfolio optimization metrics."""
    # Generate realistic portfolio metrics
    np.random.seed(42)

    # Simulate returns for each symbol
    n_symbols = len(symbols)
    returns = np.random.normal(0.001, 0.02, (n_symbols, 252))

    # Calculate portfolio statistics
    portfolio_returns = np.mean(returns, axis=1)
    portfolio_cov = np.cov(returns)

    # Generate optimal weights (simplified)
    weights = np.random.dirichlet(np.ones(n_symbols))
    weights = weights / np.sum(weights)

    # Calculate portfolio metrics
    expected_return = float(np.sum(portfolio_returns * weights))
    volatility = float(np.sqrt(weights.T @ portfolio_cov @ weights))
    sharpe_ratio = expected_return / volatility if volatility > 0 else 0

    return {
        "expected_return": expected_return,
        "volatility": volatility,
        "sharpe_ratio": sharpe_ratio,
        "weights": dict(zip(symbols, weights.tolist())),
        "covariance_matrix": portfolio_cov.tolist(),
    }


def _generate_black_scholes_metrics(
    symbols: List[str], params: Dict[str, Any], prices_df: Optional[pd.DataFrame]
) -> Dict[str, Any]:
    """Generate Black-Scholes option pricing metrics."""
    option_type = params.get("option_type", "call")
    strike_price = params.get("strike_price", 150.0)
    time_to_expiry = params.get("time_to_expiry", 1.0)

    # Get current price from first symbol (assuming it's the underlying)
    if prices_df is not None and len(symbols) > 0:
        current_price = prices_df[symbols[0]].iloc[-1]
    else:
        current_price = 150.0  # Fallback price

    # Simplified Black-Scholes calculation
    # In a real implementation, this would use proper BS formula
    moneyness = current_price / strike_price
    volatility = 0.25  # 25% annual volatility

    if option_type == "call":
        option_price = (
            max(current_price - strike_price, 0) + volatility * time_to_expiry * 0.4
        )
        delta = 0.6 if moneyness > 1 else 0.4
    else:  # put
        option_price = (
            max(strike_price - current_price, 0) + volatility * time_to_expiry * 0.4
        )
        delta = -0.4 if moneyness < 1 else -0.6

    # Greeks
    gamma = 0.02
    theta = -option_price * 0.1
    vega = option_price * 0.4
    rho = option_price * 0.1

    return {
        "option_price": float(option_price),
        "current_price": float(current_price),
        "strike_price": float(strike_price),
        "time_to_expiry": float(time_to_expiry),
        "delta": float(delta),
        "greeks": {
            "gamma": float(gamma),
            "theta": float(theta),
            "vega": float(vega),
            "rho": float(rho),
        },
    }


def create_fixture_artifacts(
    job_type: str, symbols: List[str], params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create fixture artifacts (CSV files, charts) for job results.

    Args:
        job_type: Type of financial model
        symbols: List of symbols used
        params: Model parameters

    Returns:
        Dictionary with artifact references
    """
    if not should_use_fixture():
        raise ValueError("Fixture mode not enabled. Set USE_FIXTURE=true")

    # Generate metrics
    metrics = generate_fixture_metrics(job_type, symbols, params)

    # Create mock artifact references
    artifacts = {
        "metrics": metrics,
        "charts": {
            "price_chart": f"fixture_charts/{job_type}_prices.png",
            "results_chart": f"fixture_charts/{job_type}_results.png",
        },
        "data": {
            "raw_data": f"fixture_data/{job_type}_raw.csv",
            "processed_data": f"fixture_data/{job_type}_processed.csv",
        },
    }

    return artifacts
