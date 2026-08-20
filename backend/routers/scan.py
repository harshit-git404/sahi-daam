import base64
import binascii
import logging
from typing import Optional
import asyncio

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from ..data.agmarknet.service import get_mandi_prices
    from ..ml.freshness_model import predict_freshness
    from ..ml.produce_classifier import identify_produce
    from ..ml.gemini_analysis import analyze_with_gemini, GeminiUnavailable
    from ..pricing.engine import calculate_fair_price
except ImportError:
    from data.agmarknet.service import get_mandi_prices
    from ml.freshness_model import predict_freshness
    from ml.produce_classifier import identify_produce
    from ml.gemini_analysis import analyze_with_gemini, GeminiUnavailable
    from pricing.engine import calculate_fair_price

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/market-price")
async def verify_market_price(
    commodity: str,
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
):
    """Verify the existing Agmarknet integration."""
    return await get_mandi_prices(commodity, state, district, market)


class ScanRequest(BaseModel):
    produce_type: str | None = Field(default=None, min_length=1)
    image: str | None = None
    state: str | None = None
    district: str | None = None
    market: str | None = None
    purchase_type: str = "street_vendor"


def _decode_image(image_data: str) -> bytes:
    encoded_image = image_data.strip()
    if encoded_image.startswith("data:"):
        try:
            header, encoded_image = encoded_image.split(",", 1)
        except ValueError as exc:
            raise ValueError("Invalid image data URL.") from exc
        if ";base64" not in header.lower():
            raise ValueError("Image data URL must contain Base64 data.")

    try:
        image_bytes = base64.b64decode(encoded_image, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid Base64 image data.") from exc
    if not image_bytes:
        raise ValueError("Image data is empty.")
    return image_bytes


@router.post("/scan-produce")
async def scan_produce(request: ScanRequest):
    """Use Gemini first, local models second, and keep market failures separate."""
    if not request.image:
        raise HTTPException(status_code=400, detail="An image is required for produce analysis.")

    try:
        image_bytes = _decode_image(request.image)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    analysis_provider = "gemini"
    try:
        analysis = await asyncio.to_thread(analyze_with_gemini, image_bytes)
        detected_produce = str(analysis["produce_type"]).strip()
        detected_produce_id = detected_produce.lower().replace(" ", "_")
        produce_confidence = float(analysis["produce_confidence"])
        freshness_data = {
            key: analysis[key]
            for key in ("freshness_label", "freshness_percent", "freshness_note", "quality_adjustment", "quality_adjustment_label")
            if key in analysis
        }
    except GeminiUnavailable:
        analysis_provider = "local_fallback"
        logger.info("Using local ML fallback for produce analysis")
        try:
            classification = identify_produce(image_bytes)
            detected_produce = classification["produce_type"]
            detected_produce_id = classification["produce_id"]
            produce_confidence = classification["produce_confidence"]
            freshness_data = predict_freshness(image_bytes, detected_produce)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            logger.exception("Local ML fallback failed")
            raise HTTPException(status_code=503, detail="Both Gemini and local produce analysis are unavailable.") from exc

    try:
        commodity_query = detected_produce.replace("_", " ").title()
        mandi_data = await get_mandi_prices(
            commodity=commodity_query,
            state=request.state,
            district=request.district,
            market=request.market,
        )
    except Exception as exc:
        logger.exception("Market data request failed")
        mandi_data = {"error": "MARKET_UNAVAILABLE", "records": []}

    records = mandi_data.get("records", [])
    latest = records[0] if records else {}
    wholesale_price = latest.get("modal_price_per_kg") if latest else None
    market_status = "AVAILABLE" if wholesale_price is not None else "UNAVAILABLE"
    data_date = latest.get("arrival_date", "") if latest else ""
    if "/" in data_date:
        try:
            day, month, year = data_date.split("/")
            data_date = f"{year}-{month}-{day}"
        except ValueError:
            logger.warning("Unexpected market date format: %s", data_date)

    markup_min = 30
    markup_max = 45
    pricing = calculate_fair_price(
        wholesale_price, markup_min, markup_max, int(freshness_data.get("quality_adjustment", 0))
    ) if wholesale_price is not None else None

    return {
        "produce_type": detected_produce,
        "detected_produce_id": detected_produce_id,
        "produce_confidence": produce_confidence,
        "classification_confidence": produce_confidence,
        "analysis_provider": analysis_provider,
        **freshness_data,
        "market_status": market_status,
        "wholesale_price": wholesale_price,
        "markup_range": {"min_pct": markup_min, "max_pct": markup_max},
        "fair_price_range": {**pricing, "unit": "kg"} if pricing else None,
        "data_confidence": "High" if market_status == "AVAILABLE" else "Unavailable",
        "location": f"{latest.get('market', '')}, {latest.get('district', '')}".strip(", ") if latest else None,
        "date": data_date,
        "market": {
            "status": market_status,
            "today_price": wholesale_price,
            "unit": "kg",
            "history": records,
        },
        "pricing": {
            "fair_price_min": pricing["min"],
            "fair_price_max": pricing["max"],
        } if pricing else None,
        "quickcommerce_price": None,
    }
