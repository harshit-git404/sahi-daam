from fastapi import APIRouter

from pydantic import BaseModel

router = APIRouter()

class HaggleRequest(BaseModel):
    asking_price: float

@router.post("/haggle-check")
def haggle_check(request: HaggleRequest):
    return {
        "verdict": "Overpriced",
        "deviation_pct": 32,
        "suggested_price": 30,
        "reasoning": "Vendor's asking price is significantly above today's fair range for this quality of tomato."
    }
