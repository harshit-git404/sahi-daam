"""
inspection_control/dynamics/observation_quality_model.py
Exposure-Dependent Observation Quality Model.
Models and measures empirical degradation of visual sensing due to
condensation, thermal transition settling, and physical disturbance.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import math
import numpy as np


@dataclass
class ObservationQualityMetrics:
    """Quantitative fidelity metrics for an acquired inspection observation."""
    fidelity_score: float             # [0.0, 1.0] overall confidence multiplier
    condensation_attenuation: float   # [0.0, 1.0] loss due to lens/skin moisture haze
    settling_penalty: float           # [0.0, 1.0] loss due to immediate unstacking vibration
    exposure_bleach_factor: float     # [0.0, 1.0] surface drying / oxidation color shift
    is_affected_by_exposure: bool


class ObservationQualityModel:
    """
    Evaluates how physical environmental transitions and exposure history
    alter subsequent observation reliability.
    """

    def __init__(
        self,
        enable_condensation_effect: bool = True,
        condensation_onset_dt: float = 4.0,   # Delta T (ambient - produce) triggering dew
        min_settling_time_sec: float = 5.0,    # Seconds required for dust/vibration settling
    ):
        self.enable_condensation_effect = enable_condensation_effect
        self.condensation_onset_dt = condensation_onset_dt
        self.min_settling_time_sec = min_settling_time_sec

    def evaluate_observation_fidelity(
        self,
        elapsed_since_access_sec: float,
        core_temp_c: float,
        ambient_temp_c: float,
        dew_point_c: Optional[float] = None,
        times_opened: int = 1,
    ) -> ObservationQualityMetrics:
        """
        Computes observation confidence multiplier given physical exposure history.
        """
        temp_delta = max(0.0, ambient_temp_c - core_temp_c)
        condensation_loss = 0.0

        if self.enable_condensation_effect:
            # If cold surface is below dew point or thermal gap is large, moisture forms
            if dew_point_c and core_temp_c <= dew_point_c:
                # Direct condensation dew
                severity = min(1.0, (dew_point_c - core_temp_c + 1.0) / 5.0)
                # Condensation peaks at 30-90s after opening, then slowly dries
                time_curve = math.exp(-((elapsed_since_access_sec - 45.0) ** 2) / (2.0 * (30.0 ** 2)))
                condensation_loss = 0.35 * severity * time_curve
            elif temp_delta >= self.condensation_onset_dt:
                severity = min(1.0, (temp_delta - self.condensation_onset_dt) / 8.0)
                time_curve = math.exp(-((elapsed_since_access_sec - 40.0) ** 2) / (2.0 * (25.0 ** 2)))
                condensation_loss = 0.25 * severity * time_curve

        # Settling penalty: immediately after tray removal (<5s), vibration or dust reduces clarity
        settling_loss = 0.0
        if elapsed_since_access_sec < self.min_settling_time_sec:
            settling_loss = 0.20 * (1.0 - (elapsed_since_access_sec / self.min_settling_time_sec))

        # Repeated opening handling scuff
        scuff_loss = min(0.15, 0.03 * max(0, times_opened - 1))

        total_loss = min(0.65, condensation_loss + settling_loss + scuff_loss)
        fidelity = max(0.35, 1.0 - total_loss)

        return ObservationQualityMetrics(
            fidelity_score=round(fidelity, 3),
            condensation_attenuation=round(condensation_loss, 3),
            settling_penalty=round(settling_loss, 3),
            exposure_bleach_factor=round(scuff_loss, 3),
            is_affected_by_exposure=(total_loss > 0.05),
        )
