from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize

try:
    from sklearn.covariance import LedoitWolf

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. Ledoit-Wolf covariance disabled.")


class MonteCarloGBM:
    """Monte Carlo simulation using Geometric Brownian Motion."""

    def __init__(self, params: Dict[str, Any]):
        self.simulations = params.get("simulations", 10000)
        self.time_steps = params.get("time_steps", 252)
        self.risk_free_rate = params.get("risk_free_rate", 0.02)
        self.confidence_level = params.get("confidence_level", 0.95)

    def simulate(self, returns: pd.Series) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation.

        Args:
            returns: Series of historical returns

        Returns:
            Dictionary with simulation results and metrics
        """
        # Calculate parameters from historical data
        mu = returns.mean()
        sigma = returns.std()

        # Annualize parameters
        mu_annual = mu * 252
        sigma_annual = sigma * np.sqrt(252)

        # Generate random paths
        dt = 1 / self.time_steps
        paths = np.zeros((self.time_steps + 1, self.simulations))
        paths[0] = 1.0  # Start at 1.0

        # Generate random numbers
        np.random.seed(42)  # For reproducibility
        random_numbers = np.random.normal(0, 1, (self.time_steps, self.simulations))

        # Simulate paths
        for t in range(1, self.time_steps + 1):
            drift = (mu_annual - 0.5 * sigma_annual**2) * dt
            diffusion = sigma_annual * np.sqrt(dt) * random_numbers[t - 1]
            paths[t] = paths[t - 1] * np.exp(drift + diffusion)

        # Calculate final values
        final_values = paths[-1]

        # Calculate metrics
        mean_return = np.mean(final_values)
        std_return = np.std(final_values)

        # Calculate percentiles
        p5 = np.percentile(final_values, 5)
        p50 = np.percentile(final_values, 50)
        p95 = np.percentile(final_values, 95)

        # Calculate VaR
        var = np.percentile(final_values, (1 - self.confidence_level) * 100)

        # Calculate Sharpe ratio
        excess_returns = final_values - np.exp(self.risk_free_rate)
        sharpe_ratio = (
            np.mean(excess_returns) / np.std(excess_returns)
            if np.std(excess_returns) > 0
            else 0
        )

        results = {
            "metrics": {
                "mean": float(mean_return),
                "std": float(std_return),
                "p5": float(p5),
                "p50": float(p50),
                "p95": float(p95),
                "var": float(var),
                "sharpe_ratio": float(sharpe_ratio),
                "simulations": self.simulations,
                "time_steps": self.time_steps,
            },
            "paths": paths.tolist(),
            "final_values": final_values.tolist(),
        }

        return results


class MarkowitzOptimizer:
    """Markowitz portfolio optimization."""

    def __init__(self, params: Dict[str, Any]):
        self.target_return = params.get("target_return")
        self.risk_aversion = params.get("risk_aversion", 1.0)
        self.max_weight = params.get("max_weight", 0.3)
        self.min_weight = params.get("min_weight", 0.0)
        self.covariance_method = params.get("covariance_method", "ledoit_wolf")

    def optimize(self, returns: pd.DataFrame) -> Dict[str, Any]:
        """
        Optimize portfolio weights.

        Args:
            returns: DataFrame with returns (timestamps as index, symbols as columns)

        Returns:
            Dictionary with optimization results
        """
        # Calculate expected returns and covariance matrix
        expected_returns = returns.mean() * 252  # Annualize
        cov_matrix = self._calculate_covariance(returns)

        # Number of assets
        n_assets = len(returns.columns)

        # Initial weights (equal weight)
        initial_weights = np.array([1.0 / n_assets] * n_assets)

        # Constraints
        constraints = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1}  # Weights sum to 1
        ]

        if self.target_return is not None:
            constraints.append(
                {
                    "type": "eq",
                    "fun": lambda x: np.sum(expected_returns * x) - self.target_return,
                }
            )

        # Bounds for weights
        bounds = [(self.min_weight, self.max_weight)] * n_assets

        # Objective function: minimize portfolio variance
        def objective(weights):
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_return = np.sum(expected_returns * weights)
            # Add risk aversion penalty
            return portfolio_variance - self.risk_aversion * portfolio_return

        # Optimize
        result = minimize(
            objective,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-8, "maxiter": 1000},
        )

        if not result.success:
            raise RuntimeError(f"Portfolio optimization failed: {result.message}")

        optimal_weights = result.x

        # Calculate portfolio metrics
        portfolio_return = np.sum(expected_returns * optimal_weights)
        portfolio_variance = np.dot(
            optimal_weights.T, np.dot(cov_matrix, optimal_weights)
        )
        portfolio_volatility = np.sqrt(portfolio_variance)

        # Calculate Sharpe ratio
        risk_free_rate = 0.02  # Assume 2% risk-free rate
        sharpe_ratio = (
            (portfolio_return - risk_free_rate) / portfolio_volatility
            if portfolio_volatility > 0
            else 0
        )

        # Create weights DataFrame
        weights_df = pd.DataFrame(
            {"symbol": returns.columns, "weight": optimal_weights}
        ).sort_values("weight", ascending=False)

        results = {
            "metrics": {
                "portfolio_return": float(portfolio_return),
                "portfolio_volatility": float(portfolio_volatility),
                "portfolio_variance": float(portfolio_variance),
                "sharpe_ratio": float(sharpe_ratio),
                "risk_aversion": self.risk_aversion,
            },
            "weights": weights_df.to_dict("records"),
            "covariance_matrix": cov_matrix.tolist(),
            "expected_returns": expected_returns.to_dict(),
        }

        return results

    def _calculate_covariance(self, returns: pd.DataFrame) -> np.ndarray:
        """Calculate covariance matrix using specified method."""
        if self.covariance_method == "ledoit_wolf" and SKLEARN_AVAILABLE:
            # Use Ledoit-Wolf shrinkage estimator
            lw = LedoitWolf()
            lw.fit(returns)
            return lw.covariance_
        else:
            # Use sample covariance
            return returns.cov().values * 252  # Annualize


class BlackScholesPricer:
    """Black-Scholes option pricing model."""

    def __init__(self, params: Dict[str, Any]):
        self.option_type = params.get("option_type", "call")
        self.strike_price = params.get("strike_price")
        self.time_to_expiry = params.get("time_to_expiry")
        self.risk_free_rate = params.get("risk_free_rate", 0.02)
        self.volatility = params.get("volatility")

    def price_option(
        self, current_price: float, volatility: float = None
    ) -> Dict[str, Any]:
        """
        Price option using Black-Scholes model.

        Args:
            current_price: Current price of underlying asset
            volatility: Volatility (if not provided in params)

        Returns:
            Dictionary with option price and Greeks
        """
        if volatility is None:
            volatility = self.volatility

        if volatility is None:
            raise ValueError("Volatility must be provided")

        # Calculate option price and Greeks
        price, delta, gamma, theta, vega, rho = self._black_scholes(
            current_price,
            self.strike_price,
            self.time_to_expiry,
            self.risk_free_rate,
            volatility,
        )

        results = {
            "metrics": {
                "option_price": float(price),
                "delta": float(delta),
                "gamma": float(gamma),
                "theta": float(theta),
                "vega": float(vega),
                "rho": float(rho),
            },
            "parameters": {
                "current_price": float(current_price),
                "strike_price": float(self.strike_price),
                "time_to_expiry": float(self.time_to_expiry),
                "risk_free_rate": float(self.risk_free_rate),
                "volatility": float(volatility),
                "option_type": self.option_type,
            },
        }

        return results

    def _black_scholes(
        self, S: float, K: float, T: float, r: float, sigma: float
    ) -> Tuple[float, float, float, float, float, float]:
        """
        Calculate Black-Scholes option price and Greeks.

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiry (years)
            r: Risk-free rate
            sigma: Volatility

        Returns:
            Tuple of (price, delta, gamma, theta, vega, rho)
        """
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if self.option_type == "call":
            price = S * stats.norm.cdf(d1) - K * np.exp(-r * T) * stats.norm.cdf(d2)
            delta = stats.norm.cdf(d1)
        else:  # put
            price = K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * stats.norm.cdf(-d1)
            delta = stats.norm.cdf(d1) - 1

        # Greeks
        gamma = stats.norm.pdf(d1) / (S * sigma * np.sqrt(T))

        if self.option_type == "call":
            theta = -S * stats.norm.pdf(d1) * sigma / (2 * np.sqrt(T)) - r * K * np.exp(
                -r * T
            ) * stats.norm.cdf(d2)
        else:  # put
            theta = -S * stats.norm.pdf(d1) * sigma / (2 * np.sqrt(T)) + r * K * np.exp(
                -r * T
            ) * stats.norm.cdf(-d2)

        vega = S * np.sqrt(T) * stats.norm.pdf(d1)

        if self.option_type == "call":
            rho = K * T * np.exp(-r * T) * stats.norm.cdf(d2)
        else:  # put
            rho = -K * T * np.exp(-r * T) * stats.norm.cdf(-d2)

        return price, delta, gamma, theta, vega, rho


class BacktestEngine:
    """Backtesting engine for trading strategies."""

    def __init__(self, params: Dict[str, Any]):
        self.strategy = params.get("strategy", "buy_and_hold")
        self.rebalance_frequency = params.get("rebalance_frequency", "monthly")
        self.transaction_costs = params.get("transaction_costs", 0.001)
        self.slippage = params.get("slippage", 0.0005)

    def run_backtest(
        self, prices: pd.DataFrame, weights: List[float] = None
    ) -> Dict[str, Any]:
        """
        Run backtest simulation.

        Args:
            prices: DataFrame with prices (timestamps as index, symbols as columns)
            weights: Initial portfolio weights (if None, equal weight)

        Returns:
            Dictionary with backtest results
        """
        if weights is None:
            # Equal weight portfolio
            weights = np.array([1.0 / len(prices.columns)] * len(prices.columns))

        # Calculate returns
        returns = prices.pct_change().dropna()

        # Initialize portfolio
        portfolio_values = []
        portfolio_weights = [weights.copy()]

        # Initial portfolio value
        initial_value = 1.0
        current_value = initial_value

        # Rebalancing dates
        if self.rebalance_frequency == "monthly":
            rebalance_dates = returns.resample("M").last().index
        elif self.rebalance_frequency == "weekly":
            rebalance_dates = returns.resample("W").last().index
        else:
            rebalance_dates = returns.index

        # Run backtest
        for i, date in enumerate(returns.index):
            # Calculate daily returns
            daily_returns = returns.loc[date]

            # Update portfolio value
            current_value *= 1 + np.sum(weights * daily_returns)
            portfolio_values.append(current_value)

            # Rebalance if needed
            if date in rebalance_dates:
                # Apply transaction costs
                current_value *= 1 - self.transaction_costs

                # Update weights (for now, keep same weights)
                # In a real implementation, this would update based on strategy
                portfolio_weights.append(weights.copy())

        # Calculate metrics
        total_return = (current_value - initial_value) / initial_value
        annualized_return = (1 + total_return) ** (252 / len(returns)) - 1

        # Calculate volatility
        portfolio_returns = pd.Series(portfolio_values).pct_change().dropna()
        volatility = portfolio_returns.std() * np.sqrt(252)

        # Calculate Sharpe ratio
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0

        # Calculate maximum drawdown
        cumulative_values = pd.Series(portfolio_values)
        running_max = cumulative_values.expanding().max()
        drawdown = (cumulative_values - running_max) / running_max
        max_drawdown = drawdown.min()

        results = {
            "metrics": {
                "total_return": float(total_return),
                "annualized_return": float(annualized_return),
                "volatility": float(volatility),
                "sharpe_ratio": float(sharpe_ratio),
                "max_drawdown": float(max_drawdown),
                "final_value": float(current_value),
            },
            "portfolio_values": portfolio_values,
            "rebalance_dates": [str(d) for d in rebalance_dates],
            "strategy": self.strategy,
        }

        return results


def run_model(
    model_type: str, params: Dict[str, Any], data: pd.DataFrame = None
) -> Dict[str, Any]:
    """
    Run financial model based on type.

    Args:
        model_type: Type of model to run
        params: Model parameters
        data: Input data (if required)

    Returns:
        Model results
    """
    # Check if fixture mode is enabled
    try:
        from .demo_loader import generate_fixture_metrics, should_use_fixture

        if should_use_fixture():
            print(f"Using fixture mode for {model_type} model")
            # Extract symbols from params if available
            symbols = params.get("symbols", ["AAPL"])
            return generate_fixture_metrics(model_type, symbols, params)
    except ImportError:
        pass  # Fixture mode not available, continue with normal execution

    if model_type == "montecarlo":
        if data is None:
            raise ValueError("Data required for Monte Carlo simulation")
        returns = data.pct_change().dropna().iloc[:, 0]  # Use first column
        model = MonteCarloGBM(params)
        return model.simulate(returns)

    elif model_type == "markowitz":
        if data is None:
            raise ValueError("Data required for Markowitz optimization")
        model = MarkowitzOptimizer(params)
        return model.optimize(data)

    elif model_type == "blackscholes":
        model = BlackScholesPricer(params)
        # For Black-Scholes, we need a current price
        current_price = params.get("current_price", 100.0)
        volatility = params.get("volatility", 0.2)
        return model.price_option(current_price, volatility)

    elif model_type == "backtest":
        if data is None:
            raise ValueError("Data required for backtesting")
        model = BacktestEngine(params)
        return model.run_backtest(data)

    else:
        raise ValueError(f"Unknown model type: {model_type}")
