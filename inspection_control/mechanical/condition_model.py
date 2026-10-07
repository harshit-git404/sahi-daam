"""
inspection_control/mechanical/condition_model.py
Mechanical Condition Deterioration Model.

Models produce bruising, tissue breakdown, and latent defect activation
induced by excessive or prolonged normal mechanical loading.
Includes configurable condition coupling: 0.0 (null/no damage) to 1.0.
"""

from typing import Dict, Any, Optional
import numpy as np
from inspection_control.mechanical.mechanical_state import MechanicalStratumState


class MechanicalConditionModel:
    """
    Simulates quality deterioration driven by sustained or peak contact forces.
    """

    def __init__(
        self,
        condition_coupling_strength: float = 0.25, # 0.0 = no damage, >0 = damage active
        damage_threshold_force_n: float = 140.0,   # Force threshold above which bruising occurs
        base_decay_rate_per_hour: float = 0.02,    # Base bruising rate per hour of excess load
    ):
        self.coupling_strength = float(condition_coupling_strength)
        self.damage_threshold_force_n = float(damage_threshold_force_n)
        self.base_decay_rate_per_hour = float(base_decay_rate_per_hour)

    def apply_mechanical_deterioration(
        self,
        strata: Dict[int, MechanicalStratumState],
        delta_t_sec: float,
    ) -> Dict[int, float]:
        """
        Updates latent defect rates if force exceeds threshold.
        If coupling_strength is 0.0, condition is completely decoupled (zero change).
        """
        damage_deltas = {}
        if self.coupling_strength <= 0.0 or delta_t_sec <= 0.0:
            for sid in strata:
                damage_deltas[sid] = 0.0
            return damage_deltas

        dt_hours = delta_t_sec / 3600.0

        for sid, s in strata.items():
            if not s.is_present:
                damage_deltas[sid] = 0.0
                continue

            if s.force_n > self.damage_threshold_force_n:
                excess_ratio = (s.force_n - self.damage_threshold_force_n) / self.damage_threshold_force_n
                # Rate proportional to excess stress and duration
                delta_defect = self.coupling_strength * self.base_decay_rate_per_hour * excess_ratio * dt_hours
                s.true_defect_rate = min(1.0, s.true_defect_rate + delta_defect)
                s.units_defective = int(np.round(s.true_defect_rate * s.units_total))
                s.mechanical_bruising_delta += delta_defect
                damage_deltas[sid] = delta_defect
            else:
                damage_deltas[sid] = 0.0

        return damage_deltas
