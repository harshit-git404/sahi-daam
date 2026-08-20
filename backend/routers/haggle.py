from fastapi import APIRouter
from pydantic import BaseModel
from pricing.engine import calculate_haggle_verdict

router = APIRouter()

class HaggleRequest(BaseModel):
    asking_price: float
    fair_price_min: float
    fair_price_max: float

@router.post("/haggle-check")
def haggle_check(request: HaggleRequest):
    fair_range = {"min": request.fair_price_min, "max": request.fair_price_max}
    return calculate_haggle_verdict(request.asking_price, fair_range)
