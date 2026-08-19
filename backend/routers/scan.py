import base64
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ml.freshness_model import analyze_produce_with_gemini

router = APIRouter()

class ScanRequest(BaseModel):
    produce_type: Optional[str] = None
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
    
    produce_type = request.produce_type or "tomato"
    confidence = 0.99
    
    if request.image:
        try:
            # Strip base64 header if present (e.g. data:image/jpeg;base64,...)
            b64_data = request.image
            if "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            
            image_bytes = base64.b64decode(b64_data)
            
            # Analyze completely using Gemini VLM
            detected_type, gemini_freshness = analyze_produce_with_gemini(image_bytes)
            produce_type = detected_type
            freshness_data.update(gemini_freshness)
            
        except Exception as e:
            print(f"ML Model Error: {e}")
            pass
            
    return {
        "produce_type": produce_type.capitalize(),
        "detected_produce_id": produce_type,
        "classification_confidence": confidence,
        **freshness_data,
        "wholesale_price": 22,
        "markup_range": { "min_pct": 30, "max_pct": 45 },
        "fair_price_range": { "min": 27, "max": 30, "unit": "kg" },
        "data_confidence": "Estimated",
        "location": "Katpadi, Vellore",
        "date": "2026-08-19",
        "quickcommerce_price": { "source": "Blinkit", "price": 38, "unit": "kg" }
    }
