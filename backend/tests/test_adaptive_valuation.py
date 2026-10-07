"""Automated Test Suite for Uncertainty-Driven Adaptive Valuation System.

Validates core invention mechanisms:
A. High confidence -> finalizes without another observation.
B. Low quality confidence -> triggers additional observation request.
C. High market source disagreement -> market uncertainty increases.
D. Strong market source agreement -> market confidence improves.
E. Multi-observation fusion reduces uncertainty -> fair interval narrows.
F. Multi-observation limit reached -> controller halts.
G. High valuation uncertainty -> withholds binary OVERPRICED verdict (INSUFFICIENT_CONFIDENCE).
H. Low asking price + degraded quality -> UNUSUALLY_CHEAP / CHECK_QUALITY.
I. High asking price + high-confidence valuation -> OVERPRICED.
J. Sparse/missing market data -> graceful handling with elevated uncertainty.
K. Session state persistence -> multi-observation history preserved.
L. Value of Information (EVI) computation.
"""

import pytest
from datetime import datetime
from config import settings
from core.schemas import (
    Observation,
    ObservationView,
    QualityEstimate,
    MarketEvidenceRecord,
    ControllerAction,
    AnomalyState,
)
from uncertainty.estimator import UncertaintyEstimator
from quality.estimator import SimulatedQualityEstimator
from market.reliability import MarketReliabilityScorer
from market.estimator import WeightedMarketPriceEstimator
from valuation.adjustment import QualityPriceAdjustmentModel
from valuation.engine import UncertaintyAwareValuationEngine
from observation.fusion import ObservationFusionEngine
from controller.observation_controller import AdaptiveObservationController
from pricing.anomaly import PriceQualityAnomalyDetector
from session.manager import SessionManager


# ---------------------------------------------------------------------------
# Test A & B: Uncertainty Estimation & Controller Observation Triggers
# ---------------------------------------------------------------------------

def test_high_confidence_finalizes_without_additional_observation():
    """Criterion B: When confidence is high and uncertainty low, controller finalizes at step 1."""
    unc_est = UncertaintyEstimator()
    sim_qual = SimulatedQualityEstimator(
        fixed_commodity="tomato",
        fixed_quality=0.92,
        fixed_confidence=0.95,
        fixed_disagreement=0.02,
        uncertainty_estimator=unc_est,
    )
    obs = Observation(
        observation_id="obs-high",
        observation_index=1,
        view=ObservationView.FRONT,
        timestamp=datetime.now().isoformat(),
        image_quality_score=0.95,
        lighting_score=0.90,
    )
    q = sim_qual.estimate_quality(obs)
    assert q.uncertainty <= settings.MAX_QUALITY_UNCERTAINTY

    # High quality market evidence
    rec = MarketEvidenceRecord(
        evidence_id="ev-1",
        source="Agmarknet APMC",
        commodity="tomato",
        market="Katpadi",
        state="Tamil Nadu",
        price_per_kg=25.0,
        timestamp="2026-10-07",
        distance_or_region="local_exact",
        freshness_hours=4.0,
        source_reliability=0.95,
        is_live=True,
    )
    m_est = WeightedMarketPriceEstimator().estimate_market_price([rec], "tomato")
    val_eng = UncertaintyAwareValuationEngine()
    valuation = val_eng.calculate_valuation(q, m_est)

    controller = AdaptiveObservationController(target_max_uncertainty=0.40)
    decision = controller.evaluate_observation_decision(valuation, current_observation_count=1)

    assert decision.decision == ControllerAction.FINALIZE_VALUATION
    assert decision.observation_request is None


def test_low_quality_confidence_requests_additional_observation():
    """Criterion A & B: Substantial visual uncertainty generates an ObservationRequest with positive EVI."""
    unc_est = UncertaintyEstimator()
    sim_qual = SimulatedQualityEstimator(
        fixed_commodity="tomato",
        fixed_quality=0.65,
        fixed_confidence=0.50,
        fixed_disagreement=0.30,
        uncertainty_estimator=unc_est,
    )
    obs = Observation(
        observation_id="obs-low",
        observation_index=1,
        view=ObservationView.FRONT,
        timestamp=datetime.now().isoformat(),
        image_quality_score=0.55,
        lighting_score=0.50,
    )
    q = sim_qual.estimate_quality(obs)
    assert q.uncertainty > settings.MAX_QUALITY_UNCERTAINTY

    rec = MarketEvidenceRecord(
        evidence_id="ev-1",
        source="Agmarknet APMC",
        commodity="tomato",
        market="Katpadi",
        state="Tamil Nadu",
        price_per_kg=25.0,
        timestamp="2026-10-07",
        distance_or_region="local_exact",
        freshness_hours=12.0,
        source_reliability=0.85,
        is_live=True,
    )
    m_est = WeightedMarketPriceEstimator().estimate_market_price([rec], "tomato")
    valuation = UncertaintyAwareValuationEngine().calculate_valuation(q, m_est)

    controller = AdaptiveObservationController()
    decision = controller.evaluate_observation_decision(valuation, current_observation_count=1)

    assert decision.decision == ControllerAction.ACQUIRE_ADDITIONAL_OBSERVATION
    assert decision.observation_request is not None
    assert decision.observation_request.requested_view == "reverse_side"
    assert decision.expected_value_of_information > settings.MIN_INFORMATION_GAIN_THRESHOLD


# ---------------------------------------------------------------------------
# Test C & D: Market Source Disagreement vs Agreement
# ---------------------------------------------------------------------------

def test_market_source_disagreement_increases_uncertainty():
    """Criterion C: When market sources conflict widely, market uncertainty increases significantly."""
    records_conflicting = [
        MarketEvidenceRecord(
            evidence_id="ev-1", source="APMC Market A", commodity="tomato",
            market="Market A", state="TN", price_per_kg=20.0, timestamp="2026-10-07",
            distance_or_region="district", freshness_hours=6.0, source_reliability=0.8, is_live=True
        ),
        MarketEvidenceRecord(
            evidence_id="ev-2", source="APMC Market B", commodity="tomato",
            market="Market B", state="TN", price_per_kg=48.0, timestamp="2026-10-07",
            distance_or_region="district", freshness_hours=6.0, source_reliability=0.8, is_live=True
        ),
    ]
    records_agreeing = [
        MarketEvidenceRecord(
            evidence_id="ev-1", source="APMC Market A", commodity="tomato",
            market="Market A", state="TN", price_per_kg=25.0, timestamp="2026-10-07",
            distance_or_region="district", freshness_hours=6.0, source_reliability=0.8, is_live=True
        ),
        MarketEvidenceRecord(
            evidence_id="ev-2", source="APMC Market B", commodity="tomato",
            market="Market B", state="TN", price_per_kg=26.0, timestamp="2026-10-07",
            distance_or_region="district", freshness_hours=6.0, source_reliability=0.8, is_live=True
        ),
    ]

    estimator = WeightedMarketPriceEstimator()
    est_conflicting = estimator.estimate_market_price(records_conflicting, "tomato")
    est_agreeing = estimator.estimate_market_price(records_agreeing, "tomato")

    assert est_conflicting.market_uncertainty > est_agreeing.market_uncertainty
    assert est_agreeing.confidence > est_conflicting.confidence


# ---------------------------------------------------------------------------
# Test E & F: Multi-Observation Fusion and Interval Narrowing
# ---------------------------------------------------------------------------

def test_additional_observation_reduces_uncertainty_and_narrows_range():
    """Criterion E: Agreeing complementary views reduce visual uncertainty and narrow fair price range."""
    fusion = ObservationFusionEngine()
    val_eng = UncertaintyAwareValuationEngine()

    # Step 1: Single view with uncertainty
    q1 = QualityEstimate(
        commodity="tomato", quality_score=0.75, freshness_score=0.75, quality_class="Fresh",
        confidence=0.65, uncertainty=0.48, observations_used=["obs-1"], freshness_percent=75
    )
    rec = MarketEvidenceRecord(
        evidence_id="ev-1", source="Agmarknet APMC", commodity="tomato",
        market="Katpadi", state="TN", price_per_kg=30.0, timestamp="2026-10-07",
        distance_or_region="local_exact", freshness_hours=4.0, source_reliability=0.95, is_live=True
    )
    m_est = WeightedMarketPriceEstimator().estimate_market_price([rec], "tomato")
    val_1 = val_eng.calculate_valuation(q1, m_est)
    width_step_1 = val_1.fair_max - val_1.fair_min

    # Step 2: Second view confirms condition with close agreement
    q2 = QualityEstimate(
        commodity="tomato", quality_score=0.78, freshness_score=0.78, quality_class="Fresh",
        confidence=0.90, uncertainty=0.25, observations_used=["obs-2"], freshness_percent=78
    )
    q_fused = fusion.fuse_estimates([q1, q2])
    assert q_fused.uncertainty < q1.uncertainty
    assert q_fused.confidence > q1.confidence

    val_2 = val_eng.calculate_valuation(q_fused, m_est)
    width_step_2 = val_2.fair_max - val_2.fair_min

    # Fair range should narrow with reduced uncertainty!
    assert width_step_2 < width_step_1
    assert val_2.valuation_uncertainty < val_1.valuation_uncertainty


def test_max_observations_halts_controller():
    """Criterion F: Controller stops requesting observations once MAX_OBSERVATIONS is reached."""
    q = QualityEstimate(
        commodity="tomato", quality_score=0.50, freshness_score=0.50, quality_class="Slightly Aged",
        confidence=0.50, uncertainty=0.60, observations_used=["obs-1", "obs-2", "obs-3"], freshness_percent=50
    )
    m_est = WeightedMarketPriceEstimator().estimate_market_price([], "tomato")
    val = UncertaintyAwareValuationEngine().calculate_valuation(q, m_est)

    controller = AdaptiveObservationController(max_observations=3)
    decision = controller.evaluate_observation_decision(val, current_observation_count=3)

    assert decision.decision == ControllerAction.FINALIZE_VALUATION
    assert "Maximum observation count" in decision.reason


# ---------------------------------------------------------------------------
# Test G, H, I: Price-Quality Anomaly Detection with Uncertainty
# ---------------------------------------------------------------------------

def test_high_uncertainty_withholds_confident_overpriced_verdict():
    """Criterion G: High valuation uncertainty yields INSUFFICIENT_CONFIDENCE instead of false binary OVERPRICED."""
    q = QualityEstimate(
        commodity="tomato", quality_score=0.70, freshness_score=0.70, quality_class="Fresh",
        confidence=0.35, uncertainty=0.65, observations_used=["obs-1"], freshness_percent=70
    )
    rec = MarketEvidenceRecord(
        evidence_id="ev-1", source="Legacy Cache", commodity="tomato",
        market="Unknown", state="TN", price_per_kg=25.0, timestamp="2026-10-01",
        distance_or_region="regional", freshness_hours=72.0, source_reliability=0.3, is_live=False
    )
    m_est = WeightedMarketPriceEstimator().estimate_market_price([rec], "tomato")
    val = UncertaintyAwareValuationEngine().calculate_valuation(q, m_est)
    assert val.confidence < settings.INSUFFICIENT_CONFIDENCE_THRESHOLD

    detector = PriceQualityAnomalyDetector()
    result = detector.analyze_price_anomaly(val, asking_price=55.0)

    assert result.decision == AnomalyState.INSUFFICIENT_CONFIDENCE
    assert not result.is_confidence_sufficient
    assert result.strategy.confidence_caution is not None


def test_low_price_and_low_quality_triggers_unusually_cheap_warning():
    """Criterion H: Below-fair asking price coupled with decayed produce triggers UNUSUALLY_CHEAP / CHECK_QUALITY."""
    q = QualityEstimate(
        commodity="tomato", quality_score=0.35, freshness_score=0.35, quality_class="Overripe",
        confidence=0.90, uncertainty=0.15, observations_used=["obs-1"], freshness_percent=35
    )
    rec = MarketEvidenceRecord(
        evidence_id="ev-1", source="APMC", commodity="tomato",
        market="Katpadi", state="TN", price_per_kg=30.0, timestamp="2026-10-07",
        distance_or_region="local_exact", freshness_hours=2.0, source_reliability=0.95, is_live=True
    )
    m_est = WeightedMarketPriceEstimator().estimate_market_price([rec], "tomato")
    val = UncertaintyAwareValuationEngine().calculate_valuation(q, m_est)

    detector = PriceQualityAnomalyDetector()
    # Asking price is low (₹15/kg vs fair min of ~₹25)
    result = detector.analyze_price_anomaly(val, asking_price=15.0)

    assert result.decision == AnomalyState.UNUSUALLY_CHEAP
    assert result.recommendation_action == "CHECK_QUALITY"
    assert result.quality_caution is not None


def test_high_price_with_high_confidence_is_overpriced():
    """Criterion I: High asking price with confident narrow fair range is classified as OVERPRICED."""
    q = QualityEstimate(
        commodity="tomato", quality_score=0.90, freshness_score=0.90, quality_class="Fresh",
        confidence=0.95, uncertainty=0.10, observations_used=["obs-1"], freshness_percent=90
    )
    rec = MarketEvidenceRecord(
        evidence_id="ev-1", source="APMC", commodity="tomato",
        market="Katpadi", state="TN", price_per_kg=25.0, timestamp="2026-10-07",
        distance_or_region="local_exact", freshness_hours=2.0, source_reliability=0.95, is_live=True
    )
    m_est = WeightedMarketPriceEstimator().estimate_market_price([rec], "tomato")
    val = UncertaintyAwareValuationEngine().calculate_valuation(q, m_est)

    detector = PriceQualityAnomalyDetector()
    result = detector.analyze_price_anomaly(val, asking_price=60.0)

    assert result.decision == AnomalyState.OVERPRICED
    assert result.recommendation_action == "NEGOTIATE"
    assert result.strategy.potential_saving > 0


# ---------------------------------------------------------------------------
# Test J, K, L: Session Persistence & EVI Math
# ---------------------------------------------------------------------------

def test_missing_market_data_graceful_fallback():
    """Criterion J: System handles empty market evidence records safely with increased uncertainty."""
    estimator = WeightedMarketPriceEstimator()
    est = estimator.estimate_market_price([], "tomato")
    assert est.market_uncertainty >= 0.80
    assert est.confidence <= 0.20


def test_session_state_persistence_across_observations():
    """Criterion K & L: SessionManager preserves full multi-observation history and instrumentation deltas."""
    mgr = SessionManager()
    session = mgr.create_session(commodity="tomato")

    obs1 = Observation(observation_id="o1", observation_index=1, timestamp=datetime.now().isoformat())
    q1 = QualityEstimate(commodity="tomato", quality_score=0.7, freshness_score=0.7, quality_class="Fresh",
                         confidence=0.7, uncertainty=0.45, freshness_percent=70)
    m1 = WeightedMarketPriceEstimator().estimate_market_price([], "tomato")
    val1 = UncertaintyAwareValuationEngine().calculate_valuation(q1, m1)
    ctrl1 = AdaptiveObservationController().evaluate_observation_decision(val1, 1)

    mgr.record_observation_step(session.session_id, obs1, q1, m1, val1, ctrl1)

    obs2 = Observation(observation_id="o2", observation_index=2, timestamp=datetime.now().isoformat())
    q2 = QualityEstimate(commodity="tomato", quality_score=0.8, freshness_score=0.8, quality_class="Fresh",
                         confidence=0.9, uncertainty=0.20, freshness_percent=80)
    val2 = UncertaintyAwareValuationEngine().calculate_valuation(q2, m1)
    ctrl2 = AdaptiveObservationController().evaluate_observation_decision(val2, 2, force_finalize=True)

    mgr.record_observation_step(session.session_id, obs2, q2, m1, val2, ctrl2)

    retrieved = mgr.get_session(session.session_id)
    assert retrieved.observation_count == 2
    assert len(retrieved.observations) == 2
    assert len(retrieved.quality_history) == 2
    assert len(retrieved.valuation_history) == 2
    assert len(retrieved.decision_trace) == 2

    metrics = mgr.get_comparison_metrics(session.session_id)
    assert metrics is not None
    assert metrics["observations_count"] == 2
    assert metrics["deltas"]["uncertainty_reduced"] is True
