from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

try:
    from ..pricing.engine import calculate_haggle_verdict
except ImportError:
    from pricing.engine import calculate_haggle_verdict

router = APIRouter()


class HaggleRequest(BaseModel):
    asking_price: float = Field(gt=0)
    fair_price_min: float = Field(ge=0)
    fair_price_max: float = Field(ge=0)


@router.post("/haggle-check")
def haggle_check(request: HaggleRequest):
    if request.fair_price_max < request.fair_price_min:
        raise HTTPException(status_code=400, detail="Invalid fair-price range.")
    return calculate_haggle_verdict(
        request.asking_price,
        {"min": request.fair_price_min, "max": request.fair_price_max},
    )
