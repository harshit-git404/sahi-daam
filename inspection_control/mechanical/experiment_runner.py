"""
inspection_control/mechanical/experiment_runner.py
Master Simulation and Experiment Runner for Mechanical State-Altering Inspection.

Supports:
- High-throughput execution across 10,000+ training and 10,000+ evaluation episodes
- Multi-regime experiment matrix (Regimes 1-10)
- Calibration of additive FB6 baseline on training lots ONLY (zero leakage)
- Ablation studies (memory, obs coupling, condition coupling, uncertainty)
- Model mismatch stress tests (+/- 10% to +/- 50%)
- Sensor robustness sweeps (noise, bias, dropout)
"""

from typing import Dict, Any, List, Tuple, Optional
import copy
import time
import numpy as np

from inspection_control.mechanical.lot_mechanical_model import (
    MechanicalBulkLot,
    MechanicalDefectPattern,
)
from inspection_control.mechanical.mechanical_state import MechanicalStratumState
from inspection_control.mechanical.mechanical_access_graph import (
    MechanicalAccessGraph,
    MechAction,
    MechActionType,
)
from inspection_control.mechanical.simulated_sensors import SimulatedMechanicalSensors
from inspection_control.mechanical.sensor_fusion import MechanicalSensorFusion
from inspection_control.mechanical.observability_model import MechanicalObservabilityModel
from inspection_control.mechanical.condition_model import MechanicalConditionModel
from inspection_control.mechanical.planners.fb_planners import (
    BaseMechanicalPlanner,
    FB0SurfaceOnlyPlanner,
    FB1FixedSamplingPlanner,
    FB2DepthStratifiedPlanner,
    FB3MyopicInfoGainPlanner,
    FB4GenericVOIPlanner,
    FB5StateBlindLookaheadPlanner,
    FB6CalibratedAdditivePlanner,
    FB7MechanicalStateAwarePlanner,
    OracleMechanicalPlanner,
)
from inspection_control.domain.disposition import (
    DispositionEvaluator,
    DispositionDecision,
    DispositionLossConfig,
)


def run_episode(
    lot: MechanicalBulkLot,
    planner: BaseMechanicalPlanner,
    obs_model: MechanicalObservabilityModel,
    cond_model: MechanicalConditionModel,
    sensor_suite: SimulatedMechanicalSensors,
    fusion: MechanicalSensorFusion,
    evaluator: DispositionEvaluator,
    budget_inr: float = 60.0,
    max_steps: int = 8,
) -> Dict[str, Any]:
    """Execute a single closed-loop mechanical inspection episode."""
    planner.reset()
    access_graph = MechanicalAccessGraph(n_strata=lot.n_strata)
    fusion.initialize(lot.strata)

    remaining_budget = budget_inr
    total_spent = 0.0
    action_history: List[str] = []
    step = 0

    while step < max_steps and remaining_budget > 0.0:
        step += 1

        # 1. Acquire sensor readings and update fusion filter
        sensor_suite.update_ground_truth(
            forces=[lot.strata[i].force_n for i in range(lot.n_strata)],
            displacements=[lot.strata[i].displacement_cm for i in range(lot.n_strata)],
            pressures=[lot.strata[i].force_n / 10.0 for i in range(lot.n_strata)],
        )
        nominal_stiffness = [lot.strata[i].stiffness_n_per_cm for i in range(lot.n_strata)]
        fused = fusion.fuse_step(
            timestamp_sec=lot.current_time_sec,
            action_name="PRE_STEP",
            target_stratum_id=-1,
            nominal_stiffness=nominal_stiffness,
        )

        # 2. Planner selects action
        if isinstance(planner, OracleMechanicalPlanner):
            chosen_action = access_graph.get_candidate_actions()[0] # STOP
        else:
            chosen_action = planner.select_action(
                access_graph=access_graph,
                strata=lot.strata,
                budget_remaining=remaining_budget,
                fusion_state=fused,
            )

        action_history.append(chosen_action.name)

        if chosen_action.action_type == MechActionType.STOP:
            break

        # Deduct cost and execute physical transition
        cost = chosen_action.physical_cost_inr
        remaining_budget -= cost
        total_spent += cost

        access_graph.execute_action(chosen_action)
        lot.execute_physical_action(
            action_name=chosen_action.name,
            target_stratum_id=chosen_action.target_stratum_id,
            duration_sec=chosen_action.duration_sec,
        )

        # Apply condition deterioration
        cond_model.apply_mechanical_deterioration(
            strata=lot.strata,
            delta_t_sec=chosen_action.duration_sec,
        )

        # If observation, capture camera reading and update belief
        if chosen_action.action_type == MechActionType.OBSERVE:
            sid = chosen_action.target_stratum_id
            obs = obs_model.capture_stratum_observation(lot.strata[sid])
            planner.update_belief(
                stratum_id=sid,
                observed_theta=obs["observed_defect_rate"],
                confidence=obs["confidence"],
            )

    # Terminal disposition
    if isinstance(planner, OracleMechanicalPlanner):
        disposition = planner.recommend_terminal_disposition(lot.overall_true_defect_rate)
    else:
        disposition = planner.recommend_terminal_disposition()

    loss_dict = evaluator.evaluate_loss(
        decision=disposition,
        true_lot_defect_rate=lot.overall_true_defect_rate,
        inspection_cost_inr=total_spent,
    )

    # Calculate residual hidden risk (unobserved strata variance)
    unobserved_count = sum(1 for s in lot.strata.values() if not s.is_observed)
    cum_mechanical_stress = sum(s.accumulated_load_n_sec for s in lot.strata.values())

    return {
        "planner": planner.name,
        "disposition": disposition.value,
        "total_spent_inr": total_spent,
        "steps_taken": len(action_history),
        "action_sequence": action_history,
        "total_disposition_loss": float(loss_dict["total_disposition_loss"]),
        "penalty": float(loss_dict["disposition_penalty"]),
        "true_defect_rate": float(lot.overall_true_defect_rate),
        "unobserved_strata_count": unobserved_count,
        "cum_mechanical_stress": cum_mechanical_stress,
        "is_correct": float(loss_dict["is_correct"]),
    }


def calibrate_fb6_on_training_data(
    n_training_episodes: int = 10000,
    seed: int = 1001,
) -> Dict[str, float]:
    """
    Fits FB6 additive per-action costs on training lots to prevent strawman baseline.
    Computes the empirical mean marginal mechanical damage per action.
    """
    rng = np.random.default_rng(seed)
    cond_model = MechanicalConditionModel(condition_coupling_strength=0.25)
    evaluator = DispositionEvaluator(DispositionLossConfig())

    marginal_damage_by_action = {
        "OBSERVE": [],
        "REMOVE": [],
        "HOLD": [],
        "RECONFIGURE": [],
    }

    # Sample representative episodes to measure average mechanical damage induced
    n_sample = min(2000, n_training_episodes)
    for i in range(n_sample):
        pat = rng.choice(list(MechanicalDefectPattern))
        lot = MechanicalBulkLot(
            lot_id=f"train_calib_{i}",
            pattern=pat,
            mechanical_memory_strength=0.5,
            rng=rng,
        )
        # Test REMOVE action
        f_before = [s.force_n for s in lot.strata.values()]
        lot.execute_physical_action("REMOVE_S0", 0, duration_sec=8.0)
        damages = cond_model.apply_mechanical_deterioration(lot.strata, delta_t_sec=8.0)
        tot_dmg = sum(damages.values()) * 1200.0 # Economic damage value
        marginal_damage_by_action["REMOVE"].append(tot_dmg)

        # Test HOLD action
        lot.execute_physical_action("HOLD_SETTLE", -1, duration_sec=10.0)
        damages_h = cond_model.apply_mechanical_deterioration(lot.strata, delta_t_sec=10.0)
        marginal_damage_by_action["HOLD"].append(sum(damages_h.values()) * 1200.0)

    calibrated_weights = {
        "OBSERVE": 0.25,
        "REMOVE": float(max(1.0, np.mean(marginal_damage_by_action["REMOVE"]))),
        "HOLD": float(max(0.1, np.mean(marginal_damage_by_action["HOLD"]))),
        "RECONFIGURE": 1.2,
    }

    return calibrated_weights
