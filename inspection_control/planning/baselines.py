"""
inspection_control/planning/baselines.py
Fair Baseline Planners (FB0 through FB6) implemented under the exact same
interface, sensors, action costs, stopping rules, and disposition matrices.
"""

from typing import Tuple, Dict, Any, List, Optional
import copy

from inspection_control.domain.lot import BulkLot
from inspection_control.domain.access_graph import AccessAction, PhysicalActionType
from inspection_control.domain.disposition import DispositionDecision, DispositionLossConfig
from inspection_control.planning.planner import IInspectionPlanner
from inspection_control.planning.exposure_aware_planner import ExposureAwareInspectionPlanner


class FB0SurfaceOnlyPlanner(IInspectionPlanner):
    """FB0: Surface only. Inspects exposed surface stratum 0 once, then terminates."""

    def __init__(self, name: str = "FB0_Surface_Only"):
        self.name = name
        self.has_inspected_surface = False
        self._delegate = ExposureAwareInspectionPlanner(name="delegate")

    def select_next_action(
        self,
        lot: BulkLot,
        remaining_budget_inr: float,
        elapsed_time_sec: float,
        ambient_temp_c: float,
    ) -> Tuple[AccessAction, Dict[str, Any]]:
        candidates = lot.access_graph.get_candidate_actions()
        stop_action = next(a for a in candidates if a.action_type == PhysicalActionType.STOP_INSPECTION)

        if not self.has_inspected_surface:
            obs_s0 = next((a for a in candidates if a.action_type == PhysicalActionType.OBSERVE_STRATUM and a.target_stratum_id == 0), None)
            if obs_s0 and lot.access_graph.is_action_executable(obs_s0):
                self.has_inspected_surface = True
                return obs_s0, {"planner": self.name, "reason": "SURFACE_OBSERVATION"}

        return stop_action, {"planner": self.name, "reason": "SURFACE_ONLY_TERMINATION"}

    def recommend_terminal_disposition(self, lot: BulkLot) -> DispositionDecision:
        return self._delegate.recommend_terminal_disposition(lot)


class FB1FixedRandomPlanner(IInspectionPlanner):
    """FB1: Fixed random sampling across accessible strata up to budget."""

    def __init__(self, sample_budget: int = 3, name: str = "FB1_Fixed_Sampling"):
        self.name = name
        self.sample_budget = sample_budget
        self.samples_taken = 0
        self._delegate = ExposureAwareInspectionPlanner(name="delegate")

    def select_next_action(
        self,
        lot: BulkLot,
        remaining_budget_inr: float,
        elapsed_time_sec: float,
        ambient_temp_c: float,
    ) -> Tuple[AccessAction, Dict[str, Any]]:
        candidates = lot.access_graph.get_candidate_actions()
        stop_action = next(a for a in candidates if a.action_type == PhysicalActionType.STOP_INSPECTION)

        if self.samples_taken < self.sample_budget and remaining_budget_inr >= 15.0:
            sample_act = next((a for a in candidates if a.action_type == PhysicalActionType.SAMPLE_UNITS), None)
            if sample_act and lot.access_graph.is_action_executable(sample_act):
                self.samples_taken += 1
                return sample_act, {"planner": self.name, "reason": f"FIXED_SAMPLE_{self.samples_taken}"}

        return stop_action, {"planner": self.name, "reason": "FIXED_SAMPLE_LIMIT_REACHED"}

    def recommend_terminal_disposition(self, lot: BulkLot) -> DispositionDecision:
        return self._delegate.recommend_terminal_disposition(lot)


class FB2DepthStratifiedPlanner(IInspectionPlanner):
    """FB2: Rigidly unrolls excavation layer by layer across all strata."""

    def __init__(self, max_depth: int = 4, name: str = "FB2_Depth_Stratified"):
        self.name = name
        self.max_depth = max_depth
        self.current_target_stratum = 0
        self.phase = "OBSERVE" # OBSERVE -> EXCAVATE -> OBSERVE
        self._delegate = ExposureAwareInspectionPlanner(name="delegate")

    def select_next_action(
        self,
        lot: BulkLot,
        remaining_budget_inr: float,
        elapsed_time_sec: float,
        ambient_temp_c: float,
    ) -> Tuple[AccessAction, Dict[str, Any]]:
        candidates = lot.access_graph.get_candidate_actions()
        stop_action = next(a for a in candidates if a.action_type == PhysicalActionType.STOP_INSPECTION)

        if remaining_budget_inr < 8.0 or self.current_target_stratum > self.max_depth:
            return stop_action, {"planner": self.name, "reason": "DEPTH_PROTOCOL_COMPLETE"}

        # 1. Observe current stratum
        if self.phase == "OBSERVE":
            obs_act = next((a for a in candidates if a.action_type == PhysicalActionType.OBSERVE_STRATUM and a.target_stratum_id == self.current_target_stratum), None)
            if obs_act and lot.access_graph.is_action_executable(obs_act):
                self.phase = "EXCAVATE"
                return obs_act, {"planner": self.name, "reason": f"STRATIFIED_OBSERVE_S{self.current_target_stratum}"}
            else:
                self.phase = "EXCAVATE"

        # 2. Excavate to next stratum
        next_sid = self.current_target_stratum + 1
        if next_sid <= self.max_depth:
            open_act = next((a for a in candidates if a.action_type in (PhysicalActionType.OPEN_STRATUM, PhysicalActionType.REMOVE_LAYER) and a.target_stratum_id == next_sid), None)
            if open_act and lot.access_graph.is_action_executable(open_act):
                self.current_target_stratum = next_sid
                self.phase = "OBSERVE"
                return open_act, {"planner": self.name, "reason": f"STRATIFIED_EXCAVATE_S{next_sid}"}

        return stop_action, {"planner": self.name, "reason": "DEPTH_PROTOCOL_TERMINATION"}

    def recommend_terminal_disposition(self, lot: BulkLot) -> DispositionDecision:
        return self._delegate.recommend_terminal_disposition(lot)


class FB3MacroMyopicVOIPlanner(IInspectionPlanner):
    """FB3: Myopic VOI that bundles (Open Stratum K + Inspect K) into a macro action."""

    def __init__(self, name: str = "FB3_Macro_Myopic_VOI"):
        self.name = name
        self._delegate = ExposureAwareInspectionPlanner(name="delegate")

    def select_next_action(
        self,
        lot: BulkLot,
        remaining_budget_inr: float,
        elapsed_time_sec: float,
        ambient_temp_c: float,
    ) -> Tuple[AccessAction, Dict[str, Any]]:
        candidates = lot.access_graph.get_candidate_actions()
        stop_action = next(a for a in candidates if a.action_type == PhysicalActionType.STOP_INSPECTION)

        best_act: Optional[AccessAction] = None
        best_score = -999.0

        for act in candidates:
            if not lot.access_graph.is_action_executable(act):
                continue
            if act.action_type == PhysicalActionType.STOP_INSPECTION:
                continue

            sid = act.target_stratum_id
            var = lot.strata[sid].defect_variance if sid in lot.strata else 0.01

            # Simple 1-step VOI
            if act.action_type == PhysicalActionType.OBSERVE_STRATUM:
                score = (var * 1000.0) - act.physical_cost_inr
            elif act.action_type in (PhysicalActionType.OPEN_STRATUM, PhysicalActionType.REMOVE_LAYER):
                # Macro bundling credit: pairs excavation with observation
                score = (var * 1000.0) - (act.physical_cost_inr + 2.0)
            else:
                score = -act.physical_cost_inr

            if score > best_score:
                best_score = score
                best_act = act

        if best_act is None or best_score <= 5.0 or remaining_budget_inr <= 5.0:
            return stop_action, {"planner": self.name, "reason": "STOPPING_CRITERION"}

        return best_act, {"planner": self.name, "reason": "MACRO_MYOPIC_VOI", "score": best_score}

    def recommend_terminal_disposition(self, lot: BulkLot) -> DispositionDecision:
        return self._delegate.recommend_terminal_disposition(lot)


class FB5StateBlindLookaheadPlanner(IInspectionPlanner):
    """
    FB5: Lookahead Planner with physical deterioration and exposure COMPLETELY IGNORED.
    Only cares about informational variance drop minus access financial cost.
    """

    def __init__(self, name: str = "FB5_State_Blind_Lookahead"):
        self.name = name
        self._delegate = ExposureAwareInspectionPlanner(name="delegate")

    def select_next_action(
        self,
        lot: BulkLot,
        remaining_budget_inr: float,
        elapsed_time_sec: float,
        ambient_temp_c: float,
    ) -> Tuple[AccessAction, Dict[str, Any]]:
        candidates = lot.access_graph.get_candidate_actions()
        stop_action = next(a for a in candidates if a.action_type == PhysicalActionType.STOP_INSPECTION)

        best_act: Optional[AccessAction] = None
        best_score = -999.0

        for act in candidates:
            if not lot.access_graph.is_action_executable(act):
                continue
            if act.action_type == PhysicalActionType.STOP_INSPECTION:
                continue

            sid = act.target_stratum_id
            var = lot.strata[sid].defect_variance if sid in lot.strata else 0.01

            # Ignores deterioration/exposure completely (cost = physical labor only)
            info_gain = var * 1200.0
            score = info_gain - act.physical_cost_inr

            if score > best_score:
                best_score = score
                best_act = act

        if best_act is None or best_score <= 4.0 or remaining_budget_inr <= 5.0:
            return stop_action, {"planner": self.name, "reason": "STOPPING_CRITERION"}

        return best_act, {"planner": self.name, "reason": "STATE_BLIND_LOOKAHEAD", "score": best_score}

    def recommend_terminal_disposition(self, lot: BulkLot) -> DispositionDecision:
        return self._delegate.recommend_terminal_disposition(lot)


class FB6AdditiveCostLookaheadPlanner(IInspectionPlanner):
    """
    FB6: Lookahead planner that models exposure ONLY as an additive per-action cost.
    Ignores non-additive history, temperature integrals, repeated openings, and condensation.
    """

    def __init__(self, fixed_exposure_cost_per_sec: float = 0.08, name: str = "FB6_Additive_Cost_Planner"):
        self.name = name
        self.fixed_rate = fixed_exposure_cost_per_sec
        self._delegate = ExposureAwareInspectionPlanner(name="delegate")

    def select_next_action(
        self,
        lot: BulkLot,
        remaining_budget_inr: float,
        elapsed_time_sec: float,
        ambient_temp_c: float,
    ) -> Tuple[AccessAction, Dict[str, Any]]:
        candidates = lot.access_graph.get_candidate_actions()
        stop_action = next(a for a in candidates if a.action_type == PhysicalActionType.STOP_INSPECTION)

        best_act: Optional[AccessAction] = None
        best_score = -999.0

        for act in candidates:
            if not lot.access_graph.is_action_executable(act):
                continue
            if act.action_type == PhysicalActionType.STOP_INSPECTION:
                continue

            sid = act.target_stratum_id
            var = lot.strata[sid].defect_variance if sid in lot.strata else 0.01

            # Additive cost = physical_cost + (duration * fixed_rate)
            additive_exposure_cost = act.duration_sec * self.fixed_rate
            total_cost = act.physical_cost_inr + additive_exposure_cost
            
            info_gain = var * 1200.0
            score = info_gain - total_cost

            if score > best_score:
                best_score = score
                best_act = act

        if best_act is None or best_score <= 4.0 or remaining_budget_inr <= 5.0:
            return stop_action, {"planner": self.name, "reason": "STOPPING_CRITERION"}

        return best_act, {"planner": self.name, "reason": "ADDITIVE_COST_LOOKAHEAD", "score": best_score}

    def recommend_terminal_disposition(self, lot: BulkLot) -> DispositionDecision:
        return self._delegate.recommend_terminal_disposition(lot)
