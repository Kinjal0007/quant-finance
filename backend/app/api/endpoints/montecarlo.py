import numpy as np
from fastapi import APIRouter

from app.services.montecarlo import monte_carlo_simulation

router = APIRouter()


@router.get("/montecarlo")
def run_montecarlo(
    S0: float = 100.0,
    mu: float = 0.08,
    sigma: float = 0.2,
    T: float = 1.0,
    steps: int = 252,
    sims: int = 1000,
):
    sims_arr = monte_carlo_simulation(S0, mu, sigma, T, steps, sims)
    # return summary instead of full array to keep payload small
    final = sims_arr[-1]
    return {
        "final_mean": float(final.mean()),
        "final_std": float(final.std()),
        "p5": float(np.percentile(final, 5)),
        "p50": float(np.percentile(final, 50)),
        "p95": float(np.percentile(final, 95)),
    }
