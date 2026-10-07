"""
inspection_control/mechanical/lot_mechanical_model.py
Physical Bulk Lot Model with Coupled Mechanical Strata, Load Redistribution,
and Viscoelastic Memory Dynamics.

LABEL: SIMULATED PHYSICAL ENVIRONMENT
All physical parameters represent engineering simulation assumptions.
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import numpy as np

from inspection_control.mechanical.mechanical_state import (
    MechanicalStratumState,
    MechanicalStateLedger,
)


class MechanicalDefectPattern(str, Enum):
    UNIFORM = "UNIFORM"
    DEPTH_CORRELATED = "DEPTH_CORRELATED"
    HIDDEN_BOTTOM = "HIDDEN_BOTTOM"
    CLUSTERED = "CLUSTERED"
    SURFACE_BIASED = "SURFACE_BIASED"
    BENIGN = "BENIGN"
    ADVERSARIAL = "ADVERSARIAL"


class MechanicalBulkLot:
    """
    Simulated 5-stratum bulk perishable produce lot with heterogeneous quality,
    contact stiffness, load transfer, and viscoelastic hysteresis.
    """

    def __init__(
        self,
        lot_id: str,
        n_strata: int = 5,
        units_per_stratum: int = 50,
        pattern: MechanicalDefectPattern = MechanicalDefectPattern.DEPTH_CORRELATED,
        mechanical_memory_strength: float = 0.5, # 0.0 (none) to 1.0 (high)
        load_transfer_coeff: float = 0.25,        # Lateral load redistribution coefficient
        relaxation_tau_sec: float = 30.0,         # Viscoelastic relaxation time
        yield_force_n: float = 120.0,             # Plastic threshold force
        rng: Optional[np.random.Generator] = None,
    ):
        self.lot_id = lot_id
        self.n_strata = n_strata
        self.units_per_stratum = units_per_stratum
        self.pattern = pattern
        self.memory_strength = float(mechanical_memory_strength)
        self.load_transfer_coeff = float(load_transfer_coeff)
        self.relaxation_tau_sec = float(relaxation_tau_sec)
        self.yield_force_n = float(yield_force_n)
        self._rng = rng or np.random.default_rng(42)

        self.current_time_sec = 0.0
        self.strata: Dict[int, MechanicalStratumState] = {}
        self.ledger = MechanicalStateLedger(lot_id=lot_id, n_strata=n_strata)

        self._initialize_strata()
        self._generate_defect_distributions()
        self._update_mechanical_equilibrium(delta_t_sec=0.0)
        self.ledger.record_step(0.0, "INITIALIZE_LOT", self.strata)

    def _initialize_strata(self) -> None:
        """Initialize strata properties: mass, stiffness, deformation susceptibility."""
        # Baseline stiffness increases slightly down the stack due to packing geometry
        stiffness_profile = [120.0, 140.0, 160.0, 180.0, 210.0]  # N/cm
        deform_susceptibility = [0.08, 0.07, 0.06, 0.05, 0.04]   # cm/N plastic susceptibility

        for i in range(self.n_strata):
            # 10 kg nominal mass with small variance
            mass = float(self._rng.normal(10.0, 0.4))
            mass = max(8.0, min(12.0, mass))

            stiff = stiffness_profile[i] if i < len(stiffness_profile) else 150.0
            stiff *= float(self._rng.uniform(0.95, 1.05))

            self.strata[i] = MechanicalStratumState(
                stratum_id=i,
                name=f"Stratum S{i} ({'Surface' if i == 0 else f'Depth {i * 12}cm'})",
                mass_kg=mass,
                stiffness_n_per_cm=stiff,
                deformation_susceptibility=deform_susceptibility[i],
                is_present=True,
                is_accessible=(i == 0),
                is_open=(i == 0),
                is_observed=False,
                units_total=self.units_per_stratum,
            )

    def _generate_defect_distributions(self) -> None:
        """Generate realistic defect ground truth according to spatial patterns."""
        p = self.pattern
        rates = [0.0] * self.n_strata

        if p == MechanicalDefectPattern.BENIGN:
            rates = [float(self._rng.uniform(0.01, 0.04)) for _ in range(self.n_strata)]
        elif p == MechanicalDefectPattern.DEPTH_CORRELATED:
            # Surface healthy, bottom severe
            rates = [
                float(self._rng.uniform(0.02, 0.05)), # S0
                float(self._rng.uniform(0.05, 0.10)), # S1
                float(self._rng.uniform(0.12, 0.20)), # S2
                float(self._rng.uniform(0.25, 0.38)), # S3
                float(self._rng.uniform(0.35, 0.55)), # S4
            ]
        elif p == MechanicalDefectPattern.HIDDEN_BOTTOM:
            # Surface and mid pristine, bottom decayed
            rates = [
                float(self._rng.uniform(0.01, 0.04)),
                float(self._rng.uniform(0.02, 0.05)),
                float(self._rng.uniform(0.03, 0.06)),
                float(self._rng.uniform(0.15, 0.28)),
                float(self._rng.uniform(0.40, 0.65)),
            ]
        elif p == MechanicalDefectPattern.CLUSTERED:
            # Hotspot in core strata S1-S2
            rates = [
                float(self._rng.uniform(0.02, 0.05)),
                float(self._rng.uniform(0.30, 0.45)),
                float(self._rng.uniform(0.28, 0.42)),
                float(self._rng.uniform(0.05, 0.10)),
                float(self._rng.uniform(0.03, 0.08)),
            ]
        elif p == MechanicalDefectPattern.SURFACE_BIASED:
            rates = [
                float(self._rng.uniform(0.25, 0.40)),
                float(self._rng.uniform(0.12, 0.20)),
                float(self._rng.uniform(0.05, 0.10)),
                float(self._rng.uniform(0.02, 0.05)),
                float(self._rng.uniform(0.01, 0.04)),
            ]
        elif p == MechanicalDefectPattern.ADVERSARIAL:
            # Surface looks pristine, depths alternate sharply
            rates = [
                0.01,
                float(self._rng.uniform(0.35, 0.50)),
                0.02,
                float(self._rng.uniform(0.40, 0.60)),
                0.03,
            ]
        else: # UNIFORM
            base = float(self._rng.uniform(0.10, 0.25))
            rates = [float(np.clip(base + self._rng.normal(0, 0.03), 0.01, 0.8)) for _ in range(self.n_strata)]

        for i in range(self.n_strata):
            r = float(np.clip(rates[i], 0.0, 1.0))
            defective_count = int(np.round(r * self.units_per_stratum))
            self.strata[i].true_defect_rate = r
            self.strata[i].units_defective = defective_count

    def _update_mechanical_equilibrium(self, delta_t_sec: float) -> None:
        """
        Recompute vertical normal load, load redistribution, and viscoelastic deformation.
        """
        g = 9.81
        weights = [self.strata[i].mass_kg * g if self.strata[i].is_present else 0.0 for i in range(self.n_strata)]

        # 1. Direct vertical cumulative gravity load
        new_forces = [0.0] * self.n_strata
        cum_weight = 0.0
        for i in range(self.n_strata):
            if self.strata[i].is_present:
                cum_weight += weights[i]
                new_forces[i] = cum_weight
            else:
                new_forces[i] = 0.0

        # 2. Non-trivial load redistribution when strata have been removed
        # Granular bridging & wall support redistribution:
        # If upper strata are removed, remaining strata expand slightly and lateral stress redistributes.
        num_removed = sum(1 for i in range(self.n_strata) if not self.strata[i].is_present)
        if num_removed > 0:
            for i in range(self.n_strata):
                if self.strata[i].is_present:
                    # Redistribution adds a lateral/bridging adjustment factor
                    redist_delta = (num_removed * self.load_transfer_coeff * 9.81 * 1.5)
                    new_forces[i] = max(weights[i], new_forces[i] + redist_delta)

        # 3. Update instantaneous compression and viscoelastic / plastic deformation
        for i in range(self.n_strata):
            s = self.strata[i]
            if not s.is_present:
                s.force_n = 0.0
                s.compression_cm = 0.0
                s.recovery_fraction = 1.0 if self.memory_strength == 0.0 else min(1.0, s.recovery_fraction + delta_t_sec / self.relaxation_tau_sec)
                continue

            f_prev = s.force_n
            s.force_n = float(new_forces[i])
            s.peak_force_n = max(s.peak_force_n, s.force_n)
            s.accumulated_load_n_sec += s.force_n * delta_t_sec

            # Instantaneous elastic compression: C = F / k
            elastic_compression = s.force_n / s.stiffness_n_per_cm

            if self.memory_strength == 0.0:
                # Null memory regime: purely elastic, instantaneous rebound
                s.compression_cm = elastic_compression
                s.residual_deformation_cm = 0.0
                s.recovery_fraction = 1.0
            else:
                # Viscoelastic creep + plastic memory regime
                alpha = 1.0 - np.exp(-delta_t_sec / self.relaxation_tau_sec) if delta_t_sec > 0 else 1.0
                # Strain creeps towards steady state
                s.compression_cm = (1.0 - alpha) * s.compression_cm + alpha * elastic_compression

                # Plastic yield accumulation under heavy sustained loading
                if s.force_n > self.yield_force_n:
                    excess_force = s.force_n - self.yield_force_n
                    plastic_delta = self.memory_strength * s.deformation_susceptibility * (excess_force / 100.0) * (delta_t_sec / 10.0)
                    s.residual_deformation_cm += plastic_delta

                # Incomplete viscoelastic recovery upon unloading
                if s.force_n < f_prev:
                    recovery_rate = delta_t_sec / (self.relaxation_tau_sec * (1.0 + self.memory_strength))
                    s.recovery_fraction = min(1.0, s.recovery_fraction + recovery_rate)
                    s.compression_cm = max(s.residual_deformation_cm, s.compression_cm * (1.0 - recovery_rate * (1.0 - self.memory_strength)))

            s.displacement_cm = s.compression_cm + s.residual_deformation_cm

    def execute_physical_action(
        self,
        action_name: str,
        target_stratum_id: int,
        duration_sec: float,
    ) -> Dict[str, Any]:
        """Apply physical action, advance time, and compute new mechanical state."""
        self.current_time_sec += duration_sec
        op_log = {"action": action_name, "target": target_stratum_id, "duration": duration_sec}

        if action_name.startswith("REMOVE_"):
            if self.strata[target_stratum_id].is_present:
                self.strata[target_stratum_id].is_present = False
                self.strata[target_stratum_id].is_open = False
                # The next present stratum becomes accessible
                for j in range(target_stratum_id + 1, self.n_strata):
                    if self.strata[j].is_present:
                        self.strata[j].is_accessible = True
                        self.strata[j].is_open = True
                        break

        elif action_name.startswith("OPEN_"):
            self.strata[target_stratum_id].is_open = True

        elif action_name.startswith("OBSERVE_"):
            self.strata[target_stratum_id].is_observed = True

        elif action_name.startswith("RECONFIGURE_"):
            # Lateral settling and restacking release transient bridging
            for s in self.strata.values():
                if s.is_present:
                    s.residual_deformation_cm *= 0.90

        # Update mechanical equilibrium after the action
        self._update_mechanical_equilibrium(delta_t_sec=duration_sec)
        self.ledger.record_step(self.current_time_sec, action_name, self.strata)

        return op_log

    @property
    def overall_true_defect_rate(self) -> float:
        total_units = sum(s.units_total for s in self.strata.values())
        total_defective = sum(s.units_defective for s in self.strata.values())
        return total_defective / total_units if total_units > 0 else 0.0
