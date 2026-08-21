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
    import json
    from pathlib import Path
    
    quickcommerce_price = { "source": "Blinkit", "price": wholesale_price * 1.8, "unit": "kg" }
    retail_comparison = None
    
    try:
        snapshot_path = Path(__file__).parent.parent / "data" / "quickcommerce_snapshot.json"
        if snapshot_path.exists():
            with open(snapshot_path, "r") as f:
                qc_data = json.load(f)
            
            prod_data = qc_data.get(produce_type.lower())
            if prod_data:
                products = []
                best_price = float('inf')
                best_platform = None
                
                for platform, items in prod_data.items():
                    for item in items:
                        item["platform"] = platform
                        products.append(item)
                        if item.get("price_per_kg", float('inf')) < best_price:
                            best_price = item["price_per_kg"]
                            best_platform = platform
                
                if products:
                    products.sort(key=lambda x: x.get("price_per_kg", 0))
                    
                    latest_collected_at = products[0].get("collected_at", "")
                    cache_age_hours = None
                    if latest_collected_at:
                        from datetime import datetime
                        try:
                            dt_str = latest_collected_at.replace("Z", "+00:00")
                            collected_dt = datetime.fromisoformat(dt_str)
                            now = datetime.now(collected_dt.tzinfo) if collected_dt.tzinfo else datetime.now()
                            age = now - collected_dt
                            cache_age_hours = round(age.total_seconds() / 3600, 1)
                        except (ValueError, TypeError):
                            pass

                    retail_comparison = {
                        "status": "AVAILABLE",
                        "products": products,
                        "best_platform": best_platform,
                        "best_price_per_kg": best_price,
                        "collected_at": latest_collected_at,
                        "cache_age_hours": cache_age_hours,
                        "data_source_type": "cached_snapshot",
                        "source": "Cached retail snapshot from friend's Blinkit/Zepto collector. Not live — refresh by running the offline collector script."
                    }
                    quickcommerce_price = { "source": str(best_platform).capitalize(), "price": best_price, "unit": "kg" }
    except Exception as e:
        print(f"Failed to load quickcommerce snapshot: {e}")
        
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
        "quickcommerce_price": quickcommerce_price,
        "retail_comparison": retail_comparison,
        "market_context": market_context
    }
