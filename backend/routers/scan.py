import base64
import binascii
import logging
from typing import Optional
import asyncio

import uuid
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from ..data.agmarknet.service import get_mandi_prices
    from ..ml.freshness_model import predict_freshness
    from ..ml.produce_classifier import identify_produce
    from ..ml.gemini_analysis import analyze_with_gemini, GeminiUnavailable
    from ..pricing.engine import calculate_fair_price
    from ..data.history import analyze_distinct_history
    from ..data.retail_service import get_retail_prices
    from ..database.connection import get_db
    from ..database.repositories import LocalityRepository, MandiRepository, WholesalePriceRepository
    from ..services.transport_service import TransportCostService
    from ..pricing.reconciliation_service import PricingReconciliationService
    from ..services.ledger_service import CalculationLedgerService
except ImportError:
    from data.agmarknet.service import get_mandi_prices
    from ml.freshness_model import predict_freshness
    from ml.produce_classifier import identify_produce
    from ml.gemini_analysis import analyze_with_gemini, GeminiUnavailable
    from pricing.engine import calculate_fair_price
    from data.history import analyze_distinct_history
    from data.retail_service import get_retail_prices
    from database.connection import get_db
    from database.repositories import LocalityRepository, MandiRepository, WholesalePriceRepository
    from services.transport_service import TransportCostService
    from pricing.reconciliation_service import PricingReconciliationService
    from services.ledger_service import CalculationLedgerService

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
    # Locality & Mandi selection for transport & community reconciliation
    locality_id: str | None = None
    pincode: str | None = None
    mandi_id: str | None = None


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

@router.get("/market-price")
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
@router.post("/api/scan-produce")
async def scan_produce(
    request: ScanRequest,
    db: Session = Depends(get_db),
):
    """
    Complete produce analysis pipeline:
    1. Gemini Flash (primary) or local ML fallback for produce ID + freshness
    2. Agmarknet mandi price + 10-day market history + SQLite wholesale fallback
    3. Locality-aware transport cost calculation
    4. Adaptive community price reconciliation (2-day window, 10-report minimum threshold)
    5. Freshness-adjusted fair price & baseline range preservation
    6. Retail reference prices (Blinkit + Zepto)
    7. Persistent JSON calculation ledger and global SHA-256 hash chaining

    Failure isolation:
    - Gemini failure → local ML fallback (not an error)
    - Both ML paths fail → 503 error
    - Agmarknet failure → wholesale fallback from SQLite or UNAVAILABLE
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
            classification = await asyncio.to_thread(identify_produce, image_bytes)
            detected_produce = classification["produce_type"]
            detected_produce_id = classification["produce_id"]
            produce_confidence = classification["produce_confidence"]
            freshness_data = await asyncio.to_thread(predict_freshness, image_bytes, detected_produce)
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
    # Step 1.5: Locality and Mandi Resolution
    # ------------------------------------------------------------------
    resolved_locality = None
    resolved_locality_id = None
    if request.locality_id:
        resolved_locality = LocalityRepository.get_by_id(db, request.locality_id)
        if resolved_locality:
            resolved_locality_id = resolved_locality.id
    elif request.pincode:
        locs = LocalityRepository.list_by_pincode(db, request.pincode.strip())
        if locs:
            resolved_locality = locs[0]
            resolved_locality_id = resolved_locality.id

    resolved_mandi = None
    resolved_mandi_id = None
    if request.mandi_id:
        resolved_mandi = MandiRepository.get_by_id(db, request.mandi_id)
        if resolved_mandi:
            resolved_mandi_id = resolved_mandi.id
    elif resolved_locality:
        district_mandis = MandiRepository.list_by_district(db, resolved_locality.district)
        if district_mandis:
            resolved_mandi = district_mandis[0]
            resolved_mandi_id = resolved_mandi.id
        else:
            all_mandis = MandiRepository.list_all(db)
            if all_mandis:
                resolved_mandi = all_mandis[0]
                resolved_mandi_id = resolved_mandi.id

    # ------------------------------------------------------------------
    # Step 2: Agmarknet mandi prices + 10-day market history + SQLite fallback
    # ------------------------------------------------------------------
    market_data: dict = _build_market_unavailable()
    wholesale_price: float | None = None
    location_display: str | None = None

    try:
        commodity_query = detected_produce.replace("_", " ").title()
        mandi_response = await get_mandi_prices(
            commodity=commodity_query,
            state=request.state or (resolved_locality.state if resolved_locality else None),
            district=request.district or (resolved_locality.district if resolved_locality else None),
            market=request.market or (resolved_mandi.market_name if resolved_mandi else None),
        )
        records = mandi_response.get("records", [])

        if records:
            history_result = analyze_distinct_history(
                records,
                date_field="arrival_date",
                value_field="modal_price_per_kg",
                limit=10,
            )
            latest_record = records[0]
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
        else:
            logger.info("Agmarknet returned 0 records for %s", commodity_query)
            market_data["date"] = ""

    except Exception as exc:
        logger.exception("Agmarknet request failed for %s", detected_produce)
        market_data = _build_market_unavailable()
        market_data["error"] = "MARKET_UNAVAILABLE"
        market_data["date"] = ""

    # SQLite wholesale price fallback when Agmarknet is unavailable or returned no data and a locality/mandi is specified
    if wholesale_price is None and (resolved_mandi_id or resolved_locality_id):
        db_obs = WholesalePriceRepository.get_latest(
            db, commodity_id=detected_produce_id, mandi_id=resolved_mandi_id
        )
        if db_obs:
            wholesale_price = db_obs.price_per_kg
            obs_mandi = resolved_mandi or MandiRepository.get_by_id(db, db_obs.mandi_id)
            location_display = f"{obs_mandi.market_name if obs_mandi else 'Mandi'}, {obs_mandi.district if obs_mandi else (resolved_locality.district if resolved_locality else 'Tamil Nadu')}"
            market_data = {
                "status": "AVAILABLE",
                "today_price": wholesale_price,
                "unit": db_obs.unit or "kg",
                "date": db_obs.observed_at.strftime("%Y-%m-%d"),
                "market_name": obs_mandi.market_name if obs_mandi else "Local Mandi",
                "district": obs_mandi.district if obs_mandi else "Local District",
                "current_value": wholesale_price,
                "average_10_days": wholesale_price,
                "high_10_days": wholesale_price,
                "low_10_days": wholesale_price,
                "percentage_change": 0.0,
                "trend": "STABLE",
                "history": [],
                "periods_available": 1,
            }

    # ------------------------------------------------------------------
    # Step 2.5: Transport Cost Calculation
    # ------------------------------------------------------------------
    transport_result = None
    if resolved_mandi_id and resolved_locality_id:
        try:
            transport_result = TransportCostService.calculate_from_database_profile(
                session=db,
                vehicle_type="tata_ace",
                mandi_id=resolved_mandi_id,
            )
        except Exception as exc:
            logger.warning("Transport calculation failed: %s", exc)
            transport_result = None

    # ------------------------------------------------------------------
    # Step 3: Fair price & Adaptive Community Reconciliation
    # ------------------------------------------------------------------
    pricing: dict | None = None
    pricing_breakdown: dict = {}
    calc_status: str = "UNAVAILABLE"
    recon_result = None

    if wholesale_price is not None:
        recon_result = PricingReconciliationService.reconcile_fair_price(
            session=db,
            commodity_id=detected_produce_id,
            locality_id=resolved_locality_id,
            wholesale_price=wholesale_price,
            transport_result=transport_result,
            quality_adjustment=quality_adjustment,
        )
        calc_status = recon_result.calculation_status
        pricing_breakdown = recon_result.model_dump()
        if recon_result.reconciled_range:
            pricing = {
                "min": recon_result.reconciled_range.min,
                "max": recon_result.reconciled_range.max,
            }
        else:
            pricing = calculate_fair_price(
                wholesale_price, MARKUP_MIN, MARKUP_MAX, quality_adjustment
            )
    else:
        calc_status = "INCOMPLETE_MISSING_WHOLESALE"
        pricing_breakdown = {
            "status": "UNAVAILABLE",
            "message": "Wholesale price unavailable for produce",
            "missing_inputs": ["wholesale_price"],
        }

    # ------------------------------------------------------------------
    # Step 3.5: Ledger Persistence with SHA-256 Hash Chaining
    # ------------------------------------------------------------------
    calc_id = f"calc_{uuid.uuid4().hex[:12]}"
    evidence = {
        "commodity_id": detected_produce_id,
        "locality_id": resolved_locality_id,
        "mandi_id": resolved_mandi_id,
        "wholesale_price": wholesale_price,
        "wholesale_source": market_data.get("market_name", "agmarknet/sqlite"),
        "transport": transport_result.model_dump() if transport_result else {"status": "unavailable"},
        "quality_adjustment": quality_adjustment,
        "quality_adjustment_meaning": freshness_data.get("quality_adjustment_label", "No deduction"),
        "pricing_breakdown": pricing_breakdown,
        "missing_inputs": ["wholesale_price"] if wholesale_price is None else (["transport_cost"] if transport_result is None else []),
        "warnings": recon_result.warnings if recon_result else [],
        "fallback_decisions": recon_result.notes if recon_result else [],
    }

    ledger_record = None
    try:
        ledger_record = CalculationLedgerService.append_calculation(
            session=db,
            calculation_id=calc_id,
            commodity_id=detected_produce_id,
            locality_id=resolved_locality_id,
            status=calc_status,
            evidence=evidence,
            is_mock=True,
        )
    except Exception as exc:
        logger.exception("Failed to persist calculation to ledger: %s", exc)

    # ------------------------------------------------------------------
    # Step 4: Retail reference prices (Blinkit + Zepto)
    # ------------------------------------------------------------------
    location_str = (
        f"{request.district or ''}, {request.state or ''}".strip(", ") or None
    )
    retail: dict = _build_retail_unavailable(detected_produce_id, location_str, "Retail fetch not attempted.")

    try:
        retail = get_retail_prices(detected_produce_id, location_str)
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

    retail_products = retail.get("products", [])
    online_reference_min: float | None = None
    online_reference_max: float | None = None
    if retail_products:
        prices_per_kg = [p["price_per_kg"] for p in retail_products if p.get("price_per_kg")]
        if prices_per_kg:
            online_reference_min = round(min(prices_per_kg), 2)
            online_reference_max = round(max(prices_per_kg), 2)

    quickcommerce_price: dict | None = None
    if retail_products:
        best = retail_products[0]
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
        # --- Additive ledger & explainable pricing breakdown ---
        "pricing_breakdown": pricing_breakdown,
        "calculation_id": ledger_record.id if ledger_record else None,
        "sequence_number": ledger_record.sequence_number if ledger_record else None,
        "record_hash": ledger_record.current_record_hash if ledger_record else None,
        "calculation_status": calc_status,
        "is_mock": True,
        "locality_id": resolved_locality_id,
        "mandi_id": resolved_mandi_id,
    }

