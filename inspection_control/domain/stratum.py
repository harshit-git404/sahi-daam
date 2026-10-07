"""
inspection_control/domain/stratum.py
Physical stratum representation for bulk perishable lots.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time


@dataclass
class StratumState:
    """
    Publicly observable and estimated state of a physical stratum.
    Excludes any ground-truth defect labels.
    """
    stratum_id: int
    name: str
    unit_count: int
    physical_depth: float  # meters (0.0 for top surface)
    accessibility: bool = False
    exposure_start_time: Optional[float] = None
    cumulative_exposure_time: float = 0.0
    temperature_history: List[float] = field(default_factory=list)
    humidity_history: List[float] = field(default_factory=list)
    
    # Bayesian belief state: Beta(alpha, beta) over defect prevalence [0, 1]
    belief_alpha: float = 1.0
    belief_beta: float = 9.0
    
    observation_history: List[Dict[str, Any]] = field(default_factory=list)
    observation_confidence: float = 0.5
    access_prerequisites: List[int] = field(default_factory=list)
    last_inspection_timestamp: Optional[float] = None
    
    # Non-additive exposure ledger properties
    is_open: bool = False
    times_opened: int = 0
    mechanical_disturbance_index: float = 0.0

    @property
    def expected_defect_rate(self) -> float:
        """Expected defect prevalence from current Beta posterior."""
        total = self.belief_alpha + self.belief_beta
        return self.belief_alpha / total if total > 0 else 0.1

    @property
    def defect_variance(self) -> float:
        """Variance of defect rate posterior."""
        a, b = self.belief_alpha, self.belief_beta
        total = a + b
        if total <= 0:
            return 0.01
        return (a * b) / ((total ** 2) * (total + 1))

    def record_temperature(self, temp_c: float) -> None:
        self.temperature_history.append(temp_c)

    def record_humidity(self, rh_pct: float) -> None:
        self.humidity_history.append(rh_pct)
