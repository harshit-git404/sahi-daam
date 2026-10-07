"""
inspection_control/planning/exposure_aware_planner.py
FB7: Proposed History-Dependent, Exposure-Aware Inspection Controller.
Evaluates non-additive environmental coupling, future observation fidelity,
and downstream disposition loss.
"""

from typing import Tuple, Dict, Any, List, Optional
import math
import numpy as np

from inspection_control.domain.lot import BulkLot
from inspection_control.domain.access_graph import AccessAction, PhysicalActionType
from inspection_control.domain.disposition import DispositionDecision, DispositionLossConfig
from inspection_control.domain.exposure_state import ExposureStage
from inspection_control.dynamics.exposure_model import NonAdditiveExposureModel
from inspection_control.dynamics.observation_quality_model import ObservationQualityModel
from inspection_control.estimation.posterior import BayesianStratumConditionModel
from inspection_control.planning.planner import IInspectionPlanner


class ExposureAwareInspectionPlanner(IInspectionPlanner):
    """
    FB7: Receding-horizon controller incorporating non-additive exposure ledger,
    state-altering inspection dynamics, and downstream disposition risk.
    """

    def __init__(
        self,
        name: str = "FB7_Exposure_Aware_Planner",
        loss_config: DispositionLossConfig = DispositionLossConfig(),
        exposure_model: Optional[NonAdditiveExposureModel] = None,
        quality_model: Optional[ObservationQualityModel] = None,
        condition_model: Optional[BayesianStratumConditionModel] = None,
        risk_stopping_tolerance: float = 0.02,
        action_horizon: int = 2,
    ):
        self.name = name
        self.loss_config = loss_config
        self.exposure_model = exposure_model or NonAdditiveExposureModel()
        self.quality_model = quality_model or ObservationQualityModel()
        self.condition_model = condition_model or BayesianStratumConditionModel()
        self.risk_stopping_tolerance = risk_stopping_tolerance
        self.action_horizon = action_horizon

    def select_next_action(
        self,
        lot: BulkLot,
        remaining_budget_inr: float,
        elapsed_time_sec: float,
        ambient_temp_c: float,
    ) -> Tuple[AccessAction, Dict[str, Any]]:
        # Compute current downstream disposition risk
        current_loss = self._evaluate_current_expected_loss(lot)
        candidates = lot.access_graph.get_candidate_actions()

        best_action: Optional[AccessAction] = None
        best_net_benefit: float = -float("inf")
        action_scores: List[Dict[str, Any]] = []

        # Find default STOP action
        stop_action = next((a for a in candidates if a.action_type == PhysicalActionType.STOP_INSPECTION), candidates[-1])

        # If budget exhausted, stop
        if remaining_budget_inr <= 2.0:
            return stop_action, {
                "planner": self.name,
                "reason": "BUDGET_EXHAUSTED",
                "current_expected_loss": current_loss,
                "chosen_action": stop_action.name,
            }

        for action in candidates:
            if not lot.access_graph.is_action_executable(action):
                continue

            if action.action_type == PhysicalActionType.STOP_INSPECTION:
                continue

            score_data = self._score_action(
                action=action,
                lot=lot,
                current_expected_loss=current_loss,
                ambient_temp_c=ambient_temp_c,
                remaining_budget=remaining_budget_inr,
            )
            action_scores.append(score_data)

            net_benefit = score_data["net_benefit_inr"]
            if net_benefit > best_net_benefit:
                best_net_benefit = net_benefit
                best_action = action

        # If best action does not overcome stopping hurdle, stop
        if best_action is None or best_net_benefit <= self.risk_stopping_tolerance:
            return stop_action, {
                "planner": self.name,
                "reason": "RISK_REDUCTION_BELOW_COST",
                "current_expected_loss": current_loss,
                "best_net_benefit": best_net_benefit,
                "action_scores": action_scores,
                "chosen_action": stop_action.name,
            }

        return best_action, {
            "planner": self.name,
            "reason": "OPTIMAL_EXPECTED_BENEFIT",
            "current_expected_loss": current_loss,
            "chosen_action": best_action.name,
            "expected_benefit_inr": best_net_benefit,
            "action_scores": action_scores,
        }

    def _score_action(
        self,
        action: AccessAction,
        lot: BulkLot,
        current_expected_loss: float,
        ambient_temp_c: float,
        remaining_budget: float,
    ) -> Dict[str, Any]:
        target_sid = action.target_stratum_id
        stratum = lot.strata.get(target_sid)
        stratum_temp = stratum.temperature_history[-1] if (stratum and stratum.temperature_history) else 14.0

        # 1. Direct physical cost
        cost_inr = action.physical_cost_inr
        if cost_inr > remaining_budget:
            return {"action": action.name, "net_benefit_inr": -999.0, "reason": "OVER_BUDGET"}

        # 2. History-dependent non-additive exposure impact
        record = lot.exposure_ledger.strata_records.get(target_sid)
        marginal_exposure = 0.0
        if record:
            marginal_exposure = self.exposure_model.compute_marginal_exposure_impact(
                record=record,
                action_duration_sec=action.duration_sec,
                ambient_temp_c=ambient_temp_c,
                stratum_temp_c=stratum_temp,
                is_opening_action=(action.action_type in (PhysicalActionType.OPEN_STRATUM, PhysicalActionType.REMOVE_LAYER)),
            )

        # Deterioration economic loss
        deterioration_cost_inr = marginal_exposure * self.loss_config.base_lot_value * 2.5

        # 3. Informational value & Risk Reduction
        expected_risk_reduction = 0.0

        if action.action_type == PhysicalActionType.OBSERVE_STRATUM:
            # Observation fidelity depends on exposure history
            elapsed_access = record.time_since_access_sec if record else 10.0
            fid = self.quality_model.evaluate_observation_fidelity(
                elapsed_since_access_sec=elapsed_access,
                core_temp_c=stratum_temp,
                ambient_temp_c=ambient_temp_c,
                times_opened=record.times_opened if record else 1,
            )
            # Variance reduction from observing N units with fidelity fid.fidelity_score
            var_current = stratum.defect_variance if stratum else 0.01
            # Expected variance drop
            post_n = (stratum.belief_alpha + stratum.belief_beta) + (15.0 * fid.fidelity_score) if stratum else 25.0
            var_new = (stratum.belief_alpha * stratum.belief_beta) / ((post_n ** 2) * (post_n + 1)) if stratum else 0.005
            var_drop = max(0.0, var_current - var_new)
            
            # Risk reduction is proportional to variance drop * false accept cost
            expected_risk_reduction = var_drop * self.loss_config.cost_false_accept * 12.0

        elif action.action_type in (PhysicalActionType.OPEN_STRATUM, PhysicalActionType.REMOVE_LAYER):
            # ENABLING ACTION: Provides zero immediate observation, but unlocks subsequent observation!
            # Compute option value of the unlocked stratum observation
            unlocked_sid = action.resulting_accessible_strata[0] if action.resulting_accessible_strata else target_sid
            unlocked_stratum = lot.strata.get(unlocked_sid)
            if unlocked_stratum:
                var_unlocked = unlocked_stratum.defect_variance
                # Option value is future risk reduction of inspecting unlocked layer
                expected_risk_reduction = var_unlocked * self.loss_config.cost_false_accept * 9.0

        elif action.action_type == PhysicalActionType.SAMPLE_UNITS:
            # High precision destructive observation
            var_current = stratum.defect_variance if stratum else 0.01
            expected_risk_reduction = var_current * 0.75 * self.loss_config.cost_false_accept * 14.0

        elif action.action_type == PhysicalActionType.CLOSE_REDUCE_EXPOSURE:
            # Closes strata: saves deterioration cost on open strata
            open_count = len(lot.access_graph.open_strata)
            expected_risk_reduction = open_count * 12.0  # Saved thermal spoilage

        elif action.action_type == PhysicalActionType.WAIT_SETTLE:
            # Improves camera settling for upcoming observation
            expected_risk_reduction = 4.0

        net_benefit = expected_risk_reduction - (cost_inr + deterioration_cost_inr)

        return {
            "action": action.name,
            "cost_inr": cost_inr,
            "deterioration_cost_inr": round(deterioration_cost_inr, 2),
            "expected_risk_reduction_inr": round(expected_risk_reduction, 2),
            "net_benefit_inr": round(net_benefit, 2),
        }

    def _evaluate_current_expected_loss(self, lot: BulkLot) -> float:
        mu_defect, sigma_defect = self.condition_model.get_lot_aggregate_distribution(lot.strata)
        cfg = self.loss_config

        p_exceeds_accept = self.condition_model.probability_lot_defect_exceeds(lot.strata, cfg.threshold_accept)
        p_exceeds_markdown = self.condition_model.probability_lot_defect_exceeds(lot.strata, cfg.threshold_markdown)

        # Expected false accept loss if we were to accept now
        loss_if_accept = p_exceeds_accept * cfg.cost_false_accept
        # Expected loss if we markdown now
        loss_if_markdown = (1.0 - p_exceeds_accept) * cfg.cost_false_markdown + p_exceeds_markdown * cfg.cost_under_markdown
        # Expected loss if we reject now
        loss_if_reject = (1.0 - p_exceeds_markdown) * cfg.cost_false_reject

        return min(loss_if_accept, loss_if_markdown, loss_if_reject)

    def recommend_terminal_disposition(self, lot: BulkLot) -> DispositionDecision:
        cfg = self.loss_config
        p_exceeds_accept = self.condition_model.probability_lot_defect_exceeds(lot.strata, cfg.threshold_accept)
        p_exceeds_markdown = self.condition_model.probability_lot_defect_exceeds(lot.strata, cfg.threshold_markdown)
        p_exceeds_reroute = self.condition_model.probability_lot_defect_exceeds(lot.strata, cfg.threshold_reroute)

        # Check if upper strata are clean but lower strata are defective (candidate for SPLIT_LOT)
        s0_rate = lot.strata[0].expected_defect_rate
        lower_rates = [s.expected_defect_rate for sid, s in lot.strata.items() if sid >= 2]
        mean_lower = sum(lower_rates) / len(lower_rates) if lower_rates else s0_rate

        if s0_rate <= cfg.threshold_accept and mean_lower > cfg.threshold_markdown and len(lot.strata) >= 3:
            return DispositionDecision.SPLIT_LOT

        if p_exceeds_accept < 0.15:
            return DispositionDecision.ACCEPT
        elif p_exceeds_markdown < 0.35:
            return DispositionDecision.MARKDOWN
        elif p_exceeds_reroute < 0.50:
            return DispositionDecision.REROUTE
        else:
            return DispositionDecision.REJECT
