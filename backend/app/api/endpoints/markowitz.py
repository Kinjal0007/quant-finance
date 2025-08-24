from fastapi import APIRouter
from pydantic import BaseModel
import numpy as np
from app.services.markowitz import markowitz_optimization

router = APIRouter()

class ReturnsPayload(BaseModel):
    returns: list  # list of lists shape (n_obs, n_assets)

@router.post("/markowitz")
def run_markowitz(payload: ReturnsPayload):
    arr = np.array(payload.returns, dtype=float)
    res = markowitz_optimization(arr)
    return res
