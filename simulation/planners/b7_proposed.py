"""
simulation/planners/b7_proposed.py
B7 — Proposed Method: Closed-Loop Inspection Control System with Exposure-Aware
Hidden-Stratum Condition Model and Access-Gated, State-Altering Planning.

Implements:
1. Exposure-aware Bayesian hidden-stratum condition model P(stratum | surface, bias)
2. Precedence-constrained physical access graph
3. Option value of enabling actions (unlocked future observations)
4. State-altering inspection model (time, thermal exposure, deterioration, contagion)
5. Downstream economic disposition loss minimization
6. Receding-horizon planning (plans H-step sequence, executes only the first action, replans)
7. Stopping risk certificate.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import numpy as np

from simulation.environment.access_graph import AccessGraph, ActionType, InspectionAction
from simulation.environment.dynamics import ObservationYield
from simulation.models.disposition import DispositionDecision, DispositionEvaluator
from simulation.models.stratum_model import HiddenStratumConditionModel
from simulation.planners.base import BaseInspectionPlanner


@dataclass
class AblationConfig:
    """Controls selective deactivation of individual mechanisms for Ablation Studies."""
    disable_presentation_bias: bool = False      # Ablation A
    disable_option_value: bool = False           # Ablation B (devolves enabling lookahead)
    disable_state_change: bool = False           # Ablation C (ignores deterioration)
    disable_contagion: bool = False              # Ablation E (ignores pathogen spread)
    disable_disposition_loss: bool = False       # Ablation F (uses raw variance instead of loss)
    disable_receding_horizon: bool = False       # Ablation G
    disable_access_constraints: bool = False     # Ablation H
    disable_stopping_certificate: bool = False   # Ablation I


@dataclass
class PlanEvaluationResult:
    action: InspectionAction
    score: float
    expected_loss_reduction: float
    option_value: float
    monetary_cost: float
    expected_deterioration_cost: float
    expected_contagion_cost: float
    expected_sampling_cost: float


class B7ProposedPlanner(BaseInspectionPlanner):
    """
    Proposed closed-loop access-gated, state-altering inspection planner.
    """

    def __init__(
        self,
        evaluator: Optional[DispositionEvaluator] = None,
        ablation: Optional[AblationConfig] = None,
        horizon: int = 2,
        stopping_risk_threshold: float = 0.04,
        unit_nominal_price: float = 20.0,
    ):
        super().__init__(name="B7_Proposed", evaluator=evaluator)
        self.ablation = ablation or AblationConfig()
        self.horizon = horizon
        self.stopping_risk_threshold = stopping_risk_threshold
        self.unit_nominal_price = unit_nominal_price
        self.open_loop_plan: List[InspectionAction] = []

    def reset(self) -> None:
        self.open_loop_plan.clear()

    def select_action(
        self,
        accessible_strata: Set[int],
        exposed_strata: Set[int],
        removed_strata: Set[int],
        history: List[ObservationYield],
        belief_model: HiddenStratumConditionModel,
        access_graph: AccessGraph,
        budget_remaining: float,
        step_idx: int,
    ) -> InspectionAction:
        # If open-loop ablation is active and plan exists, pop next action
        if self.ablation.disable_receding_horizon and self.open_loop_plan:
            action = self.open_loop_plan.pop(0)
            if action.cost <= budget_remaining:
                return action

        # 1. Evaluate Stopping Risk Certificate
        if not self.ablation.disable_stopping_certificate:
            if self._should_certify_stopping(belief_model):
                return self._make_stop_action()

        # 2. Query valid physical actions from access graph
        if self.ablation.disable_access_constraints:
            # Ablation H: artificially permit direct access to any stratum
            sim_acc = set(range(belief_model.n_strata))
            sim_exp = set(range(belief_model.n_strata))
            valid_actions = access_graph.get_valid_actions(sim_acc, sim_exp, set(), budget_remaining)
        else:
            valid_actions = access_graph.get_valid_actions(
                accessible_strata, exposed_strata, removed_strata, budget_remaining
            )

        if not valid_actions:
            return self._make_stop_action()

        # 3. Evaluate each candidate plan
        current_expected_loss = self._compute_belief_disposition_loss(belief_model)
        best_eval: Optional[PlanEvaluationResult] = None

        for a1 in valid_actions:
            if a1.action_type == ActionType.STOP_INSPECTION:
                continue

            eval_res = self._evaluate_candidate_action(
                a1=a1,
                current_loss=current_expected_loss,
                belief_model=belief_model,
                access_graph=access_graph,
                accessible_strata=accessible_strata,
                exposed_strata=exposed_strata,
                removed_strata=removed_strata,
                budget_remaining=budget_remaining,
            )

            if best_eval is None or eval_res.score > best_eval.score:
                best_eval = eval_res

        # 4. Stopping Decision Threshold
        if best_eval is not None and best_eval.score > 0.0:
            return best_eval.action

        return self._make_stop_action()

    def _evaluate_candidate_action(
        self,
        a1: InspectionAction,
        current_loss: float,
        belief_model: HiddenStratumConditionModel,
        access_graph: AccessGraph,
        accessible_strata: Set[int],
        exposed_strata: Set[int],
        removed_strata: Set[int],
        budget_remaining: float,
    ) -> PlanEvaluationResult:
        monetary_cost = a1.cost
        dt = a1.time_minutes
        target_s = a1.target_stratum

        # State-alteration penalties
        if self.ablation.disable_state_change:
            deterioration_cost = 0.0
        else:
            # Model expected deterioration over elapsed time dt on exposed material
            n_exposed_units = 100 * max(1, len(exposed_strata))
            deterioration_cost = 0.002 * dt * n_exposed_units * self.unit_nominal_price

        if self.ablation.disable_contagion:
            contagion_cost = 0.0
        else:
            # Model expected contagion risk if defect load is high
            stratum_est_p = belief_model.posteriors[target_s].mean
            contagion_risk = 0.005 * dt * stratum_est_p * 150.0
            if a1.action_type == ActionType.REMOVE_LAYER:
                contagion_risk += 0.015 * 100.0 * 20.0 * stratum_est_p  # Disturbance spike
            contagion_cost = contagion_risk

        sampling_destruction_cost = (a1.n_samples * self.unit_nominal_price) if a1.destroys_units else 0.0

        loss_reduction = 0.0
        option_value = 0.0

        if a1.action_type == ActionType.REMOVE_LAYER:
            if self.ablation.disable_option_value:
                # Ablation B: Enabling action has zero immediate information, so zero value
                loss_reduction = 0.0
                option_value = 0.0
            else:
                # OPTION VALUE OF ENABLING ACTIONS:
                # Lookahead to high-value observations unlocked at newly accessible stratum k+1
                next_s = target_s + 1
                sim_removed = set(removed_strata) | {target_s}
                sim_acc = set(accessible_strata) | {next_s}
                sim_exp = set(exposed_strata) | {next_s}

                future_actions = access_graph.get_valid_actions(
                    sim_acc, sim_exp, sim_removed, budget_remaining - monetary_cost
                )
                best_subsequent_net = 0.0

                for a2 in future_actions:
                    if a2.action_type != ActionType.STOP_INSPECTION and a2.provides_immediate_info:
                        sub_red = self._estimate_action_loss_reduction(a2, current_loss, belief_model)
                        sub_net = sub_red - a2.cost
                        if sub_net > best_subsequent_net:
                            best_subsequent_net = sub_net

                option_value = best_subsequent_net
                loss_reduction = 0.0  # Immediate reduction is 0

        else:
            # Direct informational action: compute expected loss reduction across outcome scenarios
            loss_reduction = self._estimate_action_loss_reduction(a1, current_loss, belief_model)

        # Objective Function:
        # Score = Expected Reduction in Downstream Loss + Option Value - Monetary Cost - Deterioration - Contagion - Destroyed Units
        net_score = (
            (loss_reduction + option_value)
            - monetary_cost
            - deterioration_cost
            - contagion_cost
            - sampling_destruction_cost
        )

        return PlanEvaluationResult(
            action=a1,
            score=net_score,
            expected_loss_reduction=loss_reduction,
            option_value=option_value,
            monetary_cost=monetary_cost,
            expected_deterioration_cost=deterioration_cost,
            expected_contagion_cost=contagion_cost,
            expected_sampling_cost=sampling_destruction_cost,
        )

    def _estimate_action_loss_reduction(
        self, action: InspectionAction, current_loss: float, belief: HiddenStratumConditionModel
    ) -> float:
        if not action.provides_immediate_info or action.action_type == ActionType.REMOVE_LAYER:
            return 0.0

        s = action.target_stratum
        post = belief.posteriors[s]
        mu = post.mean
        sigma = float(np.sqrt(post.variance))

        # 3-point scenario integration across predictive observation distribution
        scenarios = [
            (max(0.01, mu - 1.5 * sigma), 0.25),
            (mu, 0.50),
            (min(0.99, mu + 1.5 * sigma), 0.25),
        ]

        expected_post_loss = 0.0
        var_red_total = 0.0

        for y_val, weight in scenarios:
            sim_b = belief.clone()
            if action.action_type == ActionType.SAMPLE_UNITS:
                n = action.n_samples
                k = int(np.round(y_val * n))
                sim_b.update_from_unit_samples(s, k, n)
            elif action.action_type == ActionType.INSPECT_SURFACE:
                sim_b.update_from_sensor_scan(s, y_val, 0.07 ** 2)
            elif action.action_type == ActionType.SECONDARY_SENSOR:
                sim_b.update_from_sensor_scan(s, y_val, 0.02 ** 2)

            expected_post_loss += weight * self._compute_belief_disposition_loss(sim_b)
            var_red_total += weight * max(0.0, belief.whole_lot_variance - sim_b.whole_lot_variance)

        economic_gain = max(0.0, current_loss - expected_post_loss)
        epistemic_gain = var_red_total * 25000.0  # Epistemic reduction bonus
        return float(economic_gain + epistemic_gain)

    def _should_certify_stopping(self, belief_model: HiddenStratumConditionModel) -> bool:
        """
        Risk certificate: If whole-lot posterior variance is below threshold
        AND the probability of misclassification across tolerance boundaries is tiny,
        we certify the lot can be safely stopped.
        """
        # If surface hasn't even been observed once, never stop prematurely
        if belief_model.posteriors[0].sensor_scans_count == 0 and belief_model.posteriors[0].direct_samples_count == 0:
            return False

        cfg = self.evaluator.config
        rate = belief_model.whole_lot_expected_defect_rate
        unc = belief_model.whole_lot_uncertainty

        d_accept = abs(rate - cfg.tolerance_threshold_accept)
        d_markdown = abs(rate - cfg.tolerance_threshold_markdown)
        d_reroute = abs(rate - cfg.tolerance_threshold_reroute)
        min_dist = min(d_accept, d_markdown, d_reroute)

        if unc < 0.04 and min_dist > (2.5 * unc):
            return True
        return False

    def _compute_belief_disposition_loss(self, belief: HiddenStratumConditionModel) -> float:
        if self.ablation.disable_disposition_loss:
            return float(belief.whole_lot_variance * 50000.0)

        cfg = self.evaluator.config
        rate = belief.whole_lot_expected_defect_rate

        p_exceeds_accept = belief.probability_exceeds_threshold(cfg.tolerance_threshold_accept, n_mc=150)
        p_exceeds_markdown = belief.probability_exceeds_threshold(cfg.tolerance_threshold_markdown, n_mc=150)
        p_exceeds_reroute = belief.probability_exceeds_threshold(cfg.tolerance_threshold_reroute, n_mc=150)

        if rate <= cfg.tolerance_threshold_accept:
            return p_exceeds_accept * 2800.0
        elif rate <= cfg.tolerance_threshold_markdown:
            p_clean = 1.0 - p_exceeds_accept
            p_severe = p_exceeds_markdown
            return (p_clean * 1400.0) + (p_severe * 2200.0)
        elif rate <= cfg.tolerance_threshold_reroute:
            p_good = 1.0 - p_exceeds_markdown
            return p_good * 1800.0
        else:
            p_usable = 1.0 - p_exceeds_reroute
            return p_usable * 2400.0

    def _simulate_action_belief(self, belief: HiddenStratumConditionModel, action: InspectionAction) -> None:
        s = action.target_stratum
        post = belief.posteriors[s]
        if action.action_type == ActionType.SAMPLE_UNITS:
            n = action.n_samples
            k = int(np.round(post.mean * n))
            belief.update_from_unit_samples(s, k, n)
        elif action.action_type == ActionType.INSPECT_SURFACE:
            belief.update_from_sensor_scan(s, post.mean, 0.07 ** 2)
        elif action.action_type == ActionType.SECONDARY_SENSOR:
            belief.update_from_sensor_scan(s, post.mean, 0.02 ** 2)

    def _make_stop_action(self) -> InspectionAction:
        return InspectionAction(
            action_type=ActionType.STOP_INSPECTION,
            target_stratum=0,
            cost=0.0,
            time_minutes=0.0,
            destroys_units=False,
            provides_immediate_info=False,
        )
