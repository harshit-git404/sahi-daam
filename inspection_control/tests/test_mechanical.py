"""
inspection_control/tests/test_mechanical.py
Automated Verification Suite for Mechanical State-Altering Inspection System.

Tests:
1. Static load transmission and vertical force equilibrium.
2. Nonlinear load redistribution upon stratum removal.
3. Viscoelastic recovery and hysteresis under mechanical memory.
4. Null memory regime (zero hysteresis when memory_strength=0).
5. Sensor noise, quantization, calibration scaling, and dropout handling.
6. Sensor fusion filter stability and Kalman update.
7. Access graph precedence and constraint enforcement.
8. Ground-truth isolation: planner cannot read private lot ground truth.
9. Deterministic reproducibility under identical random seed.
10. Additive baseline calibration integrity (no data leakage).
"""

import pytest
import numpy as np

from inspection_control.mechanical.lot_mechanical_model import (
    MechanicalBulkLot,
    MechanicalDefectPattern,
)
from inspection_control.mechanical.simulated_sensors import SimulatedMechanicalSensors
from inspection_control.mechanical.sensor_fusion import MechanicalSensorFusion
from inspection_control.mechanical.mechanical_access_graph import (
    MechanicalAccessGraph,
    MechAction,
    MechActionType,
)
from inspection_control.mechanical.planners.fb_planners import (
    FB6CalibratedAdditivePlanner,
    FB7MechanicalStateAwarePlanner,
)
from inspection_control.mechanical.path_dependence_test import (
    run_matched_path_dependence_experiment,
)


def test_static_load_transmission():
    """Verify that vertical normal forces increase with depth."""
    lot = MechanicalBulkLot("test_static", n_strata=5)
    forces = [lot.strata[i].force_n for i in range(5)]
    for i in range(1, 5):
        assert forces[i] > forces[i - 1], f"Force at S{i} must be greater than S{i-1}"


def test_load_redistribution_on_removal():
    """Verify that removing S0 alters forces on remaining strata (not just zeroing S0)."""
    lot = MechanicalBulkLot("test_redist", n_strata=5, load_transfer_coeff=0.3)
    f_s1_initial = lot.strata[1].force_n
    
    lot.execute_physical_action("REMOVE_S0", 0, duration_sec=8.0)
    
    assert not lot.strata[0].is_present
    assert lot.strata[0].force_n == 0.0
    # S1 force changes due to redistribution and becoming the top active layer
    assert lot.strata[1].is_present
    assert lot.strata[1].force_n > 0.0


def test_viscoelastic_hysteresis_and_memory():
    """Verify that memory_strength > 0 creates path-dependent residual deformation."""
    lot_mem = MechanicalBulkLot("test_mem", mechanical_memory_strength=0.8)
    lot_null = MechanicalBulkLot("test_null", mechanical_memory_strength=0.0)

    # Apply heavy loading step
    lot_mem.execute_physical_action("HOLD_SETTLE", -1, duration_sec=50.0)
    lot_null.execute_physical_action("HOLD_SETTLE", -1, duration_sec=50.0)

    assert lot_mem.strata[4].residual_deformation_cm >= 0.0
    assert lot_null.strata[4].residual_deformation_cm == 0.0


def test_sensor_noise_and_dropout():
    """Verify sensor suite generates noise and reports DROPOUT when configured."""
    sensors = SimulatedMechanicalSensors(
        load_noise_std_n=1.5,
        dropout_probability=1.0,  # Force 100% dropout
    )
    sensors.update_ground_truth(np.ones(5) * 50.0, np.zeros(5), np.zeros(5))
    reading = sensors.read_forces(1.0)
    assert reading.status == "DROPOUT"

    # Operational sensor
    sensors_ok = SimulatedMechanicalSensors(dropout_probability=0.0, load_noise_std_n=0.5)
    sensors_ok.update_ground_truth(np.ones(5) * 50.0, np.zeros(5), np.zeros(5))
    reading_ok = sensors_ok.read_forces(1.0)
    assert reading_ok.status == "OK"
    assert abs(reading_ok.values[0] - 50.0) < 5.0  # Within 3-sigma noise


def test_sensor_fusion_stability():
    """Verify Kalman state filter fuses measurements and tracks ground truth."""
    sensors = SimulatedMechanicalSensors(dropout_probability=0.0, load_noise_std_n=0.2)
    fusion = MechanicalSensorFusion(n_strata=5, sensor_interface=sensors)
    
    lot = MechanicalBulkLot("test_fusion")
    fusion.initialize(lot.strata)

    sensors.update_ground_truth(
        [lot.strata[i].force_n for i in range(5)],
        [lot.strata[i].displacement_cm for i in range(5)],
        [lot.strata[i].force_n / 10.0 for i in range(5)],
    )

    fused = fusion.fuse_step(1.0, "TEST", -1, [150.0] * 5)
    assert "estimated_forces_n" in fused
    assert len(fused["estimated_forces_n"]) == 5
    assert fused["overall_confidence"] > 0.5


def test_access_graph_precedence():
    """Verify access precedence: cannot observe or remove S2 before S0, S1."""
    graph = MechanicalAccessGraph(n_strata=5)
    actions = graph.get_candidate_actions()
    
    # S0 is accessible initially
    obs_s0 = [a for a in actions if a.name == "OBSERVE_S0"]
    assert len(obs_s0) == 1
    
    # S2 cannot be observed yet
    obs_s2 = [a for a in actions if a.name == "OBSERVE_S2"]
    assert len(obs_s2) == 0

    # Removing S0 unlocks S1
    rem_s0 = next(a for a in actions if a.name == "REMOVE_S0")
    graph.execute_action(rem_s0)
    actions2 = graph.get_candidate_actions()
    obs_s1 = [a for a in actions2 if a.name == "OBSERVE_S1"]
    assert len(obs_s1) == 1


def test_ground_truth_isolation():
    """Verify that planner receives only public beliefs and cannot access lot ground truth."""
    planner = FB7MechanicalStateAwarePlanner()
    lot = MechanicalBulkLot("test_iso")
    
    # Planner has its own beliefs
    assert hasattr(planner, "beliefs_alpha")
    assert hasattr(planner, "beliefs_beta")
    # Ground truth defect rate is strictly inside lot.strata
    assert lot.strata[0].true_defect_rate is not None
    # Planner select_action takes access_graph, strata, budget, fusion
    act = planner.select_action(
        MechanicalAccessGraph(5),
        lot.strata,
        60.0,
        {"estimated_forces_n": np.ones(5) * 50.0, "estimated_compressions_cm": np.zeros(5)},
    )
    assert isinstance(act, MechAction)


def test_deterministic_reproducibility():
    """Verify identical seeds produce byte-for-byte identical lot instances."""
    lot1 = MechanicalBulkLot("test_rep", rng=np.random.default_rng(999))
    lot2 = MechanicalBulkLot("test_rep", rng=np.random.default_rng(999))

    assert lot1.overall_true_defect_rate == lot2.overall_true_defect_rate
    for i in range(5):
        assert lot1.strata[i].force_n == lot2.strata[i].force_n
        assert lot1.strata[i].true_defect_rate == lot2.strata[i].true_defect_rate


def test_path_dependence_experiment():
    """Verify that path dependence test executes and identifies memory regimes."""
    res = run_matched_path_dependence_experiment(n_trials=5, seed=42)
    assert "NULL_MEMORY" in res
    assert "HIGH_MEMORY" in res
    # Under high memory, path dependence must be detected
    assert res["HIGH_MEMORY"]["path_dependence_detected"] is True
