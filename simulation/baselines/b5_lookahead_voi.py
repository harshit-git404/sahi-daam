"""
simulation/baselines/b5_lookahead_voi.py
B5 — Lookahead Value of Information (VOI) Baseline.
Employs a 2-step lookahead tree search. Recognizes that an enabling action
(REMOVE_LAYER) unlocks high-value future observations, thus escaping the myopic trap.
HOWEVER, it initially ignores physical state changes: it fails to model deterioration,
exposure accumulation, or cross-strata contagion caused by the plan.
"""

from typing import List, Optional, Set, Tuple
from simulation.environment.access_graph import AccessGraph, ActionType, InspectionAction
from simulation.environment.dynamics import ObservationYield
from simulation.models.stratum_model import HiddenStratumConditionModel
from simulation.planners.base import BaseInspectionPlanner


class B5LookaheadVOIPlanner(BaseInspectionPlanner):
    def __init__(self, horizon: int = 2, risk_value_scale: float = 600.0):
        super().__init__(name="B5_Lookahead_VOI")
        self.horizon = horizon
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

        best_first_action: Optional[InspectionAction] = None
        best_net_sequence_value: float = 0.0

        for a1 in valid_actions:
            if a1.action_type == ActionType.STOP_INSPECTION:
                continue

            # Estimate immediate gain of a1
            gain_1 = self._estimate_action_gain(a1, belief_model)
            cost_1 = a1.cost

            # If a1 is enabling action (REMOVE_LAYER), simulate unlocked access state for step 2
            if a1.action_type == ActionType.REMOVE_LAYER:
                sim_removed = set(removed_strata) | {a1.target_stratum}
                sim_acc = set(accessible_strata) | {a1.target_stratum + 1}
                sim_exp = set(exposed_strata) | {a1.target_stratum + 1}

                # Step 2 lookahead
                future_actions = access_graph.get_valid_actions(
                    sim_acc, sim_exp, sim_removed, budget_remaining - cost_1
                )
                best_step2_gain = 0.0
                best_step2_cost = 0.0

                for a2 in future_actions:
                    if a2.action_type != ActionType.STOP_INSPECTION and a2.provides_immediate_info:
                        g2 = self._estimate_action_gain(a2, belief_model)
                        if g2 - a2.cost > best_step2_gain - best_step2_cost:
                            best_step2_gain = g2
                            best_step2_cost = a2.cost

                # Sequence value = combined gain - combined monetary cost
                # NOTE: Ignores physical deterioration or contagion losses!
                seq_value = (gain_1 + best_step2_gain) - (cost_1 + best_step2_cost)
            else:
                seq_value = gain_1 - cost_1

            if seq_value > best_net_sequence_value:
                best_net_sequence_value = seq_value
                best_first_action = a1

        if best_first_action is not None and best_net_sequence_value > 0.0:
            return best_first_action

        return InspectionAction(
            action_type=ActionType.STOP_INSPECTION,
            target_stratum=0,
            cost=0.0,
            time_minutes=0.0,
            destroys_units=False,
            provides_immediate_info=False,
        )

    def _estimate_action_gain(self, action: InspectionAction, belief: HiddenStratumConditionModel) -> float:
        if not action.provides_immediate_info or action.action_type == ActionType.REMOVE_LAYER:
            return 0.0

        target_s = action.target_stratum
        post = belief.posteriors[target_s]
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
        var_reduction = max(0.0, post.variance - new_var) / belief.n_strata
        return float(var_reduction * self.risk_value_scale * 100.0)
