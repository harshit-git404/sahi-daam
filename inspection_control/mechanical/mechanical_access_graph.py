"""
inspection_control/mechanical/mechanical_access_graph.py
Physical Access Graph with Mechanical State-Altering Actions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Optional


class MechActionType(str, Enum):
    OBSERVE = "OBSERVE"
    REMOVE = "REMOVE"
    HOLD = "HOLD"
    RECONFIGURE = "RECONFIGURE"
    RECLOSE = "RECLOSE"
    STOP = "STOP"


@dataclass
class MechAction:
    action_type: MechActionType
    target_stratum_id: int
    name: str
    duration_sec: float
    physical_cost_inr: float
    mechanical_disturbance: float
    unlocked_strata: List[int] = field(default_factory=list)


class MechanicalAccessGraph:
    """
    Manages physical access precedence and allowable actions for a 5-stratum stack.
    """

    def __init__(self, n_strata: int = 5):
        self.n_strata = n_strata
        self.accessible_strata: Set[int] = {0}
        self.open_strata: Set[int] = {0}
        self.removed_strata: Set[int] = set()

    def get_candidate_actions(self) -> List[MechAction]:
        actions: List[MechAction] = []

        # STOP is always valid
        actions.append(MechAction(
            action_type=MechActionType.STOP,
            target_stratum_id=-1,
            name="STOP_INSPECTION",
            duration_sec=0.0,
            physical_cost_inr=0.0,
            mechanical_disturbance=0.0,
        ))

        # OBSERVE accessible open strata
        for sid in sorted(self.accessible_strata):
            if sid in self.open_strata and sid not in self.removed_strata:
                actions.append(MechAction(
                    action_type=MechActionType.OBSERVE,
                    target_stratum_id=sid,
                    name=f"OBSERVE_S{sid}",
                    duration_sec=4.0,
                    physical_cost_inr=5.0,
                    mechanical_disturbance=0.05,
                ))

        # REMOVE accessible stratum to expose layer underneath
        for sid in sorted(self.accessible_strata):
            if sid not in self.removed_strata and sid < self.n_strata - 1:
                actions.append(MechAction(
                    action_type=MechActionType.REMOVE,
                    target_stratum_id=sid,
                    name=f"REMOVE_S{sid}",
                    duration_sec=8.0,
                    physical_cost_inr=12.0,
                    mechanical_disturbance=0.60,
                    unlocked_strata=[sid + 1],
                ))

        # HOLD / RELAX (allows viscoelastic creep or recovery to settle)
        if len(self.open_strata) > 0:
            actions.append(MechAction(
                action_type=MechActionType.HOLD,
                target_stratum_id=-1,
                name="HOLD_SETTLE",
                duration_sec=10.0,
                physical_cost_inr=2.0,
                mechanical_disturbance=0.0,
            ))

        # RECONFIGURE (manual gentle leveling)
        if len(self.open_strata) > 0:
            actions.append(MechAction(
                action_type=MechActionType.RECONFIGURE,
                target_stratum_id=-1,
                name="RECONFIGURE_STACK",
                duration_sec=6.0,
                physical_cost_inr=6.0,
                mechanical_disturbance=0.25,
            ))

        return actions

    def execute_action(self, action: MechAction) -> None:
        if action.action_type == MechActionType.REMOVE:
            sid = action.target_stratum_id
            self.removed_strata.add(sid)
            self.open_strata.discard(sid)
            for nxt in action.unlocked_strata:
                self.accessible_strata.add(nxt)
                self.open_strata.add(nxt)

        elif action.action_type == MechActionType.RECLOSE:
            self.open_strata.clear()

        elif action.action_type == MechActionType.HOLD:
            pass

        elif action.action_type == MechActionType.RECONFIGURE:
            pass
