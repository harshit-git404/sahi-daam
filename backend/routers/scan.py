from fastapi import APIRouter, Query
from typing import Optional
import os
from data.agmarknet.service import get_mandi_prices

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

@router.post("/scan-produce")
async def scan_produce():
    # Hardcoded to Tomato for now, as in the original mock
    produce_type = "Tomato"
    
    # Fetch real wholesale data
    mandi_data = await get_mandi_prices(commodity=produce_type)
    records = mandi_data.get("records", [])
    
    wholesale_price = 22.0 # fallback
    data_date = "2026-08-19" # fallback
    
    if records:
        latest = records[0]
        # Use modal price as the main wholesale benchmark
        wholesale_price = latest.get("modal_price_per_kg", wholesale_price)
        data_date = latest.get("arrival_date", data_date)
        
        # Format date from DD/MM/YYYY to YYYY-MM-DD if needed, but we'll stick to original formatting or the one from API
        if "/" in data_date:
            try:
                d, m, y = data_date.split("/")
                data_date = f"{y}-{m}-{d}"
            except ValueError:
                pass
                
    return {
        "produce_type": produce_type,
        "freshness_label": "Fresh",
        "freshness_percent": 85,
        "freshness_note": "Slight softness detected — good for immediate use",
        "wholesale_price": wholesale_price,
        "markup_range": { "min_pct": 30, "max_pct": 45 },
        "quality_adjustment": -2,
        "quality_adjustment_label": "Slight bruising detected",
        "fair_price_range": { "min": 27, "max": 30, "unit": "kg" },
        "data_confidence": "Estimated" if not records else "High",
        "location": "Katpadi, Vellore",
        "date": data_date,
        "quickcommerce_price": { "source": "Blinkit", "price": 38, "unit": "kg" }
    }
