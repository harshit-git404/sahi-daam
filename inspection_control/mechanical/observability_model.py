"""
inspection_control/mechanical/observability_model.py
Mechanical Observability Coupling Model.

Couples mechanical strain and contact geometry to optical defect visibility.
Includes configurable coupling strength: 0.0 (null/decoupled) to 1.0 (strong).
"""

from typing import Dict, Any, Optional
import numpy as np
from inspection_control.mechanical.mechanical_state import MechanicalStratumState


class MechanicalObservabilityModel:
    """
    Simulates optical observation quality as a function of true condition,
    surface geometry, compression, and sensor noise.
    """

    def __init__(
        self,
        coupling_strength: float = 0.35,  # 0.0 = no coupling, 0.35 = medium, 0.7 = strong
        base_noise_sigma: float = 0.03,
        rng: Optional[np.random.Generator] = None,
    ):
        self.coupling_strength = float(coupling_strength)
        self.base_noise_sigma = float(base_noise_sigma)
        self._rng = rng or np.random.default_rng(42)

    def capture_stratum_observation(
        self,
        stratum: MechanicalStratumState,
    ) -> Dict[str, Any]:
        """
        Generate visual observation for target stratum.
        Under compression, lateral faces and inter-unit fissures are occluded.
        Under zero coupling, observation is strictly decoupled from mechanical state.
        """
        true_theta = stratum.true_defect_rate

        # Occlusion effect increases with compression and residual deformation
        max_nominal_compression = 2.0  # cm
        effective_compression = stratum.compression_cm + stratum.residual_deformation_cm
        compression_ratio = min(1.0, max(0.0, effective_compression / max_nominal_compression))

        # Occlusion degrades signal-to-noise and introduces negative defect bias (hidden rot)
        occlusion_factor = self.coupling_strength * compression_ratio
        stratum.visual_occlusion_factor = occlusion_factor

        # Observed defect rate: true rate attenuated by occlusion + noise
        noise = float(self._rng.normal(0.0, self.base_noise_sigma * (1.0 + occlusion_factor)))
        
        # When occlusion is high, defects hidden underneath compressed units are missed
        observed_theta = true_theta * (1.0 - 0.5 * occlusion_factor) + noise
        observed_theta = float(np.clip(observed_theta, 0.0, 1.0))

        confidence = float(np.clip(1.0 - occlusion_factor - abs(noise), 0.2, 0.98))

        return {
            "stratum_id": stratum.stratum_id,
            "observed_defect_rate": observed_theta,
            "occlusion_factor": occlusion_factor,
            "confidence": confidence,
            "coupling_strength": self.coupling_strength,
        }
