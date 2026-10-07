"""
inspection_control/domain/exposure_state.py
Exposure Ledger and Non-Additive History-Dependent Exposure Dynamics.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import math
import time


class ExposureStage(str, Enum):
    SEALED = "SEALED"
    EXPOSED_INITIAL = "EXPOSED_INITIAL"       # Just opened: high thermal gradient, potential condensation
    EXPOSED_EQUILIBRATED = "EXPOSED_EQUILIBRATED" # Ambient temperature matched: steady aerobic deterioration
    RE_COVERED = "RE_COVERED"                 # Covered after opening: trapped warm humid air, accelerated fungal spore growth


@dataclass
class StratumExposureRecord:
    """
    Detailed tracking of cumulative environmental and mechanical exposure
    for an individual stratum.
    """
    stratum_id: int
    exposure_state: ExposureStage = ExposureStage.SEALED
    cumulative_exposure_time_sec: float = 0.0
    temperature_integral: float = 0.0      # Integral of T_stratum dt (degC * sec)
    ambient_delta_integral: float = 0.0    # Integral of max(0, T_ambient - T_stratum) dt
    time_since_access_sec: float = 0.0
    time_since_observation_sec: float = 0.0
    times_opened: int = 0
    mechanical_disturbance: float = 0.0
    condensation_risk_index: float = 0.0
    estimated_condition_change: float = 0.0  # Estimated defect rate increase due to exposure history


@dataclass
class ExposureLedger:
    """
    Lot-level Exposure Ledger tracking non-additive, history-dependent
    exposure across all strata.
    """
    lot_id: str
    strata_records: Dict[int, StratumExposureRecord] = field(default_factory=dict)
    total_lot_elapsed_time_sec: float = 0.0
    start_time: float = field(default_factory=time.time)
    
    # Model parameters for non-additive thermal-temporal coupling
    alpha_thermal: float = 0.05    # Linear temperature coefficient
    beta_gradient: float = 0.12    # Non-linear thermal shock coefficient (Arrhenius-like)
    gamma_reclosed: float = 1.45   # Microclimate trap penalty for re-covered strata
    condensation_dewpoint_threshold: float = 4.0 # degC difference causing condensation

    def initialize_strata(self, stratum_ids: List[int]) -> None:
        for sid in stratum_ids:
            if sid not in self.strata_records:
                self.strata_records[sid] = StratumExposureRecord(stratum_id=sid)

    def update_exposure_step(
        self,
        stratum_id: int,
        elapsed_sec: float,
        ambient_temp_c: float,
        stratum_temp_c: float,
        is_open: bool,
        is_reclosed: bool = False,
    ) -> StratumExposureRecord:
        """
        Advance physical exposure for a stratum by elapsed_sec.
        Calculates non-additive history-dependent condition change.
        """
        if stratum_id not in self.strata_records:
            self.strata_records[stratum_id] = StratumExposureRecord(stratum_id=stratum_id)
            
        rec = self.strata_records[stratum_id]
        
        delta_t = max(0.0, ambient_temp_c - stratum_temp_c)

        # If open, accumulate exposure time first
        if is_open:
            rec.cumulative_exposure_time_sec += elapsed_sec
            rec.temperature_integral += stratum_temp_c * elapsed_sec
            rec.ambient_delta_integral += delta_t * elapsed_sec
            rec.time_since_access_sec += elapsed_sec

        # Determine state after duration update
        if not is_open:
            if rec.times_opened > 0 and is_reclosed:
                rec.exposure_state = ExposureStage.RE_COVERED
            else:
                rec.exposure_state = ExposureStage.SEALED
        else:
            if rec.cumulative_exposure_time_sec < 60.0:
                rec.exposure_state = ExposureStage.EXPOSED_INITIAL
            else:
                rec.exposure_state = ExposureStage.EXPOSED_EQUILIBRATED

        # If open or reclosed, accumulate thermal integrals and condition decay
        if is_open:
            
            # Condensation risk increases if cold produce meets warm humid ambient
            if delta_t >= self.condensation_dewpoint_threshold:
                rec.condensation_risk_index = min(1.0, rec.condensation_risk_index + 0.02 * (elapsed_sec / 10.0))
            else:
                rec.condensation_risk_index = max(0.0, rec.condensation_risk_index - 0.01 * (elapsed_sec / 10.0))
                
            # Non-additive rate: depends on existing cumulative time and thermal shock
            # Rate increases super-linearly with cumulative time
            time_factor = 1.0 + 0.25 * math.log1p(rec.cumulative_exposure_time_sec / 60.0)
            thermal_shock = math.exp(min(2.0, self.beta_gradient * delta_t))
            
            # Incremental condition decay (spoilage/rot acceleration)
            increment = 0.0001 * elapsed_sec * (1.0 + self.alpha_thermal * stratum_temp_c) * thermal_shock * time_factor
            rec.estimated_condition_change += increment

        elif rec.exposure_state == ExposureStage.RE_COVERED:
            # Trapped microclimate: warm humid air inside closed box accelerates rot
            rec.cumulative_exposure_time_sec += (elapsed_sec * 0.3)
            rec.time_since_access_sec += elapsed_sec
            
            trap_penalty = self.gamma_reclosed
            increment = 0.00015 * elapsed_sec * trap_penalty * (1.0 + self.alpha_thermal * stratum_temp_c)
            rec.estimated_condition_change += increment

        self.total_lot_elapsed_time_sec += elapsed_sec
        return rec

    def record_access_opened(self, stratum_id: int) -> None:
        rec = self.strata_records[stratum_id]
        rec.times_opened += 1
        rec.mechanical_disturbance += 0.15
        rec.time_since_access_sec = 0.0
        rec.exposure_state = ExposureStage.EXPOSED_INITIAL

    def record_observation_taken(self, stratum_id: int) -> None:
        rec = self.strata_records[stratum_id]
        rec.time_since_observation_sec = 0.0
