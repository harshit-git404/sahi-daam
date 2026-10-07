"""
inspection_control/tests/test_domain_and_ledger.py
Unit tests for physical strata, non-additive exposure ledger, and access precedence graph.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
import numpy as np

from inspection_control.domain.stratum import StratumState
from inspection_control.domain.exposure_state import ExposureLedger, ExposureStage
from inspection_control.domain.access_graph import AccessGraph, PhysicalActionType, AccessAction
from inspection_control.dynamics.exposure_model import NonAdditiveExposureModel


def test_stratum_state_belief():
    s = StratumState(stratum_id=0, name="Surface", unit_count=100, physical_depth=0.0)
    assert s.expected_defect_rate == pytest.approx(0.1, abs=0.01)
    assert s.defect_variance > 0.0


def test_exposure_ledger_non_additive_dynamics():
    ledger = ExposureLedger(lot_id="LOT_TEST_01")
    ledger.initialize_strata([0, 1, 2])
    
    # 1. Fresh stratum exposure step (10s at delta T = 15 degC)
    rec_fresh = ledger.update_exposure_step(
        stratum_id=0,
        elapsed_sec=10.0,
        ambient_temp_c=25.0,
        stratum_temp_c=10.0,
        is_open=True,
    )
    change_fresh = rec_fresh.estimated_condition_change
    assert change_fresh > 0.0
    assert rec_fresh.exposure_state == ExposureStage.EXPOSED_INITIAL

    # 2. Advance exposure further (60s). Cumulative time accumulates non-additively.
    rec_aged = ledger.update_exposure_step(
        stratum_id=0,
        elapsed_sec=60.0,
        ambient_temp_c=25.0,
        stratum_temp_c=10.0,
        is_open=True,
    )
    assert rec_aged.exposure_state == ExposureStage.EXPOSED_EQUILIBRATED
    assert rec_aged.cumulative_exposure_time_sec == 70.0
    assert rec_aged.ambient_delta_integral > 0.0


def test_non_additive_exposure_model_fatigue():
    model = NonAdditiveExposureModel()
    ledger = ExposureLedger(lot_id="LOT_TEST_02")
    ledger.initialize_strata([0, 1])

    # Case A: Fresh stratum (0 sec cumulative exposure)
    rec_fresh = ledger.strata_records[0]
    impact_fresh = model.compute_marginal_exposure_impact(
        record=rec_fresh,
        action_duration_sec=15.0,
        ambient_temp_c=28.0,
        stratum_temp_c=12.0,
        is_opening_action=False,
    )

    # Case B: Heavily fatigued stratum (180 sec cumulative exposure, 3 times opened)
    rec_fatigued = ledger.strata_records[1]
    rec_fatigued.cumulative_exposure_time_sec = 180.0
    rec_fatigued.times_opened = 3
    impact_fatigued = model.compute_marginal_exposure_impact(
        record=rec_fatigued,
        action_duration_sec=15.0,
        ambient_temp_c=28.0,
        stratum_temp_c=12.0,
        is_opening_action=True,
    )

    # Non-additive property: marginal impact on fatigued stratum must be strictly greater
    assert impact_fatigued > (impact_fresh * 1.5)


def test_access_graph_precedence():
    graph = AccessGraph(n_strata=4)
    # Stratum 0 accessible initially
    assert 0 in graph.accessible_strata
    assert 1 not in graph.accessible_strata

    # Observe S0 is valid
    obs_s0 = AccessAction(
        action_type=PhysicalActionType.OBSERVE_STRATUM,
        target_stratum_id=0,
        name="Obs S0",
        duration_sec=5.0,
        physical_cost_inr=2.0,
        exposure_impact_factor=1.0,
        mechanical_disturbance=0.0,
    )
    assert graph.is_action_executable(obs_s0)

    # Observe S1 is INVALID before removal of layer
    obs_s1 = AccessAction(
        action_type=PhysicalActionType.OBSERVE_STRATUM,
        target_stratum_id=1,
        name="Obs S1",
        duration_sec=5.0,
        physical_cost_inr=2.0,
        exposure_impact_factor=1.0,
        mechanical_disturbance=0.0,
    )
    assert not graph.is_action_executable(obs_s1)

    # Remove layer 1
    remove_l1 = AccessAction(
        action_type=PhysicalActionType.REMOVE_LAYER,
        target_stratum_id=1,
        name="Remove L1",
        duration_sec=15.0,
        physical_cost_inr=8.0,
        exposure_impact_factor=2.0,
        mechanical_disturbance=0.2,
        resulting_accessible_strata=[1],
    )
    assert graph.is_action_executable(remove_l1)
    graph.execute_action(remove_l1)

    # Now S1 is accessible and executable
    assert 1 in graph.accessible_strata
    assert graph.is_action_executable(obs_s1)
