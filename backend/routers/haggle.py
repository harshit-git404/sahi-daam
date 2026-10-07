from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal
from pricing.engine import analyze_purchase_decision
from pricing.phrasebook import generate_bargain_phrases
from session.manager import session_manager
from config import settings

router = APIRouter()

class HaggleRequest(BaseModel):
    produce_type: str
    asking_price: float
    fair_price_min: float
    fair_price_max: float
    freshness_label: Optional[str] = None
    quickcommerce_price: Optional[Dict[str, Any]] = None
    language: Literal["hi", "ta", "en"] = "hi"
    session_id: Optional[str] = None
    valuation_uncertainty: Optional[float] = None
    confidence: Optional[float] = None

@router.post("/haggle-check")
def haggle_check(request: HaggleRequest):
    # 1. Base purchase decision analysis
    result = analyze_purchase_decision(
        request.fair_price_min,
        request.fair_price_max,
        request.asking_price,
        request.freshness_label,
        request.quickcommerce_price
    )
    
    # 2. Check session or payload for high valuation uncertainty
    uncertainty = request.valuation_uncertainty
    confidence = request.confidence
    
    if request.session_id:
        session = session_manager.get_session(request.session_id)
        if session and session.current_valuation:
            uncertainty = session.current_valuation.valuation_uncertainty
            confidence = session.current_valuation.confidence

    # If uncertainty is elevated and confidence is below threshold,
    # prevent binary aggressive overpricing assertion
    is_uncertain = (confidence is not None and confidence < settings.INSUFFICIENT_CONFIDENCE_THRESHOLD) or \
                   (uncertainty is not None and uncertainty > settings.MAX_VALUATION_UNCERTAINTY)

    if is_uncertain and result.get("decision") in ("OVERPRICED", "SLIGHTLY_HIGH"):
        result["confidence_caution"] = (
            f"Valuation uncertainty is elevated ({uncertainty or 0.45:.2f}). "
            "Ask the vendor to confirm produce grade and weight before hard bargaining."
        )
        result["recommendation"]["headline"] = "Estimate is uncertain — verify before hard bargaining."
        result["recommendation"]["explanation"] = (
            f"Asking ₹{request.asking_price}/kg. Our estimated fair range is "
            f"₹{request.fair_price_min}–₹{request.fair_price_max}/kg, but information uncertainty is elevated. "
            "Negotiate politely or request an additional observation."
        )
        result["severity"] = "UNCERTAIN"
        result["decision"] = "INSUFFICIENT_CONFIDENCE"
    
    # 3. Generate contextual phrases
    phrases, source = generate_bargain_phrases(
        produce_type=request.produce_type,
        verdict=result["verdict"],
        suggested_price=result["suggested_price"],
        decision=result["decision"],
        language=request.language,
    )
    
    result["phrases"] = phrases
    result["phrases_source"] = source
    result["valuation_uncertainty"] = uncertainty
    result["valuation_confidence"] = confidence
    return result
