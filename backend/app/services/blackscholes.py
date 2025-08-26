import numpy as np
from scipy.stats import norm


def black_scholes(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
):
    """Black-Scholes price for European call/put (no dividends)."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        raise ValueError("Inputs must be positive and T,sigma > 0")
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type.lower() == "call":
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return float(price)
