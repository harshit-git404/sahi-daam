"""
simulation/baselines/b3_sahi_daam.py
B3 — Current Sahi Daam-Style Heuristic Baseline.
Emulates the single-lot quality/uncertainty feedback logic:
Scans surface first; if quality uncertainty is elevated (> threshold),
requests a secondary observation (sensor probe or surface unit sample) on the visible area.
Crucially, it lacks concepts of hidden strata, layer excavation, or state alterations.
"""

from typing import List, Set
from simulation.environment.access_graph import AccessGraph, ActionType, InspectionAction
from simulation.environment.dynamics import ObservationYield
from simulation.models.stratum_model import HiddenStratumConditionModel
from simulation.planners.base import BaseInspectionPlanner


class B3SahiDaamHeuristicPlanner(BaseInspectionPlanner):
    def __init__(self, uncertainty_threshold: float = 0.28):
        super().__init__(name="B3_Sahi_Daam_Heuristic")
        self.uncertainty_threshold = uncertainty_threshold
        self.has_scanned_surface = False
        self.has_taken_secondary_view = False

    def reset(self) -> None:
        self.has_scanned_surface = False
        self.has_taken_secondary_view = False

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
        cfg = access_graph.config

        # Step 1: Initial surface inspection
        if not self.has_scanned_surface and 0 in exposed_strata:
            self.has_scanned_surface = True
            if cfg.cost_surface_inspect <= budget_remaining:
                return InspectionAction(
                    action_type=ActionType.INSPECT_SURFACE,
                    target_stratum=0,
                    cost=cfg.cost_surface_inspect,
                    time_minutes=cfg.time_surface_inspect,
                    destroys_units=False,
                    provides_immediate_info=True,
                )

        # Step 2: Adaptive observation trigger (Sahi Daam EVI / uncertainty style)
        if self.has_scanned_surface and not self.has_taken_secondary_view:
            current_unc = belief_model.posteriors[0].uncertainty
            if current_unc > self.uncertainty_threshold:
                self.has_taken_secondary_view = True
                # Request secondary sensor on surface if affordable, else sample 3 units
                if cfg.cost_secondary_sensor <= budget_remaining:
                    return InspectionAction(
                        action_type=ActionType.SECONDARY_SENSOR,
                        target_stratum=0,
                        cost=cfg.cost_secondary_sensor,
                        time_minutes=cfg.time_secondary_sensor,
                        destroys_units=False,
                        provides_immediate_info=True,
                    )
                else:
                    sample_cost = cfg.cost_sample_unit_base + (3 * cfg.cost_sample_per_unit)
                    if sample_cost <= budget_remaining:
                        return InspectionAction(
                            action_type=ActionType.SAMPLE_UNITS,
                            target_stratum=0,
                            n_samples=3,
                            cost=sample_cost,
                            time_minutes=cfg.time_sample_units,
                            destroys_units=True,
                            provides_immediate_info=True,
                        )

        # Step 3: Conclude
        return InspectionAction(
            action_type=ActionType.STOP_INSPECTION,
            target_stratum=0,
            cost=0.0,
            time_minutes=0.0,
            destroys_units=False,
            provides_immediate_info=False,
        )
