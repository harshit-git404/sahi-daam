import base64
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ml.freshness_model import predict_freshness

router = APIRouter()

class ScanRequest(BaseModel):
    produce_type: str
    image: Optional[str] = None

@router.post("/scan-produce")
def scan_produce(request: ScanRequest):
    # Default mock values
    freshness_data = {
        "freshness_label": "Fresh",
        "freshness_percent": 85,
        "freshness_note": "Slight softness detected — good for immediate use",
        "quality_adjustment": -2,
        "quality_adjustment_label": "Slight bruising detected",
    }
    
    if request.image:
        try:
            # Strip base64 header if present (e.g. data:image/jpeg;base64,...)
            b64_data = request.image
            if "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            
            image_bytes = base64.b64decode(b64_data)
            
            # Predict using teammate's ML model
            pred = predict_freshness(image_bytes, request.produce_type)
            freshness_data.update(pred)
        except Exception as e:
            print(f"ML Model Error: {e}")
            pass
            
    return {
        "produce_type": request.produce_type.capitalize(),
        **freshness_data,
        "wholesale_price": 22,
        "markup_range": { "min_pct": 30, "max_pct": 45 },
        "fair_price_range": { "min": 27, "max": 30, "unit": "kg" },
        "data_confidence": "Estimated",
        "location": "Katpadi, Vellore",
        "date": "2026-08-19",
        "quickcommerce_price": { "source": "Blinkit", "price": 38, "unit": "kg" }
    }
