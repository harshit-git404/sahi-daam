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
    purchase_type: str = "street_vendor"
    market_reference: float | None = None
    online_reference_min: float | None = None
    online_reference_max: float | None = None


@router.post("/haggle-check")
def haggle_check(request: HaggleRequest):
    if request.purchase_type != "street_vendor":
        raise HTTPException(status_code=400, detail="Haggling is only available for street-vendor purchases.")
    if request.fair_price_max < request.fair_price_min:
        raise HTTPException(status_code=400, detail="Invalid fair-price range.")
    result = calculate_haggle_verdict(
        request.asking_price,
        {"min": request.fair_price_min, "max": request.fair_price_max},
    )
    result["market_reference"] = request.market_reference
    result["online_reference_min"] = request.online_reference_min
    result["online_reference_max"] = request.online_reference_max
    return result
