"""
simulation/environment/lot.py
Physical Bulk Perishable Lot Environment.

Represents a bulk perishable container (e.g., crate/pallet of potatoes or onions)
structured into physical strata with hidden condition distributions, spatial
clustering, exposure states, and contagion dynamics.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import numpy as np


class DefectPattern(str, Enum):
    UNIFORM = "uniform"
    DEPTH_CORRELATED = "depth_correlated"
    CLUSTERED = "clustered"
    HIDDEN_BOTTOM = "hidden_bottom"
    SUPPLIER_DEPENDENT = "supplier_dependent"
    SURFACE_BIASED = "surface_biased"
    ADVERSARIAL = "adversarial"


class PresentationBias(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ADVERSARIAL = "adversarial"


@dataclass
class StratumState:
    stratum_id: int
    name: str
    n_units: int
    qualities: np.ndarray  # float array [0.0, 1.0], values < 0.5 are defective
    temperature: float = 20.0  # Celsius
    exposure_level: float = 0.0  # Cumulative ambient exposure (hours or index)
    contagion_load: float = 0.0  # Active pathogen/decay pressure [0.0, 1.0]
    is_accessible: bool = False  # Can units currently be sampled directly?
    is_exposed: bool = False  # Is surface visible to optical sensors?
    sampled_indices: List[int] = field(default_factory=list)
    surface_observed: bool = False

    @property
    def defect_mask(self) -> np.ndarray:
        return self.qualities < 0.5

    @property
    def defect_prevalence(self) -> float:
        if len(self.qualities) == 0:
            return 0.0
        return float(np.mean(self.defect_mask))

    @property
    def mean_quality(self) -> float:
        if len(self.qualities) == 0:
            return 1.0
        return float(np.mean(self.qualities))

    @property
    def remaining_units(self) -> int:
        return self.n_units - len(self.sampled_indices)


@dataclass
class LotConfig:
    n_strata: int = 5
    units_per_stratum: int = 100
    defect_pattern: DefectPattern = DefectPattern.DEPTH_CORRELATED
    presentation_bias: PresentationBias = PresentationBias.MEDIUM
    base_defect_rate: float = 0.20
    ambient_temp: float = 24.0
    contagion_transmission_rate: float = 0.08  # Spread per unit time/exposure
    deterioration_rate: float = 0.03  # Quality degradation per unit exposure
    commodity_name: str = "Potato"


class BulkPerishableLot:
    """
    Physical simulation of a bulk perishable lot.
    Units are indexed across strata: 0 (top/exposed) to N-1 (deepest/bottom).
    """

    def __init__(self, config: Optional[LotConfig] = None, rng: Optional[np.random.Generator] = None):
        self.config = config or LotConfig()
        self.rng = rng or np.random.default_rng(42)
        self.strata: Dict[int, StratumState] = {}
        self.elapsed_time: float = 0.0  # Total inspection duration
        self.total_exposure_accumulated: float = 0.0
        self.units_destroyed: int = 0
        self._initialize_lot()

    def _initialize_lot(self) -> None:
        cfg = self.config
        pattern = cfg.defect_pattern
        bias = cfg.presentation_bias

        # Calculate target defect prevalence per stratum based on pattern and bias
        target_prevalences = self._compute_target_prevalences(cfg.n_strata, pattern, bias, cfg.base_defect_rate)

        for s_id in range(cfg.n_strata):
            name = (
                "surface" if s_id == 0 else
                "near_surface" if s_id == 1 else
                "middle" if s_id == 2 else
                "deep" if s_id == 3 else
                f"stratum_{s_id}"
            )
            target_p = target_prevalences[s_id]

            # Generate individual unit qualities
            qualities = self._generate_stratum_qualities(
                cfg.units_per_stratum, target_p, pattern, s_id
            )

            # Initially: only stratum 0 is accessible and exposed
            is_acc = (s_id == 0)
            is_exp = (s_id == 0)

            # Initial contagion load proportional to defect count
            init_contagion = float(np.mean(qualities < 0.5) * 0.4)

            self.strata[s_id] = StratumState(
                stratum_id=s_id,
                name=name,
                n_units=cfg.units_per_stratum,
                qualities=qualities,
                temperature=cfg.ambient_temp - (s_id * 0.5),  # Core slightly cooler initially
                exposure_level=1.0 if s_id == 0 else 0.0,
                contagion_load=init_contagion,
                is_accessible=is_acc,
                is_exposed=is_exp,
            )

    def _compute_target_prevalences(
        self, n_strata: int, pattern: DefectPattern, bias: PresentationBias, base_rate: float
    ) -> List[float]:
        rates = []
        if pattern == DefectPattern.UNIFORM:
            rates = [base_rate] * n_strata

        elif pattern == DefectPattern.DEPTH_CORRELATED:
            # Defect increases monotonically with depth
            for s in range(n_strata):
                depth_frac = s / max(1, n_strata - 1)
                r = base_rate * (0.3 + 1.4 * depth_frac)
                rates.append(float(np.clip(r, 0.01, 0.95)))

        elif pattern == DefectPattern.HIDDEN_BOTTOM:
            # Clean on top, severe rot hidden at bottom
            for s in range(n_strata):
                if s < n_strata - 2:
                    rates.append(0.04)  # 4% clean
                else:
                    rates.append(base_rate * 2.5)  # Heavy rotting deep

        elif pattern == DefectPattern.CLUSTERED:
            # Pockets of decay in specific strata (e.g. middle strata 2 and 3)
            for s in range(n_strata):
                if s in [2, 3]:
                    rates.append(float(min(0.85, base_rate * 2.2)))
                else:
                    rates.append(float(base_rate * 0.5))

        elif pattern == DefectPattern.SUPPLIER_DEPENDENT:
            # Random supplier quality profile
            var = self.rng.uniform(-0.10, 0.15)
            effective_base = float(np.clip(base_rate + var, 0.05, 0.85))
            rates = [float(np.clip(effective_base + (s * 0.04), 0.02, 0.95)) for s in range(n_strata)]

        elif pattern == DefectPattern.SURFACE_BIASED:
            # Surface is naturally sorted or aerated
            rates.append(max(0.02, base_rate * 0.4))
            for s in range(1, n_strata):
                rates.append(float(min(0.90, base_rate * (1.0 + 0.2 * s))))

        elif pattern == DefectPattern.ADVERSARIAL:
            # Top layer cherry-picked to 0-3% defect, all hidden layers 35-70% defect
            rates.append(0.02)
            for s in range(1, n_strata):
                rates.append(float(min(0.95, base_rate * (1.8 + 0.3 * s))))

        # Apply presentation bias multiplier to surface vs hidden
        if bias == PresentationBias.LOW:
            pass  # Keep as-is
        elif bias == PresentationBias.MEDIUM:
            rates[0] = max(0.01, rates[0] * 0.8)
        elif bias == PresentationBias.HIGH:
            rates[0] = max(0.01, rates[0] * 0.4)
            for s in range(1, n_strata):
                rates[s] = min(0.95, rates[s] * 1.25)
        elif bias == PresentationBias.ADVERSARIAL:
            rates[0] = 0.01  # Near pristine surface
            for s in range(1, n_strata):
                rates[s] = min(0.95, max(0.35, rates[s] * 1.5))

        return [float(np.clip(r, 0.005, 0.98)) for r in rates]

    def _generate_stratum_qualities(
        self, n_units: int, defect_rate: float, pattern: DefectPattern, stratum_id: int
    ) -> np.ndarray:
        # Generates continuous qualities in [0, 1].
        # Defective units have quality < 0.5 (mean ~0.28), good units have quality >= 0.5 (mean ~0.84).
        n_defects = int(np.round(n_units * defect_rate))
        n_good = n_units - n_defects

        defective_q = self.rng.beta(2.5, 7.0, size=n_defects) * 0.49  # [0.0, 0.49]
        good_q = 0.50 + self.rng.beta(7.0, 2.5, size=n_good) * 0.49    # [0.50, 0.99]

        all_q = np.concatenate([defective_q, good_q])

        # If clustered pattern, place defects in contiguous spatial blocks
        if pattern == DefectPattern.CLUSTERED and n_defects > 0:
            cluster_start = self.rng.integers(0, max(1, n_units - n_defects))
            shuffled = np.ones(n_units) * 0.85
            # Insert defects in block
            shuffled[cluster_start : cluster_start + n_defects] = defective_q
            # Fill remaining with good
            good_idx = [i for i in range(n_units) if not (cluster_start <= i < cluster_start + n_defects)]
            shuffled[good_idx] = good_q[:len(good_idx)]
            return np.clip(shuffled, 0.01, 0.99)

        self.rng.shuffle(all_q)
        return np.clip(all_q, 0.01, 0.99)

    @property
    def total_units(self) -> int:
        return sum(s.n_units for s in self.strata.values())

    @property
    def total_remaining_units(self) -> int:
        return sum(s.remaining_units for s in self.strata.values())

    @property
    def ground_truth_defect_count(self) -> int:
        return int(sum(np.sum(s.defect_mask) for s in self.strata.values()))

    @property
    def ground_truth_defect_prevalence(self) -> float:
        total = self.total_units
        if total == 0:
            return 0.0
        return float(self.ground_truth_defect_count / total)

    @property
    def ground_truth_mean_quality(self) -> float:
        all_q = np.concatenate([s.qualities for s in self.strata.values()])
        return float(np.mean(all_q))

    def clone(self) -> "BulkPerishableLot":
        """Creates a deep copy of the lot for matched counterfactual comparison."""
        new_lot = BulkPerishableLot.__new__(BulkPerishableLot)
        new_lot.config = self.config
        new_lot.rng = np.random.default_rng(12345)
        new_lot.elapsed_time = self.elapsed_time
        new_lot.total_exposure_accumulated = self.total_exposure_accumulated
        new_lot.units_destroyed = self.units_destroyed
        new_lot.strata = {}
        for s_id, s in self.strata.items():
            new_lot.strata[s_id] = StratumState(
                stratum_id=s.stratum_id,
                name=s.name,
                n_units=s.n_units,
                qualities=s.qualities.copy(),
                temperature=s.temperature,
                exposure_level=s.exposure_level,
                contagion_load=s.contagion_load,
                is_accessible=s.is_accessible,
                is_exposed=s.is_exposed,
                sampled_indices=list(s.sampled_indices),
                surface_observed=s.surface_observed,
            )
        return new_lot
