"""
simulation/baselines/b4_myopic_voi.py
B4 — Myopic Value of Information (VOI) Baseline.
Greedily evaluates single-step candidate actions by their immediate information gain.
Crucially falls into the 'myopic trap': because REMOVE_LAYER yields zero immediate
observation (Gain = 0), its myopic VOI is strictly negative (-cost), so B4 never
chooses an enabling action.
"""

from typing import List, Set
import numpy as np

from simulation.environment.access_graph import AccessGraph, ActionType, InspectionAction
from simulation.environment.dynamics import ObservationYield
from simulation.models.stratum_model import HiddenStratumConditionModel
from simulation.planners.base import BaseInspectionPlanner


class B4MyopicVOIPlanner(BaseInspectionPlanner):
    def __init__(self, risk_value_scale: float = 600.0):
        super().__init__(name="B4_Myopic_VOI")
        self.risk_value_scale = risk_value_scale

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

        current_variance = belief_model.whole_lot_variance
        best_action: Optional[InspectionAction] = None
        best_net_voi: float = 0.0  # Must exceed 0 to justify action over stopping

        for action in valid_actions:
            if action.action_type == ActionType.STOP_INSPECTION:
                continue

            # ENABLING ACTION CHECK: Immediate information is ZERO
            if not action.provides_immediate_info or action.action_type == ActionType.REMOVE_LAYER:
                immediate_gain = 0.0
                net_voi = immediate_gain - action.cost  # Strictly negative
            else:
                # Approximate expected posterior variance reduction on target stratum
                target_s = action.target_stratum
                post = belief_model.posteriors[target_s]
                ab = post.alpha + post.beta

                if action.action_type == ActionType.SAMPLE_UNITS:
                    effective_n = action.n_samples
                elif action.action_type == ActionType.INSPECT_SURFACE:
                    effective_n = 5.0
                elif action.action_type == ActionType.SECONDARY_SENSOR:
                    effective_n = 15.0
                else:
                    effective_n = 1.0

                new_ab = ab + effective_n
                new_var = (post.alpha * post.beta) / (new_ab * new_ab * (new_ab + 1.0))
                var_reduction = max(0.0, post.variance - new_var) / belief_model.n_strata

                immediate_value = var_reduction * self.risk_value_scale * 100.0
                net_voi = immediate_value - action.cost

            if net_voi > best_net_voi:
                best_net_voi = net_voi
                best_action = action

        if best_action is not None and best_net_voi > 0.0:
            return best_action

        return InspectionAction(
            action_type=ActionType.STOP_INSPECTION,
            target_stratum=0,
            cost=0.0,
            time_minutes=0.0,
            destroys_units=False,
            provides_immediate_info=False,
        )
