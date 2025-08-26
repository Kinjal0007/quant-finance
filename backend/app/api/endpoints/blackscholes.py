from fastapi import APIRouter

from app.services.blackscholes import black_scholes

router = APIRouter()


@router.get("/blackscholes")
def run_bs(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
):
    price = black_scholes(S, K, T, r, sigma, option_type)
    return {"price": price}
