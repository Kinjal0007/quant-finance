import numpy as np


def monte_carlo_simulation(
    S0: float, mu: float, sigma: float, T: float, steps: int, n_sims: int
):
    """Geometric Brownian Motion paths (no dividends).

    Returns:
        np.ndarray: shape (steps, n_sims)
    """
    dt = T / steps
    prices = np.zeros((steps + 1, n_sims), dtype=float)
    prices[0] = S0
    for t in range(1, steps + 1):
        z = np.random.normal(0.0, 1.0, size=n_sims)
        growth = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z
        prices[t] = prices[t - 1] * np.exp(growth)
    return prices
