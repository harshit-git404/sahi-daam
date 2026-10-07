"""
simulation/baselines/b6_access_aware.py
B6 — Access-Aware Planner Baseline.
Respects precedence constraints of physical access and models future observation
availability and downstream disposition loss reduction.
However, it ignores physical state alterations (no modelling of inspection-induced
deterioration, thermal exposure accumulation, or cross-strata contagion).
"""

from typing import List, Optional, Set
import numpy as np

from simulation.environment.access_graph import AccessGraph, ActionType, InspectionAction
from simulation.environment.dynamics import ObservationYield
from simulation.models.disposition import DispositionDecision, DispositionEvaluator
from simulation.models.stratum_model import HiddenStratumConditionModel
from simulation.planners.base import BaseInspectionPlanner


class B6AccessAwarePlanner(BaseInspectionPlanner):
    def __init__(self, evaluator: Optional[DispositionEvaluator] = None, horizon: int = 2):
        super().__init__(name="B6_Access_Aware", evaluator=evaluator)
        self.horizon = horizon

    def reset(self) -> None:
        pass

    def select_action(
        self,
        accessible_strata: Set[int],
        exposed_strata: Set[int],
        removed_strata: Set[int],
        history: List[ObservationYield],
        belief_model: HiddenStratumConditionModel,
        access_graph: AccessGraph,
        budget_remaining: float,
        step_idx: int,
    ) -> InspectionAction:
        valid_actions = access_graph.get_valid_actions(
            accessible_strata, exposed_strata, removed_strata, budget_remaining
        )

        current_loss = self._expected_disposition_loss(belief_model)
        best_first_action: Optional[InspectionAction] = None
        best_net_benefit: float = 0.0

        for a1 in valid_actions:
            if a1.action_type == ActionType.STOP_INSPECTION:
                continue

            cost_1 = a1.cost

            if a1.action_type == ActionType.REMOVE_LAYER:
                # Enabling action: lookahead to observation enabled at newly accessible layer
                sim_removed = set(removed_strata) | {a1.target_stratum}
                sim_acc = set(accessible_strata) | {a1.target_stratum + 1}
                sim_exp = set(exposed_strata) | {a1.target_stratum + 1}

                future_actions = access_graph.get_valid_actions(
                    sim_acc, sim_exp, sim_removed, budget_remaining - cost_1
                )
                best_seq_benefit = 0.0

                for a2 in future_actions:
                    if a2.action_type != ActionType.STOP_INSPECTION and a2.provides_immediate_info:
                        # Simulate posterior after a2
                        sim_belief = belief_model.clone()
                        self._simulate_belief_update(sim_belief, a2)
                        post_loss = self._expected_disposition_loss(sim_belief)
                        loss_reduction = max(0.0, current_loss - post_loss)
                        # Considers loss reduction minus monetary inspection costs, but NO deterioration!
                        net = loss_reduction - (cost_1 + a2.cost)
                        if net > best_seq_benefit:
                            best_seq_benefit = net

                if best_seq_benefit > best_net_benefit:
                    best_net_benefit = best_seq_benefit
                    best_first_action = a1

            else:
                sim_belief = belief_model.clone()
                self._simulate_belief_update(sim_belief, a1)
                post_loss = self._expected_disposition_loss(sim_belief)
                loss_reduction = max(0.0, current_loss - post_loss)
                net = loss_reduction - cost_1
                if net > best_net_benefit:
                    best_net_benefit = net
                    best_first_action = a1

        if best_first_action is not None and best_net_benefit > 5.0:  # Marginal threshold
            return best_first_action

        return InspectionAction(
            action_type=ActionType.STOP_INSPECTION,
            target_stratum=0,
            cost=0.0,
            time_minutes=0.0,
            destroys_units=False,
            provides_immediate_info=False,
        )

    def _expected_disposition_loss(self, belief: HiddenStratumConditionModel) -> float:
        rate = belief.whole_lot_expected_defect_rate
        unc = belief.whole_lot_uncertainty
        # Approximate risk: if near decision boundary (0.08 or 0.22), uncertainty incurs high expected misclassification loss
        cfg = self.evaluator.config
        dist_to_boundary = min(abs(rate - cfg.tolerance_threshold_accept), abs(rate - cfg.tolerance_threshold_markdown))
        misclassification_prob = float(np.clip(unc / (dist_to_boundary + 0.05), 0.05, 0.50))
        return misclassification_prob * 1800.0

    def _simulate_belief_update(self, belief: HiddenStratumConditionModel, action: InspectionAction) -> None:
        s = action.target_stratum
        post = belief.posteriors[s]
        if action.action_type == ActionType.SAMPLE_UNITS:
            n = action.n_samples
            k = int(np.round(post.mean * n))
            belief.update_from_unit_samples(s, k, n)
        elif action.action_type == ActionType.INSPECT_SURFACE:
            belief.update_from_sensor_scan(s, post.mean, 0.07 ** 2)
        elif action.action_type == ActionType.SECONDARY_SENSOR:
            belief.update_from_sensor_scan(s, post.mean, 0.02 ** 2)
