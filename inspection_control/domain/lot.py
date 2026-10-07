"""
inspection_control/domain/lot.py
Physical Bulk Perishable Lot Representation.
Enforces strict architectural isolation between the public inspection state
and the private ground-truth state (for teardown validation only).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import copy
import numpy as np

from inspection_control.domain.stratum import StratumState
from inspection_control.domain.exposure_state import ExposureLedger
from inspection_control.domain.access_graph import AccessGraph


class DefectPatternType(str, Enum):
    UNIFORM = "UNIFORM"
    DEPTH_CORRELATED = "DEPTH_CORRELATED"
    HIDDEN_BOTTOM = "HIDDEN_BOTTOM"
    CLUSTERED = "CLUSTERED"
    SURFACE_BIASED = "SURFACE_BIASED"
    ADVERSARIAL = "ADVERSARIAL"
    BENIGN = "BENIGN"


@dataclass
class GroundTruthStratumData:
    """Hidden ground truth data available ONLY during teardown evaluation."""
    stratum_id: int
    units_defective: int
    units_total: int
    true_defect_rate: float
    defect_types: List[str] = field(default_factory=list)


@dataclass
class GroundTruthLotContainer:
    """Container for post-inspection ground-truth teardown validation."""
    lot_id: str
    commodity: str
    pattern: DefectPatternType
    strata_ground_truth: Dict[int, GroundTruthStratumData] = field(default_factory=dict)

    @property
    def overall_true_defect_rate(self) -> float:
        total_units = sum(s.units_total for s in self.strata_ground_truth.values())
        total_defective = sum(s.units_defective for s in self.strata_ground_truth.values())
        return total_defective / total_units if total_units > 0 else 0.0


class BulkLot:
    """
    Physical inspection lot. The controller interacts ONLY with public strata,
    the exposure ledger, and the access graph.
    """

    def __init__(
        self,
        lot_id: str,
        commodity: str = "potato",
        n_strata: int = 5,
        units_per_stratum: int = 50,
        pattern: DefectPatternType = DefectPatternType.DEPTH_CORRELATED,
        initial_temp_c: float = 12.0,
        rng: Optional[np.random.Generator] = None,
    ):
        self.lot_id = lot_id
        self.commodity = commodity
        self.n_strata = n_strata
        self.units_per_stratum = units_per_stratum
        self.pattern = pattern
        self._rng = rng or np.random.default_rng(42)

        # Public observable state
        self.strata: Dict[int, StratumState] = {}
        for i in range(n_strata):
            self.strata[i] = StratumState(
                stratum_id=i,
                name=f"Stratum {i} ({'Surface' if i == 0 else f'Depth {i * 15}cm'})",
                unit_count=units_per_stratum,
                physical_depth=i * 0.15,
                accessibility=(i == 0),
                access_prerequisites=[i - 1] if i > 0 else [],
                temperature_history=[initial_temp_c],
                humidity_history=[85.0],
                is_open=(i == 0),
            )

        self.exposure_ledger = ExposureLedger(lot_id=lot_id)
        self.exposure_ledger.initialize_strata(list(range(n_strata)))
        self.access_graph = AccessGraph(n_strata=n_strata)

        # Strictly private ground truth (inaccessible to controller)
        self._private_ground_truth = self._generate_ground_truth(initial_temp_c)

    def _generate_ground_truth(self, initial_temp: float) -> GroundTruthLotContainer:
        gt = GroundTruthLotContainer(
            lot_id=self.lot_id,
            commodity=self.commodity,
            pattern=self.pattern,
        )

        for i in range(self.n_strata):
            if self.pattern == DefectPatternType.BENIGN:
                rate = float(self._rng.uniform(0.01, 0.04))
            elif self.pattern == DefectPatternType.UNIFORM:
                rate = float(self._rng.uniform(0.12, 0.18))
            elif self.pattern == DefectPatternType.DEPTH_CORRELATED:
                # Top is clean, bottom is rotting
                rate = float(0.02 + 0.08 * i + self._rng.uniform(0.0, 0.05))
            elif self.pattern == DefectPatternType.HIDDEN_BOTTOM:
                rate = 0.03 if i < (self.n_strata - 1) else float(self._rng.uniform(0.40, 0.65))
            elif self.pattern == DefectPatternType.ADVERSARIAL:
                # Surface meticulously clean (1%), deeper layers heavily decayed (35% - 55%)
                rate = 0.01 if i == 0 else float(self._rng.uniform(0.30, 0.55))
            elif self.pattern == DefectPatternType.SURFACE_BIASED:
                rate = 0.03 if i <= 1 else float(self._rng.uniform(0.20, 0.35))
            elif self.pattern == DefectPatternType.CLUSTERED:
                rate = float(self._rng.uniform(0.45, 0.70)) if i in (2, 3) else 0.04
            else:
                rate = 0.10

            rate = float(np.clip(rate, 0.0, 1.0))
            defective_count = int(np.round(rate * self.units_per_stratum))
            
            gt.strata_ground_truth[i] = GroundTruthStratumData(
                stratum_id=i,
                units_defective=defective_count,
                units_total=self.units_per_stratum,
                true_defect_rate=rate,
                defect_types=["soft_rot", "internal_browning"] if rate > 0.15 else ["skin_scuff"],
            )
        return gt

    def get_ground_truth_for_teardown(self) -> GroundTruthLotContainer:
        """
        TEARDOWN ONLY: Returns ground truth after inspection is concluded.
        Must NOT be called by any planner/controller during inspection!
        """
        return self._private_ground_truth

    def clone_for_counterfactual(self) -> "BulkLot":
        """Deep copy for paired benchmark comparisons on identical lots."""
        return copy.deepcopy(self)
