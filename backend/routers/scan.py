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
            freshness_data.update(gemini_freshness)
            
        except Exception as e:
            print(f"ML Model Error: {e}")
            pass
            
    # Fetch real wholesale data based on detected produce_type
    mandi_data = await get_mandi_prices(commodity=produce_type)
    records = mandi_data.get("records", [])
    
    wholesale_price = 22.0 # fallback
    data_date = "2026-08-19" # fallback
    
    if records:
        latest = records[0]
        # Use modal price as the main wholesale benchmark
        wholesale_price = latest.get("modal_price_per_kg", wholesale_price)
        data_date = latest.get("arrival_date", data_date)
        
        # Format date from DD/MM/YYYY to YYYY-MM-DD
        if "/" in data_date:
            try:
                d, m, y = data_date.split("/")
                data_date = f"{y}-{m}-{d}"
            except ValueError:
                pass
                
    return {
        "produce_type": produce_type.capitalize(),
        "detected_produce_id": produce_type.lower(),
        "classification_confidence": confidence,
        **freshness_data,
        "wholesale_price": wholesale_price,
        "markup_range": { "min_pct": 30, "max_pct": 45 },
        "fair_price_range": { "min": wholesale_price * 1.3, "max": wholesale_price * 1.45, "unit": "kg" },
        "data_confidence": "Estimated" if not records else "High",
        "location": "Katpadi, Vellore",
        "date": data_date,
        "quickcommerce_price": { "source": "Blinkit", "price": wholesale_price * 1.8, "unit": "kg" }
    }
