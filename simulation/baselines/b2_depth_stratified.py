"""
simulation/baselines/b2_depth_stratified.py
B2 — Depth-Stratified Sampling Baseline.
Enforces a rigid, predefined multi-stratum sampling plan:
Unpacks layers sequentially and samples a fixed quota (e.g. 5 units) at each depth,
regardless of what condition is observed or state-alteration costs incurred.
"""

from typing import List, Set
from simulation.environment.access_graph import AccessGraph, ActionType, InspectionAction
from simulation.environment.dynamics import ObservationYield
from simulation.models.stratum_model import HiddenStratumConditionModel
from simulation.planners.base import BaseInspectionPlanner


class B2DepthStratifiedSamplingPlanner(BaseInspectionPlanner):
    def __init__(self, target_depth: int = 3, samples_per_depth: int = 5):
        super().__init__(name="B2_Depth_Stratified")
        self.target_depth = target_depth
        self.samples_per_depth = samples_per_depth
        self.current_depth = 0
        self.sampled_at_current_depth = False

    def reset(self) -> None:
        self.current_depth = 0
        self.sampled_at_current_depth = False

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
        while self.current_depth < self.target_depth:
            # Check if current depth is accessible
            if self.current_depth in accessible_strata and self.current_depth not in removed_strata:
                if not self.sampled_at_current_depth:
                    # Sample at this depth
                    cost = access_graph.config.cost_sample_unit_base + (self.samples_per_depth * access_graph.config.cost_sample_per_unit)
                    if cost <= budget_remaining:
                        self.sampled_at_current_depth = True
                        return InspectionAction(
                            action_type=ActionType.SAMPLE_UNITS,
                            target_stratum=self.current_depth,
                            n_samples=self.samples_per_depth,
                            cost=cost,
                            time_minutes=access_graph.config.time_sample_units,
                            destroys_units=True,
                            provides_immediate_info=True,
                        )
                    else:
                        break  # Budget exhausted
                else:
                    # Already sampled here, remove layer to unlock next depth
                    cost = access_graph.config.cost_remove_layer
                    if cost <= budget_remaining:
                        self.sampled_at_current_depth = False
                        action = InspectionAction(
                            action_type=ActionType.REMOVE_LAYER,
                            target_stratum=self.current_depth,
                            cost=cost,
                            time_minutes=access_graph.config.time_remove_layer,
                            destroys_units=False,
                            provides_immediate_info=False,
                        )
                        self.current_depth += 1
                        return action
                    else:
                        break  # Budget exhausted
            else:
                self.current_depth += 1

        return InspectionAction(
            action_type=ActionType.STOP_INSPECTION,
            target_stratum=0,
            cost=0.0,
            time_minutes=0.0,
            destroys_units=False,
            provides_immediate_info=False,
        )
