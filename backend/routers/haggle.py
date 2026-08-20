from fastapi import APIRouter
from pydantic import BaseModel
from pricing.engine import calculate_haggle_verdict

router = APIRouter()

class HaggleRequest(BaseModel):
    produce_type: str
    asking_price: float
    fair_price_min: float
    fair_price_max: float

from pricing.phrasebook import generate_bargain_phrases

@router.post("/haggle-check")
def haggle_check(request: HaggleRequest):
    fair_range = {"min": request.fair_price_min, "max": request.fair_price_max}
    result = calculate_haggle_verdict(request.asking_price, fair_range)
    
    phrases, source = generate_bargain_phrases(
        produce_type=request.produce_type,
        verdict=result["verdict"],
        suggested_price=result["suggested_price"]
    )
    
    result["phrases"] = phrases
    result["phrases_source"] = source
    return result
