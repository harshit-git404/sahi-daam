"""Valuation Session State Manager.

Maintains multi-observation state, historical quality revisions, valuation adjustments,
and explainable decision traces across active user sessions.
"""

import uuid
from datetime import datetime
from typing import Dict, Optional, List, Any
import threading

from core.schemas import (
    ValuationSession,
    Observation,
    QualityEstimate,
    WeightedMarketPriceEstimate,
    ValuationResult,
    ControllerDecision,
    FairPriceRange,
)


class SessionManager:
    """Thread-safe in-memory storage for active valuation sessions."""

    def __init__(self):
        self._sessions: Dict[str, ValuationSession] = {}
        self._lock = threading.Lock()

    def create_session(
        self,
        commodity: str = "tomato",
        max_observations: int = 3,
        session_id: Optional[str] = None
    ) -> ValuationSession:
        sid = session_id or f"val-{uuid.uuid4().hex[:10]}"
        now_iso = datetime.now().isoformat()

        session = ValuationSession(
            session_id=sid,
            commodity=commodity.lower().strip(),
            status="ACTIVE",
            observation_count=0,
            max_observations=max_observations,
            observations=[],
            quality_history=[],
            valuation_history=[],
            controller_history=[],
            decision_trace=[],
            created_at=now_iso,
            updated_at=now_iso,
        )

        with self._lock:
            self._sessions[sid] = session

        return session

    def get_session(self, session_id: str) -> Optional[ValuationSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def record_observation_step(
        self,
        session_id: str,
        observation: Observation,
        quality_estimate: QualityEstimate,
        market_estimate: WeightedMarketPriceEstimate,
        valuation: ValuationResult,
        controller_decision: ControllerDecision,
    ) -> ValuationSession:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise KeyError(f"Valuation session '{session_id}' not found.")

            session.observations.append(observation)
            session.observation_count = len(session.observations)
            session.quality_history.append(quality_estimate)
            session.valuation_history.append(valuation)
            session.controller_history.append(controller_decision)

            session.current_quality_estimate = quality_estimate
            session.current_quality_uncertainty = quality_estimate.uncertainty
            session.current_market_estimate = market_estimate
            session.current_market_uncertainty = market_estimate.market_uncertainty
            session.current_valuation = valuation
            session.current_fair_range = FairPriceRange(
                min=valuation.fair_min,
                max=valuation.fair_max,
                unit="kg"
            )
            session.current_valuation_uncertainty = valuation.valuation_uncertainty
            session.latest_decision = controller_decision

            # Build structured step trace for patent figures & debugging
            step_record = {
                "step_index": session.observation_count,
                "timestamp": datetime.now().isoformat(),
                "observation_id": observation.observation_id,
                "view": observation.view.value,
                "quality_score": quality_estimate.quality_score,
                "quality_confidence": quality_estimate.confidence,
                "quality_uncertainty": quality_estimate.uncertainty,
                "market_price": market_estimate.estimated_price_per_kg,
                "market_uncertainty": market_estimate.market_uncertainty,
                "quality_adjustment": valuation.quality_adjustment.adjustment_per_kg,
                "fair_min": valuation.fair_min,
                "fair_max": valuation.fair_max,
                "range_width": round(valuation.fair_max - valuation.fair_min, 1),
                "valuation_uncertainty": valuation.valuation_uncertainty,
                "valuation_confidence": valuation.confidence,
                "evi": controller_decision.expected_value_of_information,
                "action": controller_decision.decision.value,
                "action_reason": controller_decision.reason,
            }
            session.decision_trace.append(step_record)

            if controller_decision.decision.value == "FINALIZE_VALUATION":
                session.status = "FINALIZED"

            session.updated_at = datetime.now().isoformat()
            return session

    def get_comparison_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Returns instrumentation comparing Step 1 vs Final Step metrics."""
        session = self.get_session(session_id)
        if not session or len(session.valuation_history) == 0:
            return None

        first_val = session.valuation_history[0]
        latest_val = session.valuation_history[-1]

        first_width = round(first_val.fair_max - first_val.fair_min, 1)
        latest_width = round(latest_val.fair_max - latest_val.fair_min, 1)

        width_delta = round(latest_width - first_width, 1)
        unc_delta = round(latest_val.valuation_uncertainty - first_val.valuation_uncertainty, 3)
        conf_delta = round(latest_val.confidence - first_val.confidence, 3)

        return {
            "session_id": session_id,
            "observations_count": session.observation_count,
            "before": {
                "fair_range": [first_val.fair_min, first_val.fair_max],
                "range_width": first_width,
                "quality_uncertainty": first_val.quality_estimate.uncertainty,
                "quality_confidence": first_val.quality_estimate.confidence,
                "valuation_uncertainty": first_val.valuation_uncertainty,
                "valuation_confidence": first_val.confidence,
            },
            "after": {
                "fair_range": [latest_val.fair_min, latest_val.fair_max],
                "range_width": latest_width,
                "quality_uncertainty": latest_val.quality_estimate.uncertainty,
                "quality_confidence": latest_val.quality_estimate.confidence,
                "valuation_uncertainty": latest_val.valuation_uncertainty,
                "valuation_confidence": latest_val.confidence,
            },
            "deltas": {
                "range_width_change": width_delta,
                "uncertainty_reduction": round(-1.0 * unc_delta, 3),
                "confidence_gain": conf_delta,
                "uncertainty_reduced": unc_delta < 0,
            }
        }


# Global session manager singleton
session_manager = SessionManager()
