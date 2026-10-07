"""
inspection_control/mechanical/path_dependence_test.py
Matched Plan-Swap Path-Dependence Test for Mechanical Inspection.

Evaluates whether identical sets of physical actions executed under different
temporal sequences yield divergent mechanical state trajectories and inspection
outcomes under null, low, medium, and high mechanical memory regimes.
"""

from typing import Dict, Any, List
import copy
import numpy as np

from inspection_control.mechanical.lot_mechanical_model import (
    MechanicalBulkLot,
    MechanicalDefectPattern,
)
from inspection_control.mechanical.observability_model import MechanicalObservabilityModel
from inspection_control.mechanical.condition_model import MechanicalConditionModel
from inspection_control.domain.disposition import (
    DispositionEvaluator,
    DispositionDecision,
    DispositionLossConfig,
)


def run_single_plan_trajectory(
    lot: MechanicalBulkLot,
    action_sequence: List[Dict[str, Any]],
    obs_model: MechanicalObservabilityModel,
    cond_model: MechanicalConditionModel,
) -> Dict[str, Any]:
    """Execute a prescribed deterministic sequence of actions on a lot."""
    observations = []
    total_physical_cost = 0.0

    for act in action_sequence:
        name = act["name"]
        sid = act["target_stratum_id"]
        dur = act["duration_sec"]
        cost = act["cost_inr"]

        total_physical_cost += cost

        # Apply physical action and mechanical redistribution
        lot.execute_physical_action(name, sid, dur)

        # Apply condition deterioration
        cond_model.apply_mechanical_deterioration(lot.strata, dur)

        # If observation, capture
        if name.startswith("OBSERVE_"):
            obs = obs_model.capture_stratum_observation(lot.strata[sid])
            observations.append(obs)

    # Calculate final mechanical metrics
    final_forces = [lot.strata[i].force_n for i in range(lot.n_strata)]
    final_compressions = [lot.strata[i].compression_cm for i in range(lot.n_strata)]
    final_residual_deformations = [lot.strata[i].residual_deformation_cm for i in range(lot.n_strata)]
    accumulated_loads = [lot.strata[i].accumulated_load_n_sec for i in range(lot.n_strata)]

    evaluator = DispositionEvaluator(DispositionLossConfig())
    # Assess terminal loss
    loss_res = evaluator.evaluate_loss(
        decision=DispositionDecision.ACCEPT if lot.overall_true_defect_rate <= 0.08 else DispositionDecision.MARKDOWN,
        true_lot_defect_rate=lot.overall_true_defect_rate,
        inspection_cost_inr=total_physical_cost,
    )

    return {
        "final_forces": final_forces,
        "final_compressions": final_compressions,
        "final_residual_deformations": final_residual_deformations,
        "accumulated_loads": accumulated_loads,
        "observations": observations,
        "total_disposition_loss": loss_res["total_disposition_loss"],
        "true_defect_rate": lot.overall_true_defect_rate,
    }


def run_matched_path_dependence_experiment(
    n_trials: int = 50,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Run matched Plan A vs Plan B across null (memory=0), medium (memory=0.5), and high (memory=1.0).
    Plan A and Plan B have:
    - Same total access
    - Same total elapsed time (36 seconds)
    - Same final exposed strata (S0 removed, S1 observed)
    - Different order of observation, hold, and reconfiguration.
    """
    plan_a = [
        {"name": "OPEN_S0", "target_stratum_id": 0, "duration_sec": 4.0, "cost_inr": 2.0},
        {"name": "OBSERVE_S0", "target_stratum_id": 0, "duration_sec": 4.0, "cost_inr": 5.0},
        {"name": "REMOVE_S0", "target_stratum_id": 0, "duration_sec": 8.0, "cost_inr": 12.0},
        {"name": "HOLD_SETTLE", "target_stratum_id": -1, "duration_sec": 10.0, "cost_inr": 2.0},
        {"name": "RECONFIGURE_STACK", "target_stratum_id": -1, "duration_sec": 6.0, "cost_inr": 6.0},
        {"name": "OBSERVE_S1", "target_stratum_id": 1, "duration_sec": 4.0, "cost_inr": 5.0},
    ]

    plan_b = [
        {"name": "OPEN_S0", "target_stratum_id": 0, "duration_sec": 4.0, "cost_inr": 2.0},
        {"name": "REMOVE_S0", "target_stratum_id": 0, "duration_sec": 8.0, "cost_inr": 12.0},
        {"name": "HOLD_SETTLE", "target_stratum_id": -1, "duration_sec": 10.0, "cost_inr": 2.0},
        {"name": "OBSERVE_S0", "target_stratum_id": 0, "duration_sec": 4.0, "cost_inr": 5.0},
        {"name": "RECONFIGURE_STACK", "target_stratum_id": -1, "duration_sec": 6.0, "cost_inr": 6.0},
        {"name": "OBSERVE_S1", "target_stratum_id": 1, "duration_sec": 4.0, "cost_inr": 5.0},
    ]

    regimes = {
        "NULL_MEMORY": 0.0,
        "MEDIUM_MEMORY": 0.5,
        "HIGH_MEMORY": 1.0,
    }

    results = {}

    for reg_name, mem_strength in regimes.items():
        comp_diffs = []
        deform_diffs = []
        loss_diffs = []

        for trial in range(n_trials):
            rng_a = np.random.default_rng(seed + trial)
            rng_b = np.random.default_rng(seed + trial)

            lot_a = MechanicalBulkLot(
                lot_id=f"lot_a_{trial}",
                mechanical_memory_strength=mem_strength,
                rng=rng_a,
            )
            lot_b = MechanicalBulkLot(
                lot_id=f"lot_b_{trial}",
                mechanical_memory_strength=mem_strength,
                rng=rng_b,
            )

            obs_a = MechanicalObservabilityModel(coupling_strength=0.35, rng=np.random.default_rng(100 + trial))
            obs_b = MechanicalObservabilityModel(coupling_strength=0.35, rng=np.random.default_rng(100 + trial))
            cond_a = MechanicalConditionModel(condition_coupling_strength=0.25)
            cond_b = MechanicalConditionModel(condition_coupling_strength=0.25)

            res_a = run_single_plan_trajectory(lot_a, plan_a, obs_a, cond_a)
            res_b = run_single_plan_trajectory(lot_b, plan_b, obs_b, cond_b)

            # Measure difference on core stratum S1
            d_comp = abs(res_a["final_compressions"][1] - res_b["final_compressions"][1])
            d_def = abs(res_a["final_residual_deformations"][1] - res_b["final_residual_deformations"][1])
            d_loss = abs(res_a["total_disposition_loss"] - res_b["total_disposition_loss"])

            comp_diffs.append(d_comp)
            deform_diffs.append(d_def)
            loss_diffs.append(d_loss)

        mean_comp_diff = float(np.mean(comp_diffs))
        mean_def_diff = float(np.mean(deform_diffs))
        mean_loss_diff = float(np.mean(loss_diffs))

        has_path_dependence = (mean_comp_diff > 1e-4 or mean_def_diff > 1e-4)

        results[reg_name] = {
            "mechanical_memory_strength": mem_strength,
            "mean_compression_diff_cm": mean_comp_diff,
            "mean_residual_deformation_diff_cm": mean_def_diff,
            "mean_loss_diff_inr": mean_loss_diff,
            "path_dependence_detected": bool(has_path_dependence),
        }

    return results
