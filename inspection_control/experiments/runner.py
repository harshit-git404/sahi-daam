"""
inspection_control/experiments/runner.py
Master Closed-Loop Execution Runner for Physical and Simulated Inspection Episodes.
Enforces the complete control loop:
Lot -> Senses -> Estimation -> Ledger -> Planner -> Actuation -> Replan -> Teardown.
"""

from typing import Dict, Any, Optional
import time

from inspection_control.domain.lot import BulkLot
from inspection_control.domain.access_graph import PhysicalActionType
from inspection_control.planning.planner import IInspectionPlanner
from inspection_control.station.hardware_interface import PhysicalInspectionStation
from inspection_control.estimation.posterior import BayesianStratumConditionModel
from inspection_control.evidence.logger import AuditLogger
from inspection_control.evidence.ground_truth import GroundTruthTeardownEvaluator


class InspectionEpisodeRunner:
    """
    Executes a complete closed-loop physical inspection trajectory for a single lot.
    """

    def __init__(
        self,
        station: Optional[PhysicalInspectionStation] = None,
        condition_model: Optional[BayesianStratumConditionModel] = None,
        logger: Optional[AuditLogger] = None,
        evaluator: Optional[GroundTruthTeardownEvaluator] = None,
    ):
        self.station = station or PhysicalInspectionStation()
        self.condition_model = condition_model or BayesianStratumConditionModel()
        self.logger = logger or AuditLogger()
        self.evaluator = evaluator or GroundTruthTeardownEvaluator()

    def run_episode(
        self,
        lot: BulkLot,
        planner: IInspectionPlanner,
        initial_budget_inr: float = 60.0,
        max_steps: int = 12,
        ambient_temp_c: float = 25.0,
    ) -> Dict[str, Any]:
        """
        Executes receding-horizon closed loop until planner stops or budget is exhausted.
        """
        # 1. Initialize Bayesian priors
        self.condition_model.initialize_lot_beliefs(lot.strata)

        remaining_budget = initial_budget_inr
        total_spent = 0.0
        elapsed_time = 0.0
        step_index = 0
        action_history = []

        while step_index < max_steps and remaining_budget > 0.0:
            step_index += 1

            # 2. Planner selects next physical action based strictly on public state
            action, telemetry = planner.select_next_action(
                lot=lot,
                remaining_budget_inr=remaining_budget,
                elapsed_time_sec=elapsed_time,
                ambient_temp_c=ambient_temp_c,
            )

            action_history.append(action.action_type.value)

            # Check for stopping decision
            if action.action_type == PhysicalActionType.STOP_INSPECTION:
                # Log stopping step
                self.logger.log_step(
                    lot_id=lot.lot_id,
                    step_index=step_index,
                    stratum_id=0,
                    action=action.name,
                    operator_status="STOPPED",
                    core_temp_c=self.station.get_current_temperature(0),
                    ambient_temp_c=ambient_temp_c,
                    rh_pct=80.0,
                    cumulative_exposure_sec=elapsed_time,
                    chosen_action=action.name,
                    reason=telemetry.get("reason", "PLANNER_STOPPED"),
                )
                break

            # Deduct cost and advance time
            remaining_budget -= action.physical_cost_inr
            total_spent += action.physical_cost_inr
            elapsed_time += action.duration_sec

            # 3. Execute physical action instruction on the station
            op_event = self.station.execute_access_instruction(lot, action)

            # 4. If action was an observation, acquire sensor frame and update Bayesian posterior
            obs = None
            if action.action_type in (PhysicalActionType.OBSERVE_STRATUM, PhysicalActionType.SAMPLE_UNITS):
                target_sid = action.target_stratum_id
                obs = self.station.capture_observation(lot, target_sid)
                
                # Update stratum belief state
                stratum_state = lot.strata[target_sid]
                self.condition_model.update_with_observation(stratum_state, obs)

            # 5. Log step telemetry to audit trail
            core_t = self.station.get_current_temperature(action.target_stratum_id)
            rec = lot.exposure_ledger.strata_records.get(action.target_stratum_id)
            cum_exp = rec.cumulative_exposure_time_sec if rec else elapsed_time

            self.logger.log_step(
                lot_id=lot.lot_id,
                step_index=step_index,
                stratum_id=action.target_stratum_id,
                action=action.name,
                operator_status=op_event.get("operator_status", "EXECUTED"),
                core_temp_c=core_t,
                ambient_temp_c=ambient_temp_c,
                rh_pct=80.0,
                cumulative_exposure_sec=cum_exp,
                observation_quality=obs.quality_estimate if obs else None,
                defect_probability=obs.defect_probability if obs else None,
                confidence=obs.confidence if obs else None,
                planner_score=telemetry.get("expected_benefit_inr"),
                chosen_action=action.name,
                reason=telemetry.get("reason"),
                metadata=telemetry,
            )

        # 6. Planner commits terminal disposition
        final_disposition = planner.recommend_terminal_disposition(lot)

        # 7. Post-inspection ground-truth teardown evaluation (completely unbiased)
        cum_lot_exposure = sum(r.cumulative_exposure_time_sec for r in lot.exposure_ledger.strata_records.values())
        
        teardown_results = self.evaluator.evaluate_completed_lot(
            lot=lot,
            chosen_disposition=final_disposition,
            total_inspection_cost_inr=total_spent,
            cumulative_exposure_time_sec=cum_lot_exposure,
            planner_name=getattr(planner, "name", "UnknownPlanner"),
        )

        teardown_results["steps_taken"] = step_index
        teardown_results["action_sequence"] = action_history
        teardown_results["total_spent_inr"] = round(total_spent, 2)
        teardown_results["elapsed_inspection_time_sec"] = round(elapsed_time, 2)

        return teardown_results
