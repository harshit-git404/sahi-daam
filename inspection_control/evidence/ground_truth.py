"""
inspection_control/evidence/ground_truth.py
Post-Inspection Ground-Truth Teardown Protocol and Performance Evaluation.
Strictly executed AFTER the inspection controller terminates.
"""

from typing import Dict, Any, List
from inspection_control.domain.lot import BulkLot
from inspection_control.domain.disposition import DispositionDecision, DispositionEvaluator


class GroundTruthTeardownEvaluator:
    """
    Simulates complete post-inspection teardown and grading of all units
    to establish unbiased ground-truth performance metrics.
    """

    def __init__(self, evaluator: DispositionEvaluator = DispositionEvaluator()):
        self.evaluator = evaluator

    def evaluate_completed_lot(
        self,
        lot: BulkLot,
        chosen_disposition: DispositionDecision,
        total_inspection_cost_inr: float,
        cumulative_exposure_time_sec: float,
        planner_name: str,
    ) -> Dict[str, Any]:
        # Access the private ground-truth container ONLY during teardown
        gt = lot.get_ground_truth_for_teardown()
        true_overall_defect_rate = gt.overall_true_defect_rate

        # Estimate deterioration loss caused by inspection exposure
        # Produce spoilage penalty = ₹0.05 per exposed second * open strata
        deterioration_loss_inr = cumulative_exposure_time_sec * 0.04

        loss_eval = self.evaluator.evaluate_loss(
            decision=chosen_disposition,
            true_lot_defect_rate=true_overall_defect_rate,
            inspection_cost_inr=total_inspection_cost_inr,
            deterioration_loss_inr=deterioration_loss_inr,
        )

        # Residual defect risk: absolute difference between estimated lot rate and true rate
        mu_estimated, _ = (
            sum(s.unit_count * s.expected_defect_rate for s in lot.strata.values()) / max(1, sum(s.unit_count for s in lot.strata.values())),
            0.0
        )
        residual_risk = abs(mu_estimated - true_overall_defect_rate)

        strata_defect_breakdown = {
            sid: round(data.true_defect_rate, 4)
            for sid, data in gt.strata_ground_truth.items()
        }

        return {
            "lot_id": lot.lot_id,
            "planner": planner_name,
            "commodity": lot.commodity,
            "pattern": lot.pattern.value,
            "true_overall_defect_rate": round(true_overall_defect_rate, 4),
            "estimated_defect_rate": round(mu_estimated, 4),
            "residual_risk": round(residual_risk, 4),
            "chosen_disposition": chosen_disposition.value,
            "is_false_accept": loss_eval["is_false_accept"],
            "is_false_reject": loss_eval["is_false_reject"],
            "is_correct": loss_eval["is_correct"],
            "disposition_penalty": round(loss_eval["disposition_penalty"], 2),
            "inspection_cost": round(loss_eval["inspection_cost"], 2),
            "deterioration_loss": round(loss_eval["deterioration_loss"], 2),
            "total_disposition_loss": round(loss_eval["total_disposition_loss"], 2),
            "cumulative_exposure_sec": round(cumulative_exposure_time_sec, 2),
            "strata_defect_breakdown": strata_defect_breakdown,
        }
