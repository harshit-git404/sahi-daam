"""Adaptive Valuation API Router.

Implements persistent valuation sessions, active multi-observation loops,
before/after uncertainty instrumentation, and deterministic scenario simulations.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.schemas import (
    Observation,
    ObservationView,
    ValuationSession,
    ValuationResult,
    ControllerDecision,
    AnomalyAnalysisResult,
)
from quality.estimator import HybridQualityEstimator, SimulatedQualityEstimator
from market.evidence import MarketEvidenceProvider
from market.reliability import MarketReliabilityScorer
from market.estimator import WeightedMarketPriceEstimator
from valuation.engine import UncertaintyAwareValuationEngine
from observation.fusion import ObservationFusionEngine
from controller.observation_controller import AdaptiveObservationController
from pricing.anomaly import PriceQualityAnomalyDetector
from session.manager import session_manager
from config import settings

router = APIRouter(prefix="/api/valuation", tags=["Adaptive Valuation"])

# Pipeline singletons
quality_estimator = HybridQualityEstimator()
evidence_provider = MarketEvidenceProvider()
reliability_scorer = MarketReliabilityScorer()
market_estimator = WeightedMarketPriceEstimator(reliability_scorer)
valuation_engine = UncertaintyAwareValuationEngine()
fusion_engine = ObservationFusionEngine()
controller = AdaptiveObservationController()
anomaly_detector = PriceQualityAnomalyDetector()


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class StartValuationRequest(BaseModel):
    commodity: str = "tomato"
    image: Optional[str] = None
    view: ObservationView = ObservationView.FRONT
    session_id: Optional[str] = None
    location_state: str = "Tamil Nadu"
    location_district: str = "Vellore"
    target_market: str = "Katpadi"


class AdditionalObservationRequest(BaseModel):
    session_id: str
    image: Optional[str] = None
    view: ObservationView = ObservationView.REVERSE_SIDE
    force_finalize: bool = False


class ValuationDecisionRequest(BaseModel):
    session_id: str
    asking_price: float
    quickcommerce_price: Optional[float] = None
    language: str = "hi"


class SimulationRequest(BaseModel):
    scenario_id: str = "scenario_2_low_confidence_requires_second_view"
    commodity: str = "tomato"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/session")
async def start_valuation_session(request: StartValuationRequest):
    """
    Step 1 of the Adaptive Loop:
    Initializes a valuation session, records the initial observation, estimates quality
    and uncertainty, retrieves multi-source market evidence, derives initial valuation,
    and queries the Adaptive Observation Controller to determine if additional views are needed.
    """
    comm = request.commodity.lower().strip()
    session = session_manager.create_session(
        commodity=comm,
        max_observations=settings.MAX_OBSERVATIONS,
        session_id=request.session_id,
    )

    # 1. Register Observation 1
    obs_id = f"obs-{uuid.uuid4().hex[:8]}"
    obs = Observation(
        observation_id=obs_id,
        observation_index=1,
        image_b64=request.image,
        view=request.view,
        timestamp=datetime.now().isoformat(),
        image_quality_score=0.85 if request.image else 0.70,
        lighting_score=0.80 if request.image else 0.65,
    )

    # 2. Quality & Uncertainty Estimation
    q_estimate = quality_estimator.estimate_quality(obs, commodity_hint=comm)

    # 3. Multi-Source Market Evidence
    evidence_records = await evidence_provider.collect_evidence(
        commodity=q_estimate.commodity,
        state=request.location_state,
        district=request.location_district,
        target_market=request.target_market,
    )
    m_estimate = market_estimator.estimate_market_price(evidence_records, commodity=q_estimate.commodity)

    # 4. Uncertainty-Aware Valuation
    val_result = valuation_engine.calculate_valuation(
        quality_estimate=q_estimate,
        market_estimate=m_estimate,
        commodity=q_estimate.commodity,
    )

    # 5. Controller Decision (EVI vs Cost)
    ctrl_decision = controller.evaluate_observation_decision(
        valuation=val_result,
        current_observation_count=1,
    )

    # 6. Record State in Session
    updated_session = session_manager.record_observation_step(
        session_id=session.session_id,
        observation=obs,
        quality_estimate=q_estimate,
        market_estimate=m_estimate,
        valuation=val_result,
        controller_decision=ctrl_decision,
    )

    return {
        "session_id": updated_session.session_id,
        "status": updated_session.status,
        "observation_count": updated_session.observation_count,
        "quality_estimate": q_estimate,
        "market_estimate": m_estimate,
        "valuation": val_result,
        "controller_decision": ctrl_decision,
        "needs_additional_observation": ctrl_decision.decision.value == "ACQUIRE_ADDITIONAL_OBSERVATION",
        "observation_request": ctrl_decision.observation_request,
    }


@router.post("/observe")
async def submit_additional_observation(request: AdditionalObservationRequest):
    """
    Step 2 of the Adaptive Loop:
    Receives an additional targeted visual observation, estimates quality, fuses all
    available observations to reduce epistemic uncertainty, updates the fair price interval,
    and runs the controller again to either request another view or finalize.
    """
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Valuation session '{request.session_id}' not found.")

    obs_idx = session.observation_count + 1
    obs_id = f"obs-{uuid.uuid4().hex[:8]}"
    obs = Observation(
        observation_id=obs_id,
        observation_index=obs_idx,
        image_b64=request.image,
        view=request.view,
        timestamp=datetime.now().isoformat(),
        image_quality_score=0.90 if request.image else 0.75,
        lighting_score=0.85 if request.image else 0.70,
    )

    # 1. Quality Estimate for this single observation
    new_q_estimate = quality_estimator.estimate_quality(obs, commodity_hint=session.commodity)

    # 2. Multi-Observation Fusion across all session observations
    all_q_estimates = session.quality_history + [new_q_estimate]
    fused_q_estimate = fusion_engine.fuse_estimates(all_q_estimates)

    # 3. Re-use or refresh Market Evidence
    m_estimate = session.current_market_estimate
    if not m_estimate:
        evidence = await evidence_provider.collect_evidence(commodity=session.commodity)
        m_estimate = market_estimator.estimate_market_price(evidence, commodity=session.commodity)

    # 4. Recompute Uncertainty-Aware Valuation with Fused Evidence
    val_result = valuation_engine.calculate_valuation(
        quality_estimate=fused_q_estimate,
        market_estimate=m_estimate,
        commodity=session.commodity,
    )

    # 5. Controller Decision on Next Step
    ctrl_decision = controller.evaluate_observation_decision(
        valuation=val_result,
        current_observation_count=obs_idx,
        force_finalize=request.force_finalize,
    )

    # 6. Record State in Session
    updated_session = session_manager.record_observation_step(
        session_id=session.session_id,
        observation=obs,
        quality_estimate=fused_q_estimate,
        market_estimate=m_estimate,
        valuation=val_result,
        controller_decision=ctrl_decision,
    )

    comparison = session_manager.get_comparison_metrics(session.session_id)

    return {
        "session_id": updated_session.session_id,
        "status": updated_session.status,
        "observation_count": updated_session.observation_count,
        "fused_quality_estimate": fused_q_estimate,
        "valuation": val_result,
        "controller_decision": ctrl_decision,
        "needs_additional_observation": ctrl_decision.decision.value == "ACQUIRE_ADDITIONAL_OBSERVATION",
        "observation_request": ctrl_decision.observation_request,
        "instrumentation_comparison": comparison,
    }


@router.get("/{session_id}")
def get_valuation_session(session_id: str):
    """Retrieves full session history, step-by-step decision trace, and before/after metrics."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Valuation session '{session_id}' not found.")
    comparison = session_manager.get_comparison_metrics(session_id)
    return {
        "session": session,
        "instrumentation_comparison": comparison,
    }


@router.post("/decision")
def analyze_asking_price_decision(request: ValuationDecisionRequest):
    """
    Evaluates vendor asking price against the current valuation session.
    Withholds aggressive overpricing verdicts if compound uncertainty is high.
    """
    session = session_manager.get_session(request.session_id)
    if not session or not session.current_valuation:
        raise HTTPException(status_code=404, detail="Active valuation not found for this session.")

    anomaly_result = anomaly_detector.analyze_price_anomaly(
        valuation=session.current_valuation,
        asking_price=request.asking_price,
        quickcommerce_ref_price=request.quickcommerce_price,
    )

    # Also generate phrases using phrasebook
    from pricing.phrasebook import generate_bargain_phrases
    phrases, source = generate_bargain_phrases(
        produce_type=session.commodity,
        verdict="Overpriced" if anomaly_result.decision.value in ("OVERPRICED", "SLIGHTLY_HIGH") else "Fair Price",
        suggested_price=anomaly_result.strategy.starting_offer,
        decision=anomaly_result.decision.value,
        language=request.language,
    )

    return {
        **anomaly_result.dict(),
        "phrases": phrases,
        "phrases_source": source,
    }


@router.post("/simulate")
async def run_simulation_scenario(request: SimulationRequest):
    """
    Test and demonstration harness endpoint. Runs fully deterministic scenarios
    demonstrating the complete 10-step adaptive loop with verifiable before/after metrics.
    """
    scenario_id = request.scenario_id
    comm = request.commodity.lower()

    if scenario_id == "scenario_1_high_confidence_no_extra_view":
        # Scenario 1: High confidence initial observation -> Finalizes immediately
        test_session = session_manager.create_session(commodity=comm)
        sim_estimator = SimulatedQualityEstimator(
            fixed_commodity=comm,
            fixed_quality=0.88,
            fixed_confidence=0.92,
            fixed_disagreement=0.03,
        )
        obs_1 = Observation(
            observation_id="sim-obs-1",
            observation_index=1,
            view=ObservationView.FRONT,
            timestamp=datetime.now().isoformat(),
            image_quality_score=0.95,
            lighting_score=0.90,
        )
        q_1 = sim_estimator.estimate_quality(obs_1, comm)
        evidence = await evidence_provider.collect_evidence(commodity=comm)
        m_est = market_estimator.estimate_market_price(evidence, comm)
        val_1 = valuation_engine.calculate_valuation(q_1, m_est, commodity=comm)
        ctrl_dec = controller.evaluate_observation_decision(val_1, 1)
        session_manager.record_observation_step(test_session.session_id, obs_1, q_1, m_est, val_1, ctrl_dec)

        return {
            "scenario": scenario_id,
            "description": "High quality image with high confidence; controller finalizes at step 1.",
            "session_id": test_session.session_id,
            "observations_taken": 1,
            "final_action": ctrl_dec.decision.value,
            "action_reason": ctrl_dec.reason,
            "valuation": val_1,
        }

    elif scenario_id == "scenario_2_low_confidence_requires_second_view":
        # Scenario 2: Low confidence single view -> Requests View 2 -> Fuses -> Narrows range
        test_session = session_manager.create_session(commodity=comm)
        sim_estimator_step1 = SimulatedQualityEstimator(
            fixed_commodity=comm,
            fixed_quality=0.72,
            fixed_confidence=0.58,
            fixed_disagreement=0.20,
        )
        obs_1 = Observation(
            observation_id="sim-obs-1",
            observation_index=1,
            view=ObservationView.FRONT,
            timestamp=datetime.now().isoformat(),
            image_quality_score=0.60,
            lighting_score=0.55,
        )
        q_1 = sim_estimator_step1.estimate_quality(obs_1, comm)
        evidence = await evidence_provider.collect_evidence(commodity=comm)
        m_est = market_estimator.estimate_market_price(evidence, comm)
        val_1 = valuation_engine.calculate_valuation(q_1, m_est, commodity=comm)
        ctrl_1 = controller.evaluate_observation_decision(val_1, 1)
        session_manager.record_observation_step(test_session.session_id, obs_1, q_1, m_est, val_1, ctrl_1)

        # Step 2: User provides requested reverse side view with high clarity
        sim_estimator_step2 = SimulatedQualityEstimator(
            fixed_commodity=comm,
            fixed_quality=0.75,
            fixed_confidence=0.90,
            fixed_disagreement=0.04,
        )
        obs_2 = Observation(
            observation_id="sim-obs-2",
            observation_index=2,
            view=ObservationView.REVERSE_SIDE,
            timestamp=datetime.now().isoformat(),
            image_quality_score=0.92,
            lighting_score=0.88,
        )
        q_2 = sim_estimator_step2.estimate_quality(obs_2, comm)
        fused_q = fusion_engine.fuse_estimates([q_1, q_2])
        val_2 = valuation_engine.calculate_valuation(fused_q, m_est, commodity=comm)
        ctrl_2 = controller.evaluate_observation_decision(val_2, 2)
        session_manager.record_observation_step(test_session.session_id, obs_2, fused_q, m_est, val_2, ctrl_2)

        comparison = session_manager.get_comparison_metrics(test_session.session_id)

        return {
            "scenario": scenario_id,
            "description": "Initial uncertain view triggers ObservationRequest; complementary second view fuses to reduce uncertainty and narrow fair price range.",
            "session_id": test_session.session_id,
            "observations_taken": 2,
            "step_1_decision": ctrl_1.decision.value,
            "step_1_request": ctrl_1.observation_request,
            "step_2_decision": ctrl_2.decision.value,
            "instrumentation_comparison": comparison,
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unknown scenario ID: {scenario_id}")
