"""
inspection_control/dynamics/exposure_model.py
Non-additive, history-dependent environmental exposure model.
"""

import math
from typing import Dict, Any
from inspection_control.domain.exposure_state import StratumExposureRecord, ExposureStage


class NonAdditiveExposureModel:
    """
    Computes exposure accumulation where the marginal damage of an action
    is non-linearly coupled with prior exposure duration, thermal history,
    and mechanical disruption.
    """

    def __init__(
        self,
        base_rate: float = 0.001,
        thermal_shock_weight: float = 0.15,
        reclosed_trap_multiplier: float = 1.6,
        disturbance_decay_factor: float = 0.3,
    ):
        self.base_rate = base_rate
        self.thermal_shock_weight = thermal_shock_weight
        self.reclosed_trap_multiplier = reclosed_trap_multiplier
        self.disturbance_decay_factor = disturbance_decay_factor

    def compute_marginal_exposure_impact(
        self,
        record: StratumExposureRecord,
        action_duration_sec: float,
        ambient_temp_c: float,
        stratum_temp_c: float,
        is_opening_action: bool,
    ) -> float:
        """
        Calculates the non-additive exposure increment.
        Key property: An action on an already-exposed or repeatedly opened
        stratum causes significantly higher deterioration than on a fresh stratum.
        """
        delta_t = max(0.0, ambient_temp_c - stratum_temp_c)
        
        # 1. Thermal shock gradient (Arrhenius-style exponential response)
        shock_factor = math.exp(min(2.5, self.thermal_shock_weight * delta_t))
        
        # 2. Cumulative fatigue / history weighting
        # Previous exposure weakens epidermal skin resistance
        fatigue_multiplier = 1.0 + 0.4 * math.log1p(record.cumulative_exposure_time_sec / 30.0)
        
        # 3. Repeated handling / disturbance penalty
        opening_penalty = 1.0 + (0.25 * record.times_opened) if is_opening_action else 1.0
        
        # 4. Trapped microclimate penalty if re-covered
        trap_factor = self.reclosed_trap_multiplier if record.exposure_state == ExposureStage.RE_COVERED else 1.0

        marginal_impact = (
            self.base_rate *
            action_duration_sec *
            shock_factor *
            fatigue_multiplier *
            opening_penalty *
            trap_factor
        )
        return float(marginal_impact)
