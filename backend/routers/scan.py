from fastapi import APIRouter

router = APIRouter()

@router.post("/scan-produce")
def scan_produce():
    return {
        "produce_type": "Tomato",
        "freshness_label": "Fresh",
        "freshness_note": "Slight softness detected — good for immediate use",
        "wholesale_price": 22,
        "markup_range": { "min_pct": 30, "max_pct": 45 },
        "quality_adjustment": -2,
        "fair_price_range": { "min": 27, "max": 30, "unit": "kg" },
        "data_confidence": "Medium",
        "location": "Katpadi, Vellore",
        "date": "2026-08-19",
        "quickcommerce_price": { "source": "Blinkit", "price": 38, "unit": "kg" }
    }
