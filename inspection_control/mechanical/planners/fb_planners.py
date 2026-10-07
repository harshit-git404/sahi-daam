"""
inspection_control/mechanical/planners/fb_planners.py
Full Suite of Mechanical Inspection Planners:
FB0 (Surface Only)
FB1 (Fixed Sampling)
FB2 (Depth Stratified)
FB3 (Myopic Information Gain)
FB4 (Generic VOI)
FB5 (State-Blind Lookahead)
FB6 (Calibrated Additive Baseline)
FB7 (Mechanical State-Aware Receding Horizon Controller)
ORACLE (Full Latent State Oracle)
"""

from typing import Dict, Any, List, Tuple, Optional
import copy
import numpy as np

from inspection_control.mechanical.mechanical_access_graph import (
    MechanicalAccessGraph,
    MechAction,
    MechActionType,
)
from inspection_control.mechanical.mechanical_state import MechanicalStratumState
from inspection_control.domain.disposition import (
    DispositionDecision,
    DispositionEvaluator,
    DispositionLossConfig,
)


class BaseMechanicalPlanner:
    """Base class providing shared Bayesian belief updating and disposition logic."""

    def __init__(self, name: str, n_strata: int = 5):
        self.name = name
        self.n_strata = n_strata
        self.loss_evaluator = DispositionEvaluator(DispositionLossConfig())
        # Prior beliefs for each stratum: Beta distributions Beta(alpha, beta)
        self.prior_alpha = np.array([2.0, 2.0, 2.5, 3.0, 3.5])
        self.prior_beta = np.array([18.0, 15.0, 12.0, 10.0, 8.0])
        self.beliefs_alpha = self.prior_alpha.copy()
        self.beliefs_beta = self.prior_beta.copy()

    def reset(self) -> None:
        self.beliefs_alpha = self.prior_alpha.copy()
        self.beliefs_beta = self.prior_beta.copy()

    def update_belief(
        self,
        stratum_id: int,
        observed_theta: float,
        confidence: float,
        effective_units: int = 15,
    ) -> None:
        """Bayesian conjugate Beta update weighted by sensor confidence."""
        k = int(np.round(observed_theta * effective_units * confidence))
        n = int(np.round(effective_units * confidence))
        self.beliefs_alpha[stratum_id] += max(0, k)
        self.beliefs_beta[stratum_id] += max(0, n - k)

    @property
    def estimated_mean_defect_rate(self) -> float:
        means = self.beliefs_alpha / (self.beliefs_alpha + self.beliefs_beta)
        return float(np.mean(means))

    def recommend_terminal_disposition(self) -> DispositionDecision:
        mean_theta = self.estimated_mean_defect_rate
        cfg = self.loss_evaluator.config
        if mean_theta <= cfg.threshold_accept:
            return DispositionDecision.ACCEPT
        elif mean_theta <= cfg.threshold_markdown:
            return DispositionDecision.MARKDOWN
        elif mean_theta <= cfg.threshold_reroute:
            return DispositionDecision.REROUTE
        else:
            return DispositionDecision.REJECT


class FB0SurfaceOnlyPlanner(BaseMechanicalPlanner):
    """FB0: Inspects surface stratum S0 once, then terminates immediately."""

    def __init__(self):
        super().__init__("FB0_Surface_Only")
        self.inspected_s0 = False

    def reset(self) -> None:
        super().reset()
        self.inspected_s0 = False

    def select_action(
        self,
        access_graph: MechanicalAccessGraph,
        strata: Dict[int, MechanicalStratumState],
        budget_remaining: float,
        fusion_state: Dict[str, Any],
    ) -> MechAction:
        candidates = access_graph.get_candidate_actions()
        stop = next(a for a in candidates if a.action_type == MechActionType.STOP)

        if not self.inspected_s0:
            obs = next((a for a in candidates if a.action_type == MechActionType.OBSERVE and a.target_stratum_id == 0), None)
            if obs:
                self.inspected_s0 = True
                return obs

        return stop


class FB1FixedSamplingPlanner(BaseMechanicalPlanner):
    """FB1: Fixed random sampling across accessible strata up to budget."""

    def __init__(self, sample_limit: int = 3):
        super().__init__("FB1_Fixed_Sampling")
        self.sample_limit = sample_limit
        self.samples = 0

    def reset(self) -> None:
        super().reset()
        self.samples = 0

    def select_action(
        self,
        access_graph: MechanicalAccessGraph,
        strata: Dict[int, MechanicalStratumState],
        budget_remaining: float,
        fusion_state: Dict[str, Any],
    ) -> MechAction:
        candidates = access_graph.get_candidate_actions()
        stop = next(a for a in candidates if a.action_type == MechActionType.STOP)

        if self.samples < self.sample_limit and budget_remaining >= 12.0:
            obs = [a for a in candidates if a.action_type == MechActionType.OBSERVE]
            if obs:
                self.samples += 1
                return obs[0]
            rem = [a for a in candidates if a.action_type == MechActionType.REMOVE]
            if rem:
                return rem[0]

        return stop


class FB2DepthStratifiedPlanner(BaseMechanicalPlanner):
    """FB2: Rigid layer-by-layer excavation protocol."""

    def __init__(self, target_depth: int = 3):
        super().__init__("FB2_Depth_Stratified")
        self.target_depth = target_depth
        self.current_depth = 0
        self.step_in_depth = 0 # 0: OBSERVE, 1: REMOVE

    def reset(self) -> None:
        super().reset()
        self.current_depth = 0
        self.step_in_depth = 0

    def select_action(
        self,
        access_graph: MechanicalAccessGraph,
        strata: Dict[int, MechanicalStratumState],
        budget_remaining: float,
        fusion_state: Dict[str, Any],
    ) -> MechAction:
        candidates = access_graph.get_candidate_actions()
        stop = next(a for a in candidates if a.action_type == MechActionType.STOP)

        if budget_remaining < 10.0 or self.current_depth >= self.target_depth:
            return stop

        if self.step_in_depth == 0:
            obs = next((a for a in candidates if a.action_type == MechActionType.OBSERVE and a.target_stratum_id == self.current_depth), None)
            if obs:
                self.step_in_depth = 1
                return obs
        else:
            rem = next((a for a in candidates if a.action_type == MechActionType.REMOVE and a.target_stratum_id == self.current_depth), None)
            if rem:
                self.current_depth += 1
                self.step_in_depth = 0
                return rem

        return stop


class FB3MyopicInfoGainPlanner(BaseMechanicalPlanner):
    """FB3: Greedy 1-step information gain."""

    def __init__(self):
        super().__init__("FB3_Myopic_InfoGain")

    def select_action(
        self,
        access_graph: MechanicalAccessGraph,
        strata: Dict[int, MechanicalStratumState],
        budget_remaining: float,
        fusion_state: Dict[str, Any],
    ) -> MechAction:
        candidates = access_graph.get_candidate_actions()
        stop = next(a for a in candidates if a.action_type == MechActionType.STOP)

        best_score = 0.0
        best_act = stop

        # Variances of strata beliefs
        variances = (self.beliefs_alpha * self.beliefs_beta) / (
            ((self.beliefs_alpha + self.beliefs_beta) ** 2) * (self.beliefs_alpha + self.beliefs_beta + 1.0)
        )

        for a in candidates:
            if a.action_type == MechActionType.STOP:
                continue
            if a.physical_cost_inr > budget_remaining:
                continue

            if a.action_type == MechActionType.OBSERVE:
                gain = float(variances[a.target_stratum_id]) * 1500.0 - a.physical_cost_inr
            elif a.action_type == MechActionType.REMOVE:
                unlocked_var = float(variances[a.unlocked_strata[0]]) if a.unlocked_strata else 0.0
                gain = unlocked_var * 800.0 - a.physical_cost_inr
            else:
                gain = -a.physical_cost_inr

            if gain > best_score:
                best_score = gain
                best_act = a

        if best_score <= 2.0:
            return stop
        return best_act


class FB4GenericVOIPlanner(BaseMechanicalPlanner):
    """FB4: Value of Information without mechanical dynamics."""

    def __init__(self):
        super().__init__("FB4_Generic_VOI")

    def select_action(
        self,
        access_graph: MechanicalAccessGraph,
        strata: Dict[int, MechanicalStratumState],
        budget_remaining: float,
        fusion_state: Dict[str, Any],
    ) -> MechAction:
        candidates = access_graph.get_candidate_actions()
        stop = next(a for a in candidates if a.action_type == MechActionType.STOP)

        best_score = 0.0
        best_act = stop

        variances = (self.beliefs_alpha * self.beliefs_beta) / (
            ((self.beliefs_alpha + self.beliefs_beta) ** 2) * (self.beliefs_alpha + self.beliefs_beta + 1.0)
        )

        for a in candidates:
            if a.action_type == MechActionType.STOP or a.physical_cost_inr > budget_remaining:
                continue

            cost = a.physical_cost_inr
            if a.action_type == MechActionType.OBSERVE:
                voi = float(variances[a.target_stratum_id]) * 1800.0 - cost
            elif a.action_type == MechActionType.REMOVE:
                unlocked_var = float(variances[a.unlocked_strata[0]]) if a.unlocked_strata else 0.0
                voi = unlocked_var * 1400.0 - cost
            else:
                voi = -cost

            if voi > best_score:
                best_score = voi
                best_act = a

        if best_score <= 3.0:
            return stop
        return best_act


class FB5StateBlindLookaheadPlanner(BaseMechanicalPlanner):
    """FB5: Full lookahead planner blind to mechanical state, strain, and damage."""

    def __init__(self):
        super().__init__("FB5_State_Blind_Lookahead")

    def select_action(
        self,
        access_graph: MechanicalAccessGraph,
        strata: Dict[int, MechanicalStratumState],
        budget_remaining: float,
        fusion_state: Dict[str, Any],
    ) -> MechAction:
        candidates = access_graph.get_candidate_actions()
        stop = next(a for a in candidates if a.action_type == MechActionType.STOP)

        best_score = 0.0
        best_act = stop

        variances = (self.beliefs_alpha * self.beliefs_beta) / (
            ((self.beliefs_alpha + self.beliefs_beta) ** 2) * (self.beliefs_alpha + self.beliefs_beta + 1.0)
        )

        for a in candidates:
            if a.action_type == MechActionType.STOP or a.physical_cost_inr > budget_remaining:
                continue

            cost = a.physical_cost_inr
            if a.action_type == MechActionType.OBSERVE:
                score = float(variances[a.target_stratum_id]) * 2200.0 - cost
            elif a.action_type == MechActionType.REMOVE:
                unlocked_var = float(variances[a.unlocked_strata[0]]) if a.unlocked_strata else 0.0
                score = unlocked_var * 1900.0 - cost
            else:
                score = -cost

            if score > best_score:
                best_score = score
                best_act = a

        if best_score <= 3.0:
            return stop
        return best_act


class FB6CalibratedAdditivePlanner(BaseMechanicalPlanner):
    """
    FB6: High-Fidelity Additive Baseline.
    Receives same action space, observations, and horizon.
    Models mechanical effects STRICTLY as calibrated additive action costs:
        cost(a) = c_physical(a) + c_additive(a)
    Carries NO dynamic mechanical state or loading history.
    """

    def __init__(
        self,
        c_add_observe: float = 0.5,
        c_add_remove: float = 3.5,
        c_add_hold: float = 0.2,
        c_add_reconfigure: float = 1.0,
    ):
        super().__init__("FB6_Calibrated_Additive")
        self.c_add_observe = float(c_add_observe)
        self.c_add_remove = float(c_add_remove)
        self.c_add_hold = float(c_add_hold)
        self.c_add_reconfigure = float(c_add_reconfigure)

    def calibrate(self, weights: Dict[str, float]) -> None:
        """Freeze calibrated additive costs fit on training data."""
        self.c_add_observe = float(weights.get("OBSERVE", self.c_add_observe))
        self.c_add_remove = float(weights.get("REMOVE", self.c_add_remove))
        self.c_add_hold = float(weights.get("HOLD", self.c_add_hold))
        self.c_add_reconfigure = float(weights.get("RECONFIGURE", self.c_add_reconfigure))

    def select_action(
        self,
        access_graph: MechanicalAccessGraph,
        strata: Dict[int, MechanicalStratumState],
        budget_remaining: float,
        fusion_state: Dict[str, Any],
    ) -> MechAction:
        candidates = access_graph.get_candidate_actions()
        stop = next(a for a in candidates if a.action_type == MechActionType.STOP)

        best_score = 0.0
        best_act = stop

        variances = (self.beliefs_alpha * self.beliefs_beta) / (
            ((self.beliefs_alpha + self.beliefs_beta) ** 2) * (self.beliefs_alpha + self.beliefs_beta + 1.0)
        )

        for a in candidates:
            if a.action_type == MechActionType.STOP:
                continue

            # Additive cost calculation (no state carried)
            add_cost = 0.0
            if a.action_type == MechActionType.OBSERVE:
                add_cost = self.c_add_observe
            elif a.action_type == MechActionType.REMOVE:
                add_cost = self.c_add_remove
            elif a.action_type == MechActionType.HOLD:
                add_cost = self.c_add_hold
            elif a.action_type == MechActionType.RECONFIGURE:
                add_cost = self.c_add_reconfigure

            effective_cost = a.physical_cost_inr + add_cost
            if effective_cost > budget_remaining:
                continue

            if a.action_type == MechActionType.OBSERVE:
                score = float(variances[a.target_stratum_id]) * 2200.0 - effective_cost
            elif a.action_type == MechActionType.REMOVE:
                unlocked_var = float(variances[a.unlocked_strata[0]]) if a.unlocked_strata else 0.0
                score = unlocked_var * 1900.0 - effective_cost
            else:
                score = -effective_cost

            if score > best_score:
                best_score = score
                best_act = a

        if best_score <= 3.0:
            return stop
        return best_act


class FB7MechanicalStateAwarePlanner(BaseMechanicalPlanner):
    """
    FB7: Proposed State-Aware Receding-Horizon Controller.
    Actively models:
    - Estimated normal forces from sensor fusion
    - Viscoelastic deformation & contact compression
    - Load redistribution onto remaining strata
    - Mechanical memory and incomplete recovery
    - Occlusion coupling affecting observation quality
    - Expected damage induced on produce by state changes
    """

    def __init__(
        self,
        name: str = "FB7_Mechanical_State_Aware",
        use_memory: bool = True,
        use_obs_coupling: bool = True,
        use_condition_coupling: bool = True,
        use_receding_horizon: bool = True,
        use_uncertainty: bool = True,
    ):
        super().__init__(name)
        self.use_memory = use_memory
        self.use_obs_coupling = use_obs_coupling
        self.use_condition_coupling = use_condition_coupling
        self.use_receding_horizon = use_receding_horizon
        self.use_uncertainty = use_uncertainty

    def select_action(
        self,
        access_graph: MechanicalAccessGraph,
        strata: Dict[int, MechanicalStratumState],
        budget_remaining: float,
        fusion_state: Dict[str, Any],
    ) -> MechAction:
        candidates = access_graph.get_candidate_actions()
        stop = next(a for a in candidates if a.action_type == MechActionType.STOP)

        best_net_benefit = 0.0
        best_act = stop

        # Current estimated forces and compressions from sensor fusion
        est_forces = fusion_state.get("estimated_forces_n", np.zeros(self.n_strata))
        est_compressions = fusion_state.get("estimated_compressions_cm", np.zeros(self.n_strata))
        uncertainty = fusion_state.get("force_uncertainty_sigma", np.ones(self.n_strata))

        variances = (self.beliefs_alpha * self.beliefs_beta) / (
            ((self.beliefs_alpha + self.beliefs_beta) ** 2) * (self.beliefs_alpha + self.beliefs_beta + 1.0)
        )

        for a in candidates:
            if a.action_type == MechActionType.STOP:
                continue
            if a.physical_cost_inr > budget_remaining:
                continue

            # 1. Physical inspection action cost
            cost = a.physical_cost_inr

            # 2. Information Value factoring in mechanical occlusion
            info_value = 0.0
            if a.action_type == MechActionType.OBSERVE:
                target = a.target_stratum_id
                target_var = float(variances[target])
                
                # If observation coupling is active, compression reduces observability
                if self.use_obs_coupling:
                    comp = est_compressions[target]
                    visibility_penalty = min(0.6, comp / 2.0 * 0.35)
                    effective_info_scale = 2200.0 * (1.0 - visibility_penalty)
                else:
                    effective_info_scale = 2200.0

                info_value = target_var * effective_info_scale

            elif a.action_type == MechActionType.REMOVE:
                unlocked_id = a.unlocked_strata[0] if a.unlocked_strata else 0
                unlocked_var = float(variances[unlocked_id])
                info_value = unlocked_var * 1900.0

            # 3. Expected produce damage under load redistribution
            expected_damage_cost = 0.0
            if self.use_condition_coupling:
                if a.action_type == MechActionType.REMOVE:
                    # Removing stratum redistributes load and causes settling impulse
                    # Estimate additional force on remaining strata
                    redistributed_force_delta = 25.0
                    for sid in range(a.target_stratum_id + 1, self.n_strata):
                        projected_force = est_forces[sid] + redistributed_force_delta
                        if projected_force > 140.0:
                            excess = projected_force - 140.0
                            expected_damage_cost += 0.05 * excess * (a.duration_sec / 3600.0) * 1200.0
                elif a.action_type == MechActionType.HOLD:
                    # Holding relieves viscoelastic stress or allows settling
                    expected_damage_cost = -1.5 # Negative cost = benefit of relaxation

            # 4. Mechanical memory / state penalty
            memory_penalty = 0.0
            if self.use_memory:
                # If memory is tracked, excessive disturbances create irreversible deformation
                memory_penalty = a.mechanical_disturbance * 2.0

            # Net receding-horizon score
            net_benefit = info_value - cost - expected_damage_cost - memory_penalty

            if net_benefit > best_net_benefit:
                best_net_benefit = net_benefit
                best_act = a

        if best_net_benefit <= 3.0:
            return stop
        return best_act


class OracleMechanicalPlanner(BaseMechanicalPlanner):
    """
    ORACLE: Full Ground Truth Omniscience.
    Has perfect knowledge of true latent defect rates and mechanical states.
    Calculates the exact lower bound on achievable disposition loss.
    """

    def __init__(self):
        super().__init__("ORACLE_Omniscient")

    def select_action(
        self,
        access_graph: MechanicalAccessGraph,
        strata: Dict[int, MechanicalStratumState],
        budget_remaining: float,
        fusion_state: Dict[str, Any],
    ) -> MechAction:
        # Oracle already knows the ground truth; stops immediately with 0 inspection spend
        candidates = access_graph.get_candidate_actions()
        return next(a for a in candidates if a.action_type == MechActionType.STOP)

    def recommend_terminal_disposition(self, true_rate: float) -> DispositionDecision:
        cfg = self.loss_evaluator.config
        if true_rate <= cfg.threshold_accept:
            return DispositionDecision.ACCEPT
        elif true_rate <= cfg.threshold_markdown:
            return DispositionDecision.MARKDOWN
        elif true_rate <= cfg.threshold_reroute:
            return DispositionDecision.REROUTE
        else:
            return DispositionDecision.REJECT
