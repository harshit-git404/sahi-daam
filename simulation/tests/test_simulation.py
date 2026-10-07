import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import pytest

from simulation.environment.lot import BulkPerishableLot, DefectPattern, LotConfig, PresentationBias
from simulation.environment.access_graph import AccessGraph, ActionType
from simulation.environment.dynamics import LotDynamicsEngine
from simulation.models.stratum_model import HiddenStratumConditionModel
from simulation.models.disposition import DispositionEvaluator, DispositionDecision
from simulation.baselines.b0_surface import B0SurfaceOnlyPlanner
from simulation.baselines.b4_myopic_voi import B4MyopicVOIPlanner
from simulation.planners.b7_proposed import B7ProposedPlanner
from simulation.experiments.runner import SimulationTrialRunner


def test_lot_initialization_and_cloning():
    cfg = LotConfig(n_strata=5, units_per_stratum=100, defect_pattern=DefectPattern.DEPTH_CORRELATED)
    lot = BulkPerishableLot(config=cfg, rng=np.random.default_rng(42))
    assert len(lot.strata) == 5
    assert lot.total_units == 500
    assert 0.0 < lot.ground_truth_defect_prevalence < 1.0

    clone = lot.clone()
    assert clone.total_units == lot.total_units
    assert clone.ground_truth_defect_prevalence == lot.ground_truth_defect_prevalence


def test_access_graph_precedence():
    graph = AccessGraph(n_strata=5)
    # Initially only stratum 0 is accessible and exposed
    actions = graph.get_valid_actions({0}, {0}, set())
    action_types = {a.action_type for a in actions}

    # Should contain surface inspection, sampling stratum 0, secondary sensor on 0, and remove_layer 0
    assert ActionType.INSPECT_SURFACE in action_types
    assert ActionType.SAMPLE_UNITS in action_types
    assert ActionType.REMOVE_LAYER in action_types
    assert ActionType.STOP_INSPECTION in action_types

    # Should NOT be able to sample stratum 1 or 2 yet
    for a in actions:
        if a.action_type == ActionType.SAMPLE_UNITS:
            assert a.target_stratum == 0


def test_dynamics_layer_removal_yields_zero_immediate_info():
    cfg = LotConfig(n_strata=5)
    lot = BulkPerishableLot(config=cfg)
    dynamics = LotDynamicsEngine()
    graph = AccessGraph(n_strata=5)

    valid = graph.get_valid_actions({0}, {0}, set())
    rem_act = [a for a in valid if a.action_type == ActionType.REMOVE_LAYER][0]

    yield_data, removed, accessible, exposed = dynamics.transition(lot, rem_act, set(), {0}, {0})
    assert yield_data.data_type == "none"
    assert yield_data.sample_count == 0
    assert 0 in removed
    assert 1 in accessible
    assert 1 in exposed


def test_bayesian_condition_model_updates():
    model = HiddenStratumConditionModel(n_strata=5)
    init_mean = model.posteriors[1].mean
    init_var = model.posteriors[1].variance

    # Update stratum 1 with high defects (10 defects out of 10 samples)
    model.update_from_unit_samples(1, 10, 10)
    assert model.posteriors[1].mean > init_mean
    assert model.posteriors[1].variance < init_var


def test_disposition_evaluation():
    evaluator = DispositionEvaluator()
    # 5% defect rate should be optimally ACCEPT
    assert evaluator.get_optimal_disposition(0.05) == DispositionDecision.ACCEPT
    # 15% defect rate should be optimally MARKDOWN
    assert evaluator.get_optimal_disposition(0.15) == DispositionDecision.MARKDOWN
    # 30% defect rate should be optimally REROUTE
    assert evaluator.get_optimal_disposition(0.30) == DispositionDecision.REROUTE
    # 50% defect rate should be optimally REJECT
    assert evaluator.get_optimal_disposition(0.50) == DispositionDecision.REJECT


def test_planners_single_trial():
    lot = BulkPerishableLot()
    runner = SimulationTrialRunner()

    p_b0 = B0SurfaceOnlyPlanner()
    m_b0 = runner.run_single_trial(p_b0, lot, 100)
    assert m_b0.steps_count >= 1

    p_b4 = B4MyopicVOIPlanner()
    m_b4 = runner.run_single_trial(p_b4, lot, 100)
    assert m_b4.steps_count >= 0

    p_b7 = B7ProposedPlanner()
    m_b7 = runner.run_single_trial(p_b7, lot, 100)
    assert m_b7.steps_count >= 1
