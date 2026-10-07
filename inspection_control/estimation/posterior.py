"""
inspection_control/estimation/posterior.py
Bayesian Stratum Condition Model and Analytic CLT Tail Risk Evaluator.
"""

from typing import Dict, List, Tuple
import math
import numpy as np

from inspection_control.domain.stratum import StratumState
from inspection_control.domain.observation import InspectionObservation


class BayesianStratumConditionModel:
    """
    Maintains Beta(alpha, beta) conjugate posteriors for each stratum
    and computes overall lot risk using analytic CLT normal approximations.
    """

    def __init__(
        self,
        n_strata: int = 5,
        prior_alpha: float = 1.0,
        prior_beta: float = 9.0,
        presentation_bias_shift: float = 0.08,
    ):
        self.n_strata = n_strata
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.presentation_bias_shift = presentation_bias_shift

    def initialize_lot_beliefs(self, strata: Dict[int, StratumState]) -> None:
        """Initialize prior beliefs with depth-correlated bias adjustment."""
        for sid, state in strata.items():
            # Deeper strata have slightly higher uncertainty and conservative prior
            depth_penalty = self.presentation_bias_shift * sid
            state.belief_alpha = self.prior_alpha + depth_penalty
            state.belief_beta = max(1.0, self.prior_beta - depth_penalty)

    def update_with_observation(
        self,
        stratum_state: StratumState,
        observation: InspectionObservation,
    ) -> None:
        """
        Conjugate Beta-Binomial update weighted by observation confidence.
        Effective trials N_eff = N * confidence
        Effective defects k_eff = N_eff * defect_probability
        """
        conf = float(np.clip(observation.confidence, 0.05, 1.0))
        n_eff = observation.units_observed * conf
        k_eff = n_eff * observation.defect_probability

        stratum_state.belief_alpha += k_eff
        stratum_state.belief_beta += (n_eff - k_eff)
        stratum_state.observation_confidence = conf
        stratum_state.last_inspection_timestamp = observation.observation_timestamp
        stratum_state.observation_history.append({
            "obs_id": observation.observation_id,
            "quality": observation.quality_estimate,
            "defect_prob": observation.defect_probability,
            "conf": conf,
            "timestamp": observation.observation_timestamp,
        })

    def get_lot_aggregate_distribution(
        self,
        strata: Dict[int, StratumState],
    ) -> Tuple[float, float]:
        """
        Returns (mean_lot_defect_rate, std_lot_defect_rate).
        Calculated across all strata weighted by unit counts.
        """
        total_units = sum(s.unit_count for s in strata.values())
        if total_units <= 0:
            return 0.1, 0.05

        weighted_mean = 0.0
        weighted_var = 0.0

        for sid, s in strata.items():
            weight = s.unit_count / total_units
            weighted_mean += weight * s.expected_defect_rate
            # Independent stratum variances add in quadrature
            weighted_var += (weight ** 2) * s.defect_variance

        return float(weighted_mean), float(math.sqrt(max(1e-8, weighted_var)))

    def probability_lot_defect_exceeds(
        self,
        strata: Dict[int, StratumState],
        threshold: float,
    ) -> float:
        """
        Analytic tail risk P(theta_lot > threshold) via complementary error function.
        Instantaneous O(1) evaluation without Monte Carlo sampling.
        """
        mu, sigma = self.get_lot_aggregate_distribution(strata)
        if sigma <= 1e-6:
            return 1.0 if mu > threshold else 0.0

        z = (threshold - mu) / (sigma * math.sqrt(2.0))
        prob = 0.5 * math.erfc(z)
        return float(np.clip(prob, 0.0, 1.0))
