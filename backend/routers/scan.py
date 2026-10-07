import base64
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.schemas import Observation, ObservationView
from quality.estimator import HybridQualityEstimator
from market.evidence import MarketEvidenceProvider
from market.reliability import MarketReliabilityScorer
from market.estimator import WeightedMarketPriceEstimator
from valuation.engine import UncertaintyAwareValuationEngine
from controller.observation_controller import AdaptiveObservationController
from session.manager import session_manager
from data.agmarknet.service import get_mandi_prices, refresh_all_mandi_prices
from pricing.engine import analyze_price_trend

router = APIRouter()

# Shared adaptive components
quality_estimator = HybridQualityEstimator()
evidence_provider = MarketEvidenceProvider()
reliability_scorer = MarketReliabilityScorer()
market_estimator = WeightedMarketPriceEstimator(reliability_scorer)
valuation_engine = UncertaintyAwareValuationEngine()
controller = AdaptiveObservationController()


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


class ScanRequest(BaseModel):
    produce_type: Optional[str] = None
    image: Optional[str] = None
    session_id: Optional[str] = None
    view: Optional[str] = "front"


@router.post("/scan-produce")
async def scan_produce(request: ScanRequest):
    """
    Analyzes produce using the Uncertainty-Driven Adaptive Valuation architecture.
    Provides backward-compatible response fields while generating persistent sessions,
    uncertainty indicators, and active observation recommendations.
    """
    produce_type = (request.produce_type or "tomato").lower()

    # 1. Initialize or retrieve valuation session
    session_id = request.session_id or f"val-{uuid.uuid4().hex[:10]}"
    session = session_manager.get_session(session_id)
    if not session:
        session = session_manager.create_session(commodity=produce_type, session_id=session_id)

    # 2. Package observation
    obs_index = session.observation_count + 1
    obs_id = f"obs-{uuid.uuid4().hex[:8]}"
    obs_view = ObservationView.FRONT if request.view == "front" else ObservationView.REVERSE_SIDE
    obs = Observation(
        observation_id=obs_id,
        observation_index=obs_index,
        image_b64=request.image,
        view=obs_view,
        timestamp=datetime.now().isoformat(),
        image_quality_score=0.88 if request.image else 0.70,
        lighting_score=0.82 if request.image else 0.65,
    )

    # 3. Quality & Epistemic Uncertainty Estimation
    q_estimate = quality_estimator.estimate_quality(obs, commodity_hint=produce_type)
    detected_type = q_estimate.commodity

    # 4. Multi-Source Market Evidence & Reliability Scoring
    evidence_records = await evidence_provider.collect_evidence(
        commodity=detected_type,
        state="Tamil Nadu",
        district="Vellore",
        target_market="Katpadi",
    )
    m_estimate = market_estimator.estimate_market_price(evidence_records, commodity=detected_type)

    # 5. Uncertainty-Aware Valuation Engine
    val_result = valuation_engine.calculate_valuation(
        quality_estimate=q_estimate,
        market_estimate=m_estimate,
        markup_min_pct=30.0,
        markup_max_pct=45.0,
        commodity=detected_type,
    )

    # 6. Adaptive Observation Controller (Active Feedback Loop)
    ctrl_decision = controller.evaluate_observation_decision(
        valuation=val_result,
        current_observation_count=obs_index,
    )

    # 7. Record Step in Session State
    session_manager.record_observation_step(
        session_id=session.session_id,
        observation=obs,
        quality_estimate=q_estimate,
        market_estimate=m_estimate,
        valuation=val_result,
        controller_decision=ctrl_decision,
    )

    # 8. Trend context calculation
    historical_obs = []
    for r in evidence_records:
        historical_obs.append({"date": r.timestamp, "price": r.price_per_kg})
    market_context = analyze_price_trend(m_estimate.estimated_price_per_kg, historical_obs)

    # 9. Quick-Commerce retail comparison snapshot
    quickcommerce_price = {"source": "Blinkit", "price": round(m_estimate.estimated_price_per_kg * 1.8, 1), "unit": "kg"}
    retail_comparison = None

    try:
        snapshot_path = Path(__file__).parent.parent / "data" / "quickcommerce_snapshot.json"
        if snapshot_path.exists():
            with open(snapshot_path, "r", encoding="utf-8") as f:
                qc_data = json.load(f)

            prod_data = qc_data.get(detected_type.lower())
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
                        "source": "Cached retail snapshot from verified collector.",
                    }
                    quickcommerce_price = {"source": str(best_platform).capitalize(), "price": best_price, "unit": "kg"}
    except Exception as e:
        print(f"Retail comparison snapshot error: {e}")

    # Return complete unified contract
    return {
        # Core identification
        "produce_type": detected_type.capitalize(),
        "detected_produce_id": detected_type.lower(),
        "classification_confidence": q_estimate.confidence,

        # Quality & Freshness Assessment
        "freshness_label": q_estimate.quality_class,
        "freshness_percent": q_estimate.freshness_percent,
        "freshness_note": q_estimate.freshness_note,
        "quality_adjustment": val_result.quality_adjustment.adjustment_per_kg,
        "quality_adjustment_label": q_estimate.quality_adjustment_label,
        "quality_uncertainty": q_estimate.uncertainty,

        # Market Benchmark
        "wholesale_price": m_estimate.estimated_price_per_kg,
        "market_uncertainty": m_estimate.market_uncertainty,
        "markup_range": {"min_pct": 30.0, "max_pct": 45.0},
        "fair_price_range": {
            "min": val_result.fair_min,
            "max": val_result.fair_max,
            "unit": "kg",
        },
        "data_confidence": "High" if val_result.confidence >= 0.75 else "Medium" if val_result.confidence >= 0.50 else "Estimated",
        "price_source": "weighted_multi_source_evidence",
        "used_markets": m_estimate.sources,
        "location": "Katpadi, Vellore",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "quickcommerce_price": quickcommerce_price,
        "retail_comparison": retail_comparison,
        "market_context": market_context,

        # Active Observation Loop & Uncertainty Instrumentation
        "session_id": session.session_id,
        "observation_count": session.observation_count,
        "valuation_uncertainty": val_result.valuation_uncertainty,
        "valuation_confidence": val_result.confidence,
        "needs_additional_observation": ctrl_decision.decision.value == "ACQUIRE_ADDITIONAL_OBSERVATION",
        "controller_decision": ctrl_decision.decision.value,
        "controller_reason": ctrl_decision.reason,
        "observation_request": ctrl_decision.observation_request.dict() if ctrl_decision.observation_request else None,
        "evi": ctrl_decision.expected_value_of_information,
    }
