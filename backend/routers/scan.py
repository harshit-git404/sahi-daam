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
    from ..data.history import analyze_distinct_history
    from ..data.retail_service import get_retail_prices
except ImportError:
    from data.agmarknet.service import get_mandi_prices
    from ml.freshness_model import predict_freshness
    from ml.produce_classifier import identify_produce
    from ml.gemini_analysis import analyze_with_gemini, GeminiUnavailable
    from pricing.engine import calculate_fair_price
    from data.history import analyze_distinct_history
    from data.retail_service import get_retail_prices

router = APIRouter()
logger = logging.getLogger(__name__)

MARKUP_MIN = 30
MARKUP_MAX = 45


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class ScanRequest(BaseModel):
    produce_type: str | None = Field(default=None, min_length=1)
    image: str | None = None
    # Structured location fields — do NOT parse from display strings
    state: str | None = None
    district: str | None = None
    market: str | None = None
    purchase_type: str = "street_vendor"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _build_market_unavailable() -> dict:
    return {
        "status": "UNAVAILABLE",
        "today_price": None,
        "unit": "kg",
        "current_value": None,
        "average_10_days": None,
        "high_10_days": None,
        "low_10_days": None,
        "percentage_change": None,
        "trend": "UNAVAILABLE",
        "history": [],
        "periods_available": 0,
    }


def _build_retail_unavailable(commodity_id: str, location: str | None, message: str) -> dict:
    return {
        "status": "UNAVAILABLE",
        "commodity": commodity_id,
        "location": location,
        "products": [],
        "message": message,
    }


# ---------------------------------------------------------------------------
# Debug endpoint — keep for Agmarknet verification
# ---------------------------------------------------------------------------

@router.get("/api/market-price")
async def verify_market_price(
    commodity: str,
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
):
    """Verify the existing Agmarknet integration."""
    return await get_mandi_prices(commodity, state, district, market)


# ---------------------------------------------------------------------------
# Main scan endpoint
# ---------------------------------------------------------------------------

@router.post("/scan-produce")
async def scan_produce(request: ScanRequest):
    """
    Complete produce analysis pipeline:
    1. Gemini Flash (primary) or local ML fallback for produce ID + freshness
    2. Agmarknet mandi price + 10-day market history
    3. Freshness-adjusted fair price
    4. Retail reference prices (Blinkit + Zepto)

    Failure isolation:
    - Gemini failure → local ML fallback (not an error)
    - Both ML paths fail → 503 error
    - Agmarknet failure → ML result returned; market.status = UNAVAILABLE
    - Retail failure → ML + market result returned; retail.status = UNAVAILABLE
    """
    if not request.image:
        raise HTTPException(
            status_code=400,
            detail="An image is required for produce analysis.",
        )

    try:
        image_bytes = _decode_image(request.image)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # ------------------------------------------------------------------
    # Step 1: ML Analysis (Gemini → local fallback)
    # ------------------------------------------------------------------
    analysis_provider = "gemini"
    freshness_data: dict = {}
    detected_produce: str = ""
    detected_produce_id: str = ""
    produce_confidence: float = 0.0

    try:
        analysis = await asyncio.to_thread(analyze_with_gemini, image_bytes)
        detected_produce = str(analysis["produce_type"]).strip()
        detected_produce_id = detected_produce.lower().replace(" ", "_")
        produce_confidence = float(analysis["produce_confidence"])
        freshness_data = {
            key: analysis[key]
            for key in (
                "freshness_label",
                "freshness_percent",
                "freshness_note",
                "quality_adjustment",
                "quality_adjustment_label",
            )
            if key in analysis
        }
        logger.info(
            "Gemini analysis succeeded: produce=%s confidence=%.1f%% freshness=%s%%",
            detected_produce,
            produce_confidence,
            freshness_data.get("freshness_percent"),
        )
    except GeminiUnavailable as gem_exc:
        analysis_provider = "local_fallback"
        logger.info("Gemini unavailable (%s), using local ML fallback.", gem_exc)
        try:
            classification = identify_produce(image_bytes)
            detected_produce = classification["produce_type"]
            detected_produce_id = classification["produce_id"]
            produce_confidence = classification["produce_confidence"]
            freshness_data = predict_freshness(image_bytes, detected_produce)
            logger.info(
                "Local ML fallback succeeded: produce=%s confidence=%.1f%% freshness=%s%%",
                detected_produce,
                produce_confidence,
                freshness_data.get("freshness_percent"),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            logger.exception("Local ML fallback failed")
            raise HTTPException(
                status_code=503,
                detail=(
                    "Both Gemini and local produce analysis are currently unavailable. "
                    "Please try again later."
                ),
            ) from exc

    quality_adjustment = int(freshness_data.get("quality_adjustment", 0))

    # ------------------------------------------------------------------
    # Step 2: Agmarknet mandi prices + 10-day market history
    # (Failure here must NOT erase the ML result)
    # ------------------------------------------------------------------
    market_data: dict = _build_market_unavailable()
    wholesale_price: float | None = None
    location_display: str | None = None

    try:
        commodity_query = detected_produce.replace("_", " ").title()
        mandi_response = await get_mandi_prices(
            commodity=commodity_query,
            state=request.state,
            district=request.district,
            market=request.market,
        )
        records = mandi_response.get("records", [])

        if records:
            # Build 10-day history from ALL returned records (not just the latest)
            history_result = analyze_distinct_history(
                records,
                date_field="arrival_date",
                value_field="modal_price_per_kg",
                limit=10,
            )
            latest_record = records[0]  # already sorted newest-first by service
            wholesale_price = latest_record.get("modal_price_per_kg") or None
            data_date = latest_record.get("arrival_date", "")
            if "/" in data_date:
                try:
                    day, month, year = data_date.split("/")
                    data_date = f"{year}-{month}-{day}"
                except ValueError:
                    logger.warning("Unexpected market date format: %s", data_date)

            location_display = (
                f"{latest_record.get('market', '')}, {latest_record.get('district', '')}"
                .strip(", ")
                or None
            )

            market_data = {
                "status": "AVAILABLE",
                "today_price": wholesale_price,
                "unit": "kg",
                "date": data_date,
                "market_name": latest_record.get("market", ""),
                "district": latest_record.get("district", ""),
                **history_result,
            }
            logger.info(
                "Agmarknet: %d records for %s; wholesale=₹%s; periods=%d",
                len(records),
                commodity_query,
                wholesale_price,
                history_result.get("periods_available", 0),
            )
        else:
            logger.info("Agmarknet returned 0 records for %s", commodity_query)
            market_data["date"] = ""

    except Exception as exc:
        logger.exception("Agmarknet request failed for %s", detected_produce)
        market_data = _build_market_unavailable()
        market_data["error"] = "MARKET_UNAVAILABLE"
        market_data["date"] = ""

    # ------------------------------------------------------------------
    # Step 3: Fair price calculation
    # (Only when wholesale price is available; freshness always applied)
    # ------------------------------------------------------------------
    pricing: dict | None = None
    if wholesale_price is not None:
        pricing = calculate_fair_price(
            wholesale_price, MARKUP_MIN, MARKUP_MAX, quality_adjustment
        )
        logger.info(
            "Fair price: ₹%s–₹%s (wholesale=₹%s markup=%d–%d%% quality_adj=%d)",
            pricing["min"],
            pricing["max"],
            wholesale_price,
            MARKUP_MIN,
            MARKUP_MAX,
            quality_adjustment,
        )

    # ------------------------------------------------------------------
    # Step 4: Retail reference prices (Blinkit + Zepto)
    # (Failure here must NOT erase ML + market results)
    # ------------------------------------------------------------------
    location_str = (
        f"{request.district or ''}, {request.state or ''}".strip(", ") or None
    )
    retail: dict = _build_retail_unavailable(detected_produce_id, location_str, "Retail fetch not attempted.")

    try:
        retail = get_retail_prices(detected_produce_id, location_str)
        logger.info(
            "Retail prices for %s: status=%s products=%d",
            detected_produce_id,
            retail.get("status"),
            len(retail.get("products", [])),
        )
    except Exception as exc:
        logger.exception("Retail price fetch failed for %s", detected_produce_id)
        retail = _build_retail_unavailable(
            detected_produce_id,
            location_str,
            "Retail price service temporarily unavailable.",
        )

    # ------------------------------------------------------------------
    # Step 5: Assemble final response
    # ------------------------------------------------------------------
    market_status = market_data.get("status", "UNAVAILABLE")

    # Best retail reference for haggle context
    retail_products = retail.get("products", [])
    online_reference_min: float | None = None
    online_reference_max: float | None = None
    if retail_products:
        prices_per_kg = [p["price_per_kg"] for p in retail_products if p.get("price_per_kg")]
        if prices_per_kg:
            online_reference_min = round(min(prices_per_kg), 2)
            online_reference_max = round(max(prices_per_kg), 2)

    # Quick-commerce summary for backward-compatibility
    quickcommerce_price: dict | None = None
    if retail_products:
        best = retail_products[0]  # already sorted by price_per_kg
        quickcommerce_price = {
            "source": best["platform"].capitalize(),
            "price": best["price_per_kg"],
            "unit": "kg",
        }

    return {
        # --- ML result ---
        "produce_type": detected_produce,
        "detected_produce_id": detected_produce_id,
        "produce_confidence": produce_confidence,
        "classification_confidence": produce_confidence,
        "analysis_provider": analysis_provider,
        # --- Freshness ---
        **freshness_data,
        # --- Market ---
        "market_status": market_status,
        "wholesale_price": wholesale_price,
        "markup_range": {"min_pct": MARKUP_MIN, "max_pct": MARKUP_MAX},
        "fair_price_range": {**pricing, "unit": "kg"} if pricing else None,
        "data_confidence": "High" if market_status == "AVAILABLE" else "Unavailable",
        "location": location_display,
        "date": market_data.get("date", ""),
        # --- Structured market block (consumed by frontend) ---
        "market": market_data,
        # --- Retail reference ---
        "retail": retail,
        # --- Pricing block ---
        "pricing": {
            "fair_price_min": pricing["min"],
            "fair_price_max": pricing["max"],
        } if pricing else None,
        # --- Haggle context references ---
        "online_reference_min": online_reference_min,
        "online_reference_max": online_reference_max,
        # --- Backward-compatible quick-commerce field ---
        "quickcommerce_price": quickcommerce_price,
    }
