"""
inspection_control/planning/planner.py
Abstract base interface for physical inspection planners.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, List

from inspection_control.domain.lot import BulkLot
from inspection_control.domain.access_graph import AccessAction
from inspection_control.domain.disposition import DispositionDecision


class IInspectionPlanner(ABC):
    """Abstract controller selecting next physical action or stopping decision."""

    @abstractmethod
    def select_next_action(
        self,
        lot: BulkLot,
        remaining_budget_inr: float,
        elapsed_time_sec: float,
        ambient_temp_c: float,
    ) -> Tuple[AccessAction, Dict[str, Any]]:
        """
        Returns (chosen_action, decision_telemetry_dict).
        MUST NOT ACCESS lot.get_ground_truth_for_teardown().
        """
        pass

    @abstractmethod
    def recommend_terminal_disposition(self, lot: BulkLot) -> DispositionDecision:
        """Recommend terminal disposition (ACCEPT, MARKDOWN, REJECT, REROUTE, SPLIT)."""
        pass
