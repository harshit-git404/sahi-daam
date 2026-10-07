"""
inspection_control/estimation/uncertainty.py
Epistemic and Aleatoric Uncertainty Decomposition for Bulk Lot Inspection.
"""

from typing import Dict, Any
import numpy as np

from inspection_control.domain.stratum import StratumState


class UncertaintyEstimator:
    """Decomposes uncertainty into observation noise vs lack of stratum evidence."""

    @staticmethod
    def compute_stratum_uncertainty(stratum: StratumState) -> Dict[str, float]:
        a, b = stratum.belief_alpha, stratum.belief_beta
        total_evidence = a + b
        
        # Epistemic uncertainty: inversely related to total evidence
        epistemic = float(np.clip(1.0 / (1.0 + 0.1 * total_evidence), 0.0, 1.0))
        
        # Aleatoric uncertainty: maximum when expected defect rate is near 0.5
        p = stratum.expected_defect_rate
        aleatoric = float(4.0 * p * (1.0 - p))
        
        # Total variance
        total_var = stratum.defect_variance

        return {
            "epistemic_uncertainty": epistemic,
            "aleatoric_uncertainty": aleatoric,
            "posterior_variance": total_var,
            "observation_confidence": stratum.observation_confidence,
        }
