import base64
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from ml.freshness_model import analyze_produce_with_gemini
from data.agmarknet.service import get_mandi_prices
import asyncio

router = APIRouter()

@router.get("/api/market-price")
async def verify_market_price(
    commodity: str,
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None
):
    """
    Verification endpoint to confirm the government data integration is working.
    """
    result = await get_mandi_prices(
        commodity=commodity,
        state=state,
        district=district,
        market=market
    )
    return result

from data.agmarknet.service import refresh_all_mandi_prices

from fastapi import HTTPException

@router.post("/refresh-prices")
async def refresh_prices_endpoint():
    """
    Manually refreshes all flagship commodities and saves to today's cache file.
    """
    try:
        await refresh_all_mandi_prices()
        return {"status": "success", "message": "Daily prices refreshed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pricing.engine import calculate_fair_price

class ScanRequest(BaseModel):
    produce_type: Optional[str] = None
    image: Optional[str] = None

@router.post("/scan-produce")
async def scan_produce(request: ScanRequest):
    # Default mock values for freshness
    freshness_data = {
        "freshness_label": "Fresh",
        "freshness_percent": 85,
        "freshness_note": "Slight softness detected — good for immediate use",
        "quality_adjustment": -2,
        "quality_adjustment_label": "Slight bruising detected",
    }
    
    produce_type = request.produce_type or "tomato"
    confidence = 0.99
    
    if request.image:
        try:
            # Strip base64 header if present (e.g. data:image/jpeg;base64,...)
            b64_data = request.image
            if "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            
            image_bytes = base64.b64decode(b64_data)
            
            # Analyze completely using Gemini VLM (in a thread since it's blocking)
            detected_type, gemini_freshness = await asyncio.to_thread(analyze_produce_with_gemini, image_bytes)
            produce_type = detected_type
            if detected_type == "unknown":
                confidence = 0.0
            freshness_data.update(gemini_freshness)
            
        except Exception as e:
            print(f"ML Model Error: {e}")
            confidence = 0.0
            pass
            
    from data.agmarknet.service import resolve_wholesale_price
    from pricing.engine import analyze_price_trend
    price_info = await resolve_wholesale_price(commodity=produce_type)
    
    wholesale_price = price_info["wholesale_price"]
    data_date = price_info["data_date"]
    data_confidence = price_info["data_confidence"]
    price_source = price_info["price_source"]
    used_markets = price_info["used_markets"]
    historical_observations = price_info.get("historical_observations", [])
    
    market_context = analyze_price_trend(wholesale_price, historical_observations)
                
    markup_min = 30
    markup_max = 45
    fair_price_range = calculate_fair_price(wholesale_price, markup_min, markup_max, freshness_data.get("quality_adjustment", 0))
    fair_price_range["unit"] = "kg"
                
    return {
        "produce_type": produce_type.capitalize(),
        "detected_produce_id": produce_type.lower(),
        "classification_confidence": confidence,
        **freshness_data,
        "wholesale_price": wholesale_price,
        "markup_range": { "min_pct": markup_min, "max_pct": markup_max },
        "fair_price_range": fair_price_range,
        "data_confidence": data_confidence,
        "price_source": price_source,
        "used_markets": used_markets,
        "location": "Katpadi, Vellore",
        "date": data_date,
        "quickcommerce_price": { "source": "Blinkit", "price": wholesale_price * 1.8, "unit": "kg" },
        "market_context": market_context
    }
