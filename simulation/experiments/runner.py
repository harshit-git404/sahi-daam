"""
simulation/experiments/runner.py
Monte Carlo Paired Trial Execution Engine.

Simulates closed-loop inspection trials across all planners (B0 through B7) on
identical counterfactual lot instances. Records all physical, informational, and
economic loss metrics.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np

from simulation.environment.access_graph import AccessGraph, ActionType, InspectionAction
from simulation.environment.dynamics import LotDynamicsEngine, ObservationYield
from simulation.environment.lot import BulkPerishableLot, DefectPattern, LotConfig, PresentationBias
from simulation.models.disposition import DecisionLossResult, DispositionEvaluator
from simulation.models.stratum_model import HiddenStratumConditionModel
from simulation.planners.base import BaseInspectionPlanner


@dataclass
class TrialMetrics:
    planner_name: str
    trial_seed: int
    lot_true_defect_rate: float
    lot_estimated_defect_rate: float
    decision: str
    optimal_decision: str
    is_correct_disposition: bool
    is_false_accept: bool
    is_false_reject: bool
    total_loss: float
    disposition_loss: float
    inspection_monetary_cost: float
    destroyed_unit_loss: float
    deterioration_loss: float
    units_destroyed: int
    inspection_time_minutes: float
    access_operations_count: int      # e.g. REMOVE_LAYER count
    sensor_scans_count: int
    steps_count: int
    residual_uncertainty: float


class SimulationTrialRunner:
    """
    Executes simulated inspection episodes using closed-loop environment feedback.
    """

    def __init__(
        self,
        lot_config: Optional[LotConfig] = None,
        evaluator: Optional[DispositionEvaluator] = None,
        max_steps: int = 12,
        budget_limit: float = 180.0,
    ):
        self.lot_config = lot_config or LotConfig()
        self.evaluator = evaluator or DispositionEvaluator()
        self.max_steps = max_steps
        self.budget_limit = budget_limit
        self.dynamics = LotDynamicsEngine()

    def run_single_trial(
        self,
        planner: BaseInspectionPlanner,
        lot_instance: BulkPerishableLot,
        trial_seed: int,
    ) -> TrialMetrics:
        """
        Runs one complete closed-loop inspection episode on the provided lot instance.
        """
        planner.reset()
        lot = lot_instance.clone()
        access_graph = AccessGraph(n_strata=lot.config.n_strata)

        # Belief model initialized with prior matching lot presentation bias
        belief_model = HiddenStratumConditionModel(
            n_strata=lot.config.n_strata,
            presentation_bias=lot.config.presentation_bias,
            prior_mean=lot.config.base_defect_rate,
        )

        accessible_strata: Set[int] = {0}
        exposed_strata: Set[int] = {0}
        removed_strata: Set[int] = set()
        history: List[ObservationYield] = []

        total_inspection_cost = 0.0
        total_deterioration_loss = 0.0
        access_ops_count = 0
        sensor_scans_count = 0
        budget_remaining = self.budget_limit

        for step in range(self.max_steps):
            action = planner.select_action(
                accessible_strata=accessible_strata,
                exposed_strata=exposed_strata,
                removed_strata=removed_strata,
                history=history,
                belief_model=belief_model,
                access_graph=access_graph,
                budget_remaining=budget_remaining,
                step_idx=step,
            )

            if action.action_type == ActionType.STOP_INSPECTION or budget_remaining < action.cost:
                break

            # Execute action through dynamics engine
            yield_data, removed_strata, accessible_strata, exposed_strata = self.dynamics.transition(
                lot=lot,
                action=action,
                removed_strata=removed_strata,
                accessible_strata=accessible_strata,
                exposed_strata=exposed_strata,
            )

            history.append(yield_data)
            total_inspection_cost += action.cost
            total_deterioration_loss += yield_data.deterioration_loss
            budget_remaining -= action.cost

            if action.action_type == ActionType.REMOVE_LAYER:
                access_ops_count += 1
            elif action.action_type in [ActionType.INSPECT_SURFACE, ActionType.SECONDARY_SENSOR]:
                sensor_scans_count += 1

            # Update Bayesian belief from observation
            if yield_data.data_type == "unit_samples" and yield_data.sample_qualities is not None:
                n_defects = int(np.sum(yield_data.sample_qualities < 0.5))
                belief_model.update_from_unit_samples(
                    yield_data.observed_stratum, n_defects, yield_data.sample_count
                )
            elif yield_data.data_type in ["surface_scan", "secondary_probe"] and yield_data.estimated_defect_rate is not None:
                belief_model.update_from_sensor_scan(
                    yield_data.observed_stratum,
                    yield_data.estimated_defect_rate,
                    yield_data.sensor_variance,
                )

        # Terminal Disposition Decision
        terminal_decision = planner.select_disposition(belief_model)
        est_defect_rate = belief_model.whole_lot_expected_defect_rate

        loss_result = self.evaluator.evaluate_decision(
            decision=terminal_decision,
            lot=lot,
            inspection_cost=total_inspection_cost,
            deterioration_loss=total_deterioration_loss,
            estimated_defect_rate=est_defect_rate,
        )

        return TrialMetrics(
            planner_name=planner.name,
            trial_seed=trial_seed,
            lot_true_defect_rate=lot.ground_truth_defect_prevalence,
            lot_estimated_defect_rate=est_defect_rate,
            decision=loss_result.decision.value,
            optimal_decision=loss_result.optimal_decision.value,
            is_correct_disposition=loss_result.is_correct_disposition,
            is_false_accept=loss_result.is_false_accept,
            is_false_reject=loss_result.is_false_reject,
            total_loss=loss_result.total_loss,
            disposition_loss=loss_result.disposition_loss,
            inspection_monetary_cost=loss_result.inspection_monetary_cost,
            destroyed_unit_loss=loss_result.destroyed_unit_loss,
            deterioration_loss=loss_result.deterioration_loss,
            units_destroyed=lot.units_destroyed,
            inspection_time_minutes=lot.elapsed_time,
            access_operations_count=access_ops_count,
            sensor_scans_count=sensor_scans_count,
            steps_count=len(history),
            residual_uncertainty=belief_model.whole_lot_uncertainty,
        )
