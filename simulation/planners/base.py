"""
simulation/planners/base.py
Abstract Base Class for Inspection Planners and Baselines.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Set
from simulation.environment.access_graph import AccessGraph, InspectionAction
from simulation.environment.dynamics import ObservationYield
from simulation.models.disposition import DispositionDecision, DispositionEvaluator
from simulation.models.stratum_model import HiddenStratumConditionModel


class BaseInspectionPlanner(ABC):
    """
    Common interface for all inspection policies (B0 through B7).
    """

    def __init__(self, name: str, evaluator: Optional[DispositionEvaluator] = None):
        self.name = name
        self.evaluator = evaluator or DispositionEvaluator()

    @abstractmethod
    def reset(self) -> None:
        """Reset internal policy state before starting inspection on a new lot."""
        pass

    @abstractmethod
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
        """Selects the next physical action or STOP_INSPECTION."""
        pass

    def select_disposition(self, belief_model: HiddenStratumConditionModel) -> DispositionDecision:
        """Determines final terminal lot disposition based on current posterior belief."""
        exp_rate = belief_model.whole_lot_expected_defect_rate
        return self.evaluator.select_best_disposition_for_belief(exp_rate)
