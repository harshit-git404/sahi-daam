"""Simulation and Test Harness for Uncertainty-Driven Adaptive Valuation.

Runs 8 deterministic benchmark scenarios measuring:
- Value of Information (EVI) convergence
- Multi-observation uncertainty reduction
- Market source divergence penalties
- Confidence-gated price-quality anomaly decisions

Outputs both machine-readable JSON and formatted console reports.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.schemas import (
    Observation,
    ObservationView,
    QualityEstimate,
    MarketEvidenceRecord,
    ControllerAction,
    AnomalyState,
)
from quality.estimator import SimulatedQualityEstimator
from market.estimator import WeightedMarketPriceEstimator
from valuation.engine import UncertaintyAwareValuationEngine
from observation.fusion import ObservationFusionEngine
from controller.observation_controller import AdaptiveObservationController
from pricing.anomaly import PriceQualityAnomalyDetector
from session.manager import SessionManager


def run_scenario_1_high_confidence() -> Dict[str, Any]:
    """Scenario 1: High quality image, high confidence -> Controller finalizes immediately."""
    estimator = SimulatedQualityEstimator(fixed_quality=0.90, fixed_confidence=0.94, fixed_disagreement=0.02)
    obs = Observation(observation_id="s1-o1", observation_index=1, image_quality_score=0.95, lighting_score=0.90, timestamp=datetime.now().isoformat())
    q = estimator.estimate_quality(obs, "tomato")
    
    records = [
        MarketEvidenceRecord(evidence_id="e1", source="APMC Local", commodity="tomato", market="Katpadi", state="TN", price_per_kg=25.0, timestamp="2026-10-07", distance_or_region="local_exact", freshness_hours=3.0, source_reliability=0.95, is_live=True),
        MarketEvidenceRecord(evidence_id="e2", source="APMC Regional", commodity="tomato", market="Vellore", state="TN", price_per_kg=26.0, timestamp="2026-10-07", distance_or_region="district", freshness_hours=4.0, source_reliability=0.88, is_live=True),
    ]
    m = WeightedMarketPriceEstimator().estimate_market_price(records, "tomato")
    val = UncertaintyAwareValuationEngine().calculate_valuation(q, m)
    ctrl = AdaptiveObservationController().evaluate_observation_decision(val, 1)

    return {
        "scenario_id": "scenario_1",
        "title": "High Quality Image & Strong Market Agreement",
        "passed": ctrl.decision == ControllerAction.FINALIZE_VALUATION,
        "metrics": {
            "quality_confidence": q.confidence,
            "quality_uncertainty": q.uncertainty,
            "market_uncertainty": m.market_uncertainty,
            "valuation_uncertainty": val.valuation_uncertainty,
            "fair_range": [val.fair_min, val.fair_max],
            "decision": ctrl.decision.value,
            "evi": ctrl.expected_value_of_information,
            "reason": ctrl.reason,
        }
    }


def run_scenario_2_poor_image_requires_second_view() -> Dict[str, Any]:
    """Scenario 2: Low quality image, high visual uncertainty -> Controller requests View 2."""
    estimator = SimulatedQualityEstimator(fixed_quality=0.68, fixed_confidence=0.52, fixed_disagreement=0.28)
    obs = Observation(observation_id="s2-o1", observation_index=1, image_quality_score=0.50, lighting_score=0.45, timestamp=datetime.now().isoformat())
    q = estimator.estimate_quality(obs, "tomato")
    
    records = [
        MarketEvidenceRecord(evidence_id="e1", source="APMC Local", commodity="tomato", market="Katpadi", state="TN", price_per_kg=25.0, timestamp="2026-10-07", distance_or_region="local_exact", freshness_hours=6.0, source_reliability=0.90, is_live=True)
    ]
    m = WeightedMarketPriceEstimator().estimate_market_price(records, "tomato")
    val = UncertaintyAwareValuationEngine().calculate_valuation(q, m)
    ctrl = AdaptiveObservationController().evaluate_observation_decision(val, 1)

    return {
        "scenario_id": "scenario_2",
        "title": "Poor Quality Image / High Uncertainty Request",
        "passed": ctrl.decision == ControllerAction.ACQUIRE_ADDITIONAL_OBSERVATION,
        "metrics": {
            "quality_confidence": q.confidence,
            "quality_uncertainty": q.uncertainty,
            "valuation_uncertainty": val.valuation_uncertainty,
            "decision": ctrl.decision.value,
            "evi": ctrl.expected_value_of_information,
            "requested_view": ctrl.observation_request.requested_view if ctrl.observation_request else None,
            "user_guidance": ctrl.observation_request.user_guidance if ctrl.observation_request else None,
        }
    }


def run_scenario_3_two_agreeing_observations() -> Dict[str, Any]:
    """Scenario 3: Two observations agree closely -> Range narrows and uncertainty reduces."""
    est1 = SimulatedQualityEstimator(fixed_quality=0.76, fixed_confidence=0.68, fixed_disagreement=0.15)
    est2 = SimulatedQualityEstimator(fixed_quality=0.78, fixed_confidence=0.90, fixed_disagreement=0.04)
    obs1 = Observation(observation_id="s3-o1", observation_index=1, view=ObservationView.FRONT, timestamp=datetime.now().isoformat())
    obs2 = Observation(observation_id="s3-o2", observation_index=2, view=ObservationView.REVERSE_SIDE, timestamp=datetime.now().isoformat())
    
    q1 = est1.estimate_quality(obs1, "tomato")
    q2 = est2.estimate_quality(obs2, "tomato")
    q_fused = ObservationFusionEngine().fuse_estimates([q1, q2])

    records = [MarketEvidenceRecord(evidence_id="e1", source="APMC", commodity="tomato", market="Katpadi", state="TN", price_per_kg=28.0, timestamp="2026-10-07", distance_or_region="local_exact", freshness_hours=4.0, source_reliability=0.92, is_live=True)]
    m = WeightedMarketPriceEstimator().estimate_market_price(records, "tomato")
    
    engine = UncertaintyAwareValuationEngine()
    val_before = engine.calculate_valuation(q1, m)
    val_after = engine.calculate_valuation(q_fused, m)

    width_before = val_before.fair_max - val_before.fair_min
    width_after = val_after.fair_max - val_after.fair_min

    return {
        "scenario_id": "scenario_3",
        "title": "Two Agreeing Observations Reduce Range Width",
        "passed": width_after < width_before and val_after.valuation_uncertainty < val_before.valuation_uncertainty,
        "metrics": {
            "before": {"range": [val_before.fair_min, val_before.fair_max], "width": round(width_before, 1), "uncertainty": val_before.valuation_uncertainty},
            "after": {"range": [val_after.fair_min, val_after.fair_max], "width": round(width_after, 1), "uncertainty": val_after.valuation_uncertainty},
            "width_reduction": round(width_before - width_after, 1),
            "uncertainty_reduction": round(val_before.valuation_uncertainty - val_after.valuation_uncertainty, 3),
        }
    }


def run_scenario_4_conflicting_observations() -> Dict[str, Any]:
    """Scenario 4: Two observations disagree sharply (front pristine, back rotted) -> Retains defect & uncertainty."""
    est1 = SimulatedQualityEstimator(fixed_quality=0.88, fixed_confidence=0.85, fixed_disagreement=0.05)
    est2 = SimulatedQualityEstimator(fixed_quality=0.35, fixed_confidence=0.85, fixed_disagreement=0.10)
    q1 = est1.estimate_quality(Observation(observation_id="o1", observation_index=1, timestamp=datetime.now().isoformat()))
    q2 = est2.estimate_quality(Observation(observation_id="o2", observation_index=2, timestamp=datetime.now().isoformat()))
    
    q_fused = ObservationFusionEngine().fuse_estimates([q1, q2])

    return {
        "scenario_id": "scenario_4",
        "title": "Conflicting Views Preserve Defect and Retain Uncertainty",
        "passed": q_fused.quality_score < 0.65 and q_fused.quality_class in ("Slightly Aged", "Overripe"),
        "metrics": {
            "view_1_score": q1.quality_score,
            "view_2_score": q2.quality_score,
            "fused_quality_score": q_fused.quality_score,
            "fused_class": q_fused.quality_class,
            "inter_view_diff": q_fused.details.get("inter_view_max_diff"),
        }
    }


def run_scenario_5_market_disagreement() -> Dict[str, Any]:
    """Scenario 5: Market sources disagree -> Market uncertainty increases."""
    records_split = [
        MarketEvidenceRecord(evidence_id="e1", source="APMC A", commodity="tomato", market="Market A", state="TN", price_per_kg=18.0, timestamp="2026-10-07", distance_or_region="local_exact", freshness_hours=2.0, source_reliability=0.85, is_live=True),
        MarketEvidenceRecord(evidence_id="e2", source="APMC B", commodity="tomato", market="Market B", state="TN", price_per_kg=46.0, timestamp="2026-10-07", distance_or_region="district", freshness_hours=3.0, source_reliability=0.85, is_live=True),
    ]
    records_aligned = [
        MarketEvidenceRecord(evidence_id="e1", source="APMC A", commodity="tomato", market="Market A", state="TN", price_per_kg=24.0, timestamp="2026-10-07", distance_or_region="local_exact", freshness_hours=2.0, source_reliability=0.85, is_live=True),
        MarketEvidenceRecord(evidence_id="e2", source="APMC B", commodity="tomato", market="Market B", state="TN", price_per_kg=25.0, timestamp="2026-10-07", distance_or_region="district", freshness_hours=3.0, source_reliability=0.85, is_live=True),
    ]
    est_split = WeightedMarketPriceEstimator().estimate_market_price(records_split, "tomato")
    est_aligned = WeightedMarketPriceEstimator().estimate_market_price(records_aligned, "tomato")

    return {
        "scenario_id": "scenario_5",
        "title": "Conflicting Market Sources Elevate Market Uncertainty",
        "passed": est_split.market_uncertainty > est_aligned.market_uncertainty,
        "metrics": {
            "aligned_market_uncertainty": est_aligned.market_uncertainty,
            "divergent_market_uncertainty": est_split.market_uncertainty,
            "uncertainty_increase": round(est_split.market_uncertainty - est_aligned.market_uncertainty, 3),
        }
    }


def run_scenario_6_stale_market_data() -> Dict[str, Any]:
    """Scenario 6: Stale data incurs recency penalty lowering reliability."""
    fresh_rec = MarketEvidenceRecord(evidence_id="e1", source="APMC", commodity="tomato", market="Katpadi", state="TN", price_per_kg=25.0, timestamp="2026-10-07", distance_or_region="local_exact", freshness_hours=4.0, is_live=True)
    stale_rec = MarketEvidenceRecord(evidence_id="e2", source="APMC", commodity="tomato", market="Katpadi", state="TN", price_per_kg=25.0, timestamp="2026-10-01", distance_or_region="local_exact", freshness_hours=96.0, is_live=False)

    from market.reliability import MarketReliabilityScorer
    scorer = MarketReliabilityScorer()
    scored = scorer.score_evidence([fresh_rec, stale_rec])

    return {
        "scenario_id": "scenario_6",
        "title": "Stale Market Data Decays Source Reliability",
        "passed": scored[0].source_reliability > scored[1].source_reliability,
        "metrics": {
            "fresh_reliability_4h": scored[0].source_reliability,
            "stale_reliability_96h": scored[1].source_reliability,
        }
    }


def run_scenario_7_overpriced_confident() -> Dict[str, Any]:
    """Scenario 7: High asking price with confident narrow fair range is classified OVERPRICED."""
    q = QualityEstimate(commodity="tomato", quality_score=0.90, freshness_score=0.90, quality_class="Fresh", confidence=0.92, uncertainty=0.12, freshness_percent=90)
    rec = MarketEvidenceRecord(evidence_id="e1", source="APMC", commodity="tomato", market="Katpadi", state="TN", price_per_kg=25.0, timestamp="2026-10-07", distance_or_region="local_exact", freshness_hours=2.0, source_reliability=0.95, is_live=True)
    m = WeightedMarketPriceEstimator().estimate_market_price([rec], "tomato")
    val = UncertaintyAwareValuationEngine().calculate_valuation(q, m)

    res = PriceQualityAnomalyDetector().analyze_price_anomaly(val, asking_price=55.0)

    return {
        "scenario_id": "scenario_7",
        "title": "High Asking Price with Confident Valuation is Overpriced",
        "passed": res.decision == AnomalyState.OVERPRICED and res.recommendation_action == "NEGOTIATE",
        "metrics": {
            "asking_price": 55.0,
            "fair_range": [val.fair_min, val.fair_max],
            "deviation_pct": res.deviation_pct,
            "potential_saving": res.strategy.potential_saving,
        }
    }


def run_scenario_8_uncertain_valuation_withholds_overpriced() -> Dict[str, Any]:
    """Scenario 8: High asking price with high uncertainty outputs INSUFFICIENT_CONFIDENCE."""
    q = QualityEstimate(commodity="tomato", quality_score=0.65, freshness_score=0.65, quality_class="Fresh", confidence=0.40, uncertainty=0.65, freshness_percent=65)
    rec = MarketEvidenceRecord(evidence_id="e1", source="Legacy", commodity="tomato", market="Unknown", state="TN", price_per_kg=25.0, timestamp="2026-10-01", distance_or_region="regional", freshness_hours=80.0, source_reliability=0.30, is_live=False)
    m = WeightedMarketPriceEstimator().estimate_market_price([rec], "tomato")
    val = UncertaintyAwareValuationEngine().calculate_valuation(q, m)

    res = PriceQualityAnomalyDetector().analyze_price_anomaly(val, asking_price=55.0)

    return {
        "scenario_id": "scenario_8",
        "title": "High Uncertainty Guard Withholds Overpriced Assertion",
        "passed": res.decision == AnomalyState.INSUFFICIENT_CONFIDENCE and not res.is_confidence_sufficient,
        "metrics": {
            "confidence": val.confidence,
            "valuation_uncertainty": val.valuation_uncertainty,
            "decision": res.decision.value,
            "caution": res.strategy.confidence_caution,
        }
    }


def run_all_scenarios() -> Dict[str, Any]:
    scenarios = [
        run_scenario_1_high_confidence(),
        run_scenario_2_poor_image_requires_second_view(),
        run_scenario_3_two_agreeing_observations(),
        run_scenario_4_conflicting_observations(),
        run_scenario_5_market_disagreement(),
        run_scenario_6_stale_market_data(),
        run_scenario_7_overpriced_confident(),
        run_scenario_8_uncertain_valuation_withholds_overpriced(),
    ]
    all_passed = all(s["passed"] for s in scenarios)
    return {
        "timestamp": datetime.now().isoformat(),
        "total_scenarios": len(scenarios),
        "all_passed": all_passed,
        "scenarios": scenarios,
    }


if __name__ == "__main__":
    report = run_all_scenarios()
    print("=" * 70)
    print("SAHI DAAM - ADAPTIVE VALUATION SIMULATION HARNESS")
    print(f"Timestamp: {report['timestamp']}")
    print(f"Status: {'ALL SCENARIOS PASSED (8/8)' if report['all_passed'] else 'SCENARIOS FAILED'}")
    print("=" * 70)
    for s in report["scenarios"]:
        status_tag = "PASSED" if s["passed"] else "FAILED"
        print(f"[{status_tag}] {s['scenario_id']}: {s['title']}")
        for k, v in s["metrics"].items():
            print(f"    - {k}: {v}")
        print("-" * 70)
    
    # Save machine-readable output
    out_path = Path(__file__).resolve().parent.parent / "docs" / "simulation_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Machine-readable results saved to: {out_path}")
