import numpy as np

def markowitz_optimization(returns: np.ndarray):
    """Compute global minimum-variance portfolio (long-only weights sum to 1).

    Args:
        returns: shape (n_obs, n_assets) log/arith returns

    Returns:
        dict with weights (list), expected_return, volatility
    """
    mean_returns = np.mean(returns, axis=0)  # (n_assets,)
    cov_matrix = np.cov(returns.T)           # (n_assets, n_assets)
    n = mean_returns.shape[0]

    # Add small ridge to avoid singular matrix
    cov_matrix = cov_matrix + 1e-6 * np.eye(n)
    inv_cov = np.linalg.inv(cov_matrix)
    ones = np.ones(n)

    # Global minimum variance weights: w ∝ Σ^{-1} 1
    w = inv_cov @ ones
    w = w / (ones @ w)

    port_ret = float(w @ mean_returns)
    port_vol = float(np.sqrt(w @ cov_matrix @ w))

    return {
        "weights": w.tolist(),
        "expected_return": port_ret,
        "volatility": port_vol
    }
