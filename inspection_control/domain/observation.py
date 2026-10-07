"""
inspection_control/domain/observation.py
Sensor observation schemas and metadata for bulk lot inspection.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import time


@dataclass
class InspectionObservation:
    """
    Standard observation output from visual or physical sensing of a stratum.
    """
    observation_id: str
    visible_stratum: int
    quality_estimate: float         # 0.0 (total decay) to 1.0 (pristine grade A)
    defect_probability: float       # Estimated fraction of defective produce [0, 1]
    confidence: float               # Observation reliability / fidelity score [0, 1]
    observation_timestamp: float = field(default_factory=time.time)
    units_observed: int = 15
    sensor_metadata: Dict[str, Any] = field(default_factory=dict)
    image_path: Optional[str] = None
    observation_latency_ms: float = 0.0

    @property
    def effective_observed_defects(self) -> float:
        """Weighted defect count for Bayesian updates."""
        return self.defect_probability * self.units_observed
