from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pricing.engine import analyze_purchase_decision
from pricing.phrasebook import generate_bargain_phrases

router = APIRouter()

class HaggleRequest(BaseModel):
    produce_type: str
    asking_price: float
    fair_price_min: float
    fair_price_max: float
    freshness_label: Optional[str] = None
    quickcommerce_price: Optional[Dict[str, Any]] = None

@router.post("/haggle-check")
def haggle_check(request: HaggleRequest):
    result = analyze_purchase_decision(
        request.fair_price_min,
        request.fair_price_max,
        request.asking_price,
        request.freshness_label,
        request.quickcommerce_price
    )
    
    phrases, source = generate_bargain_phrases(
        produce_type=request.produce_type,
        verdict=result["verdict"],
        suggested_price=result["suggested_price"],
        decision=result["decision"],
    )
    
    result["phrases"] = phrases
    result["phrases_source"] = source
    return result
