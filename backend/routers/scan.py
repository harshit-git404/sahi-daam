import base64
import binascii
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ml.freshness_model import predict_freshness
from ml.produce_classifier import identify_produce

router = APIRouter()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
def scan_produce(request: ScanRequest):
    if not request.image:
        raise HTTPException(status_code=400, detail="An image is required.")

    try:
        image_bytes = _decode_image(request.image)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info("Photo received")
    try:
        classification = identify_produce(image_bytes)
    except (RuntimeError, ValueError, OSError) as exc:
        logger.exception("Produce classifier failed")
        raise HTTPException(status_code=500, detail="Produce classifier unavailable.") from exc

    detected_produce = classification["produce_type"]
    produce_confidence = classification["produce_confidence"]
    logger.info(
        "Produce identified: %s | Confidence: %.2f%%",
        detected_produce,
        produce_confidence,
    )

    logger.info("ML model running for %s", detected_produce)
    try:
        freshness_data = predict_freshness(image_bytes, detected_produce)
    except RuntimeError as exc:
        logger.exception("Freshness model inference failed")
        raise HTTPException(status_code=500, detail="Freshness model unavailable.") from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info(
        "Result: %s | Freshness score: %s%%",
        freshness_data["freshness_label"],
        freshness_data["freshness_percent"],
    )
    return {
        "produce_type": detected_produce,
        "produce_confidence": produce_confidence,
        **freshness_data,
        "wholesale_price": 22,
        "markup_range": {"min_pct": 30, "max_pct": 45},
        "fair_price_range": {"min": 27, "max": 30, "unit": "kg"},
        "data_confidence": "Estimated",
        "location": "Katpadi, Vellore",
        "date": "2026-08-19",
        "quickcommerce_price": {"source": "Blinkit", "price": 38, "unit": "kg"},
    }
