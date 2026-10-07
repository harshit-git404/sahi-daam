"""
inspection_control/domain/access_graph.py
Precedence-constrained physical access graph for multi-strata bulk lots.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Optional


class PhysicalActionType(str, Enum):
    OBSERVE_STRATUM = "OBSERVE_STRATUM"
    OPEN_STRATUM = "OPEN_STRATUM"
    REMOVE_LAYER = "REMOVE_LAYER"
    SAMPLE_UNITS = "SAMPLE_UNITS"
    WAIT_SETTLE = "WAIT_SETTLE"
    CLOSE_REDUCE_EXPOSURE = "CLOSE_REDUCE_EXPOSURE"
    STOP_INSPECTION = "STOP_INSPECTION"


@dataclass
class AccessAction:
    """
    Physical action descriptor defining operational constraints and impacts.
    """
    action_type: PhysicalActionType
    target_stratum_id: int
    name: str
    duration_sec: float
    physical_cost_inr: float
    exposure_impact_factor: float
    mechanical_disturbance: float
    prerequisite_strata_unlocked: List[int] = field(default_factory=list)
    resulting_accessible_strata: List[int] = field(default_factory=list)
    unlocked_observation_strata: List[int] = field(default_factory=list)


class AccessGraph:
    """
    Maintains dynamic physical precedence constraints for inspecting
    a stacked lot of strata (e.g. tabletop tray stack S0..S4).
    """

    def __init__(self, n_strata: int = 5):
        self.n_strata = n_strata
        # Currently accessible strata (can be observed or sampled)
        self.accessible_strata: Set[int] = {0}  # Stratum 0 (surface) accessible initially
        # Strata currently exposed to ambient air
        self.open_strata: Set[int] = {0}
        # Precedence prerequisites: to open stratum k, layer k-1 must be removed
        self.prerequisites: Dict[int, List[int]] = {
            i: [i - 1] for i in range(1, n_strata)
        }
        self.prerequisites[0] = []

    def is_action_executable(self, action: AccessAction) -> bool:
        """Verify whether physical constraints allow this action in current state."""
        if action.action_type == PhysicalActionType.STOP_INSPECTION:
            return True
            
        if action.action_type == PhysicalActionType.OBSERVE_STRATUM:
            # Can only observe if stratum is currently accessible and open
            return (action.target_stratum_id in self.accessible_strata and 
                    action.target_stratum_id in self.open_strata)
            
        if action.action_type == PhysicalActionType.SAMPLE_UNITS:
            return action.target_stratum_id in self.accessible_strata

        if action.action_type in (PhysicalActionType.OPEN_STRATUM, PhysicalActionType.REMOVE_LAYER):
            # Target stratum prerequisites must be satisfied
            needed = self.prerequisites.get(action.target_stratum_id, [])
            for req in needed:
                if req not in self.accessible_strata:
                    return False
            return True

        if action.action_type == PhysicalActionType.WAIT_SETTLE:
            return True

        if action.action_type == PhysicalActionType.CLOSE_REDUCE_EXPOSURE:
            # Can only close if something is open
            return len(self.open_strata) > 0

        return False

    def execute_action(self, action: AccessAction) -> None:
        """Transition physical access state upon executing action."""
        if action.action_type in (PhysicalActionType.OPEN_STRATUM, PhysicalActionType.REMOVE_LAYER):
            self.accessible_strata.add(action.target_stratum_id)
            self.open_strata.add(action.target_stratum_id)
            for unlocked in action.resulting_accessible_strata:
                self.accessible_strata.add(unlocked)
                self.open_strata.add(unlocked)

        elif action.action_type == PhysicalActionType.CLOSE_REDUCE_EXPOSURE:
            # Re-cover opened strata
            self.open_strata.clear()

    def get_candidate_actions(self) -> List[AccessAction]:
        """Generate all physically valid actions at the current state."""
        candidates: List[AccessAction] = []
        
        # 1. Observe any currently accessible and open stratum
        for sid in sorted(self.accessible_strata):
            if sid in self.open_strata:
                candidates.append(AccessAction(
                    action_type=PhysicalActionType.OBSERVE_STRATUM,
                    target_stratum_id=sid,
                    name=f"Inspect Exposed Stratum S{sid}",
                    duration_sec=5.0,
                    physical_cost_inr=2.0,
                    exposure_impact_factor=1.0,
                    mechanical_disturbance=0.0,
                    unlocked_observation_strata=[sid],
                ))

        # 2. Open / Remove layer for next unopened stratum
        for sid in range(1, self.n_strata):
            if sid not in self.accessible_strata:
                # Check prerequisites
                needed = self.prerequisites.get(sid, [])
                if all(req in self.accessible_strata for req in needed):
                    candidates.append(AccessAction(
                        action_type=PhysicalActionType.REMOVE_LAYER,
                        target_stratum_id=sid,
                        name=f"Remove Tray / Excavate to Stratum S{sid}",
                        duration_sec=15.0,
                        physical_cost_inr=8.0,
                        exposure_impact_factor=2.0,
                        mechanical_disturbance=0.25,
                        resulting_accessible_strata=[sid],
                        unlocked_observation_strata=[sid],
                    ))

        # 3. Sample destructive physical unit from accessible strata
        for sid in sorted(self.accessible_strata):
            candidates.append(AccessAction(
                action_type=PhysicalActionType.SAMPLE_UNITS,
                target_stratum_id=sid,
                name=f"Sample Core Unit from S{sid} (Destructive Cut/Brix)",
                duration_sec=25.0,
                physical_cost_inr=15.0,
                exposure_impact_factor=1.5,
                mechanical_disturbance=0.1,
            ))

        # 4. Wait / Settle (allows camera auto-focus, thermal acclimation)
        candidates.append(AccessAction(
            action_type=PhysicalActionType.WAIT_SETTLE,
            target_stratum_id=0,
            name="Wait / Thermal Acclimation Settle (10s)",
            duration_sec=10.0,
            physical_cost_inr=0.5,
            exposure_impact_factor=1.0,
            mechanical_disturbance=0.0,
        ))

        # 5. Close / Reduce exposure
        if len(self.open_strata) > 0:
            candidates.append(AccessAction(
                action_type=PhysicalActionType.CLOSE_REDUCE_EXPOSURE,
                target_stratum_id=0,
                name="Close / Re-cover Open Strata (Thermal Blanket)",
                duration_sec=8.0,
                physical_cost_inr=3.0,
                exposure_impact_factor=0.2,
                mechanical_disturbance=0.05,
            ))

        # 6. Stop inspection and make terminal disposition
        candidates.append(AccessAction(
            action_type=PhysicalActionType.STOP_INSPECTION,
            target_stratum_id=0,
            name="Stop Inspection & Commit Terminal Disposition",
            duration_sec=0.0,
            physical_cost_inr=0.0,
            exposure_impact_factor=0.0,
            mechanical_disturbance=0.0,
        ))

        return candidates
