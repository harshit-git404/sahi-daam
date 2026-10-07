"""
simulation/environment/access_graph.py
Precedence-Constrained Physical Access Graph for Bulk Lots.

Defines allowable physical actions, execution prerequisites, immediate
informational yields, labor costs, and state unlocking transitions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class ActionType(str, Enum):
    INSPECT_SURFACE = "inspect_surface"      # Optical scan of exposed stratum surface
    REMOVE_LAYER = "remove_layer"            # ENABLING ACTION: removes stratum k to expose k+1 (Zero immediate info!)
    SAMPLE_UNITS = "sample_units"            # Draw n physical units from accessible stratum (destructive)
    SECONDARY_SENSOR = "secondary_sensor"    # High-accuracy optical/chemical/NIR probe on accessible stratum
    STOP_INSPECTION = "stop_inspection"      # Conclude inspection and commit to lot disposition


@dataclass(frozen=True)
class InspectionAction:
    action_type: ActionType
    target_stratum: int
    n_samples: int = 0                       # Applicable for SAMPLE_UNITS
    cost: float = 0.0                        # Monetary / resource cost (INR)
    time_minutes: float = 1.0                # Duration of action
    destroys_units: bool = False             # Does this action consume lot material?
    provides_immediate_info: bool = True     # False for enabling actions like REMOVE_LAYER

    def __str__(self) -> str:
        if self.action_type == ActionType.REMOVE_LAYER:
            return f"REMOVE_LAYER(Stratum {self.target_stratum} -> unlocks {self.target_stratum + 1})"
        elif self.action_type == ActionType.SAMPLE_UNITS:
            return f"SAMPLE_UNITS(Stratum {self.target_stratum}, n={self.n_samples})"
        elif self.action_type == ActionType.INSPECT_SURFACE:
            return f"INSPECT_SURFACE(Stratum {self.target_stratum})"
        elif self.action_type == ActionType.SECONDARY_SENSOR:
            return f"SECONDARY_SENSOR(Stratum {self.target_stratum})"
        elif self.action_type == ActionType.STOP_INSPECTION:
            return "STOP_INSPECTION"
        return f"{self.action_type.value}({self.target_stratum})"


@dataclass
class AccessGraphConfig:
    cost_surface_inspect: float = 5.0
    cost_remove_layer: float = 25.0          # Enabling action cost
    cost_sample_unit_base: float = 10.0      # Base sampling cost
    cost_sample_per_unit: float = 2.0        # Additional cost per unit sampled
    cost_secondary_sensor: float = 35.0      # Specialized probe cost
    time_surface_inspect: float = 1.0        # Minutes
    time_remove_layer: float = 4.0           # Minutes
    time_sample_units: float = 2.0           # Minutes
    time_secondary_sensor: float = 3.0       # Minutes


class AccessGraph:
    """
    Maintains the directed precedence graph of physical access for a bulk lot.
    Enforces that deep strata cannot be observed or sampled without prior removal actions.
    """

    def __init__(self, n_strata: int = 5, config: Optional[AccessGraphConfig] = None):
        self.n_strata = n_strata
        self.config = config or AccessGraphConfig()

    def get_valid_actions(
        self,
        accessible_strata: Set[int],
        exposed_strata: Set[int],
        removed_strata: Set[int],
        budget_remaining: float = float("inf"),
    ) -> List[InspectionAction]:
        """
        Returns all physically permissible actions given current lot configuration.
        """
        cfg = self.config
        actions: List[InspectionAction] = []

        # 1. Optical surface inspection of currently exposed strata
        for s in exposed_strata:
            if s not in removed_strata:
                act = InspectionAction(
                    action_type=ActionType.INSPECT_SURFACE,
                    target_stratum=s,
                    cost=cfg.cost_surface_inspect,
                    time_minutes=cfg.time_surface_inspect,
                    destroys_units=False,
                    provides_immediate_info=True,
                )
                if act.cost <= budget_remaining:
                    actions.append(act)

        # 2. Physical unit sampling on accessible strata
        for s in accessible_strata:
            if s not in removed_strata:
                for n_s in [3, 5]:  # Standard sample batch sizes
                    cost = cfg.cost_sample_unit_base + (n_s * cfg.cost_sample_per_unit)
                    act = InspectionAction(
                        action_type=ActionType.SAMPLE_UNITS,
                        target_stratum=s,
                        n_samples=n_s,
                        cost=cost,
                        time_minutes=cfg.time_sample_units,
                        destroys_units=True,
                        provides_immediate_info=True,
                    )
                    if act.cost <= budget_remaining:
                        actions.append(act)

        # 3. Secondary sensor probe on accessible strata
        for s in accessible_strata:
            if s not in removed_strata:
                act = InspectionAction(
                    action_type=ActionType.SECONDARY_SENSOR,
                    target_stratum=s,
                    cost=cfg.cost_secondary_sensor,
                    time_minutes=cfg.time_secondary_sensor,
                    destroys_units=False,
                    provides_immediate_info=True,
                )
                if act.cost <= budget_remaining:
                    actions.append(act)

        # 4. ENABLING ACTION: Remove stratum layer k to unlock stratum k+1
        # Precedence constraint: can only remove layer k if layer k is currently top accessible
        for s in range(self.n_strata - 1):
            if s in accessible_strata and s not in removed_strata:
                # Can remove layer s if all preceding layers 0..(s-1) are already removed
                prereqs_met = all(prev in removed_strata for prev in range(s))
                if prereqs_met:
                    act = InspectionAction(
                        action_type=ActionType.REMOVE_LAYER,
                        target_stratum=s,
                        cost=cfg.cost_remove_layer,
                        time_minutes=cfg.time_remove_layer,
                        destroys_units=False,
                        provides_immediate_info=False,  # CRITICAL: ZERO immediate observation!
                    )
                    if act.cost <= budget_remaining:
                        actions.append(act)

        # 5. Always can choose to STOP inspection
        actions.append(
            InspectionAction(
                action_type=ActionType.STOP_INSPECTION,
                target_stratum=0,
                cost=0.0,
                time_minutes=0.0,
                destroys_units=False,
                provides_immediate_info=False,
            )
        )

        return actions

    def unlock_strata_on_removal(self, removed_stratum: int) -> Tuple[int, int]:
        """
        When layer k is removed, stratum k+1 becomes exposed and accessible.
        Returns: (newly_exposed_stratum, newly_accessible_stratum)
        """
        next_s = removed_stratum + 1
        return (next_s, next_s)
