"""
inspection_control/dynamics/deterioration_model.py
Physical produce deterioration and rot contagion dynamics.
"""

from typing import Dict, List, Optional
import math
from inspection_control.domain.exposure_state import StratumExposureRecord


class ProduceDeteriorationModel:
    """
    Translates accumulated exposure and temperature history into
    real deterioration changes (loss of quality, defect acceleration).
    """

    def __init__(
        self,
        base_decay_rate: float = 0.00008,
        contagion_rate: float = 0.00015,
        ambient_temp_q10: float = 2.0, # Van 't Hoff rule: rate doubles every 10 degC
        reference_temp_c: float = 10.0,
    ):
        self.base_decay_rate = base_decay_rate
        self.contagion_rate = contagion_rate
        self.ambient_temp_q10 = ambient_temp_q10
        self.reference_temp_c = reference_temp_c

    def calculate_defect_rate_increase(
        self,
        exposure_impact: float,
        core_temp_c: float,
        ambient_temp_c: float,
        current_stratum_defect_rate: float,
        adjacent_strata_defect_rates: Optional[List[float]] = None,
    ) -> float:
        # Q10 biological respiration scaling
        temp_delta = max(0.0, core_temp_c - self.reference_temp_c)
        temp_multiplier = self.ambient_temp_q10 ** (temp_delta / 10.0)

        # Intrinsic biological breakdown
        decay_delta = exposure_impact * temp_multiplier

        # Fungal/bacterial spore contagion from adjacent strata if exposed
        contagion_delta = 0.0
        if adjacent_strata_defect_rates:
            mean_neighbor_defect = sum(adjacent_strata_defect_rates) / len(adjacent_strata_defect_rates)
            contagion_delta = self.contagion_rate * mean_neighbor_defect * exposure_impact * 5.0

        return float(decay_delta + contagion_delta)
