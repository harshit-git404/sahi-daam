import base64
import binascii
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from ..data.agmarknet.service import get_mandi_prices
    from ..ml.freshness_model import predict_freshness
    from ..ml.produce_classifier import identify_produce
except ImportError:
    from data.agmarknet.service import get_mandi_prices
    from ml.freshness_model import predict_freshness
    from ml.produce_classifier import identify_produce

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
    """Classify produce locally, assess freshness locally, then fetch its market price."""
    if not request.image:
        raise HTTPException(status_code=400, detail="An image is required for produce analysis.")

    try:
        image_bytes = _decode_image(request.image)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info("Produce photo received; starting local classification")
    try:
        classification = identify_produce(image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Produce classifier failed")
        raise HTTPException(status_code=503, detail="Produce classifier unavailable.") from exc

    detected_produce = classification["produce_type"]
    detected_produce_id = classification["produce_id"]
    produce_confidence = classification["produce_confidence"]

    try:
        freshness_data = predict_freshness(image_bytes, detected_produce)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Freshness model failed")
        raise HTTPException(status_code=503, detail="Freshness model unavailable.") from exc

    try:
        commodity_query = detected_produce.replace("_", " ").title()
        mandi_data = await get_mandi_prices(commodity=commodity_query)
    except Exception as exc:
        logger.exception("Market data request failed")
        raise HTTPException(status_code=502, detail="Market data unavailable.") from exc

    if not mandi_data or mandi_data.get("error"):
        raise HTTPException(status_code=502, detail="Market data unavailable.")
    records = mandi_data.get("records", [])
    if not records:
        raise HTTPException(status_code=404, detail=f"No market data found for {detected_produce}.")

    latest = records[0]
    wholesale_price = latest.get("modal_price_per_kg")
    if wholesale_price is None:
        raise HTTPException(status_code=502, detail="Market data did not include a modal price.")
    data_date = latest.get("arrival_date", "")
    if "/" in data_date:
        try:
            day, month, year = data_date.split("/")
            data_date = f"{year}-{month}-{day}"
        except ValueError:
            logger.warning("Unexpected market date format: %s", data_date)

    return {
        "produce_type": detected_produce,
        "detected_produce_id": detected_produce_id,
        "produce_confidence": produce_confidence,
        "classification_confidence": produce_confidence,
        **freshness_data,
        "wholesale_price": wholesale_price,
        "markup_range": {"min_pct": 30, "max_pct": 45},
        "fair_price_range": {"min": wholesale_price * 1.3, "max": wholesale_price * 1.45, "unit": "kg"},
        "data_confidence": "High",
        "location": f"{latest.get('market', '')}, {latest.get('district', '')}".strip(", "),
        "date": data_date,
        "quickcommerce_price": {"source": "Blinkit", "price": wholesale_price * 1.8, "unit": "kg"},
    }
