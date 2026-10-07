"""
simulation/baselines/b1_fixed_random.py
B1 — Fixed Random Sampling Baseline.
Samples a fixed quota of units (e.g. 15 units across 3 batches of 5)
from accessible material without progressive unstacking/layer removal, then stops.
"""

from typing import List, Set
from simulation.environment.access_graph import AccessGraph, ActionType, InspectionAction
from simulation.environment.dynamics import ObservationYield
from simulation.models.stratum_model import HiddenStratumConditionModel
from simulation.planners.base import BaseInspectionPlanner


class B1FixedRandomSamplingPlanner(BaseInspectionPlanner):
    def __init__(self, target_sample_count: int = 15):
        super().__init__(name="B1_Fixed_Random")
        self.target_sample_count = target_sample_count
        self.samples_collected = 0

    def reset(self) -> None:
        self.samples_collected = 0

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
        if self.samples_collected < self.target_sample_count:
            # Pick currently accessible stratum
            valid_strata = [s for s in accessible_strata if s not in removed_strata]
            if valid_strata:
                target_s = valid_strata[0]
                n_take = min(5, self.target_sample_count - self.samples_collected)
                cost = access_graph.config.cost_sample_unit_base + (n_take * access_graph.config.cost_sample_per_unit)
                if cost <= budget_remaining:
                    self.samples_collected += n_take
                    return InspectionAction(
                        action_type=ActionType.SAMPLE_UNITS,
                        target_stratum=target_s,
                        n_samples=n_take,
                        cost=cost,
                        time_minutes=access_graph.config.time_sample_units,
                        destroys_units=True,
                        provides_immediate_info=True,
                    )

        return InspectionAction(
            action_type=ActionType.STOP_INSPECTION,
            target_stratum=0,
            cost=0.0,
            time_minutes=0.0,
            destroys_units=False,
            provides_immediate_info=False,
        )
