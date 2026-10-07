"""
simulation/baselines/b0_surface.py
B0 — Surface Only Baseline.
Only inspects currently visible surface material (Stratum 0 optical scan),
then immediately stops and commits to lot disposition.
"""

from typing import List, Set
from simulation.environment.access_graph import AccessGraph, ActionType, InspectionAction
from simulation.environment.dynamics import ObservationYield
from simulation.models.stratum_model import HiddenStratumConditionModel
from simulation.planners.base import BaseInspectionPlanner


class B0SurfaceOnlyPlanner(BaseInspectionPlanner):
    def __init__(self):
        super().__init__(name="B0_Surface_Only")
        self.scanned = False

    def reset(self) -> None:
        self.scanned = False

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
        if not self.scanned and 0 in exposed_strata:
            self.scanned = True
            return InspectionAction(
                action_type=ActionType.INSPECT_SURFACE,
                target_stratum=0,
                cost=access_graph.config.cost_surface_inspect,
                time_minutes=access_graph.config.time_surface_inspect,
                destroys_units=False,
                provides_immediate_info=True,
            )
        # Immediately stop
        return InspectionAction(
            action_type=ActionType.STOP_INSPECTION,
            target_stratum=0,
            cost=0.0,
            time_minutes=0.0,
            destroys_units=False,
            provides_immediate_info=False,
        )
