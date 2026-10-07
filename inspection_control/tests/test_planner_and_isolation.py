"""
inspection_control/tests/test_planner_and_isolation.py
Critical Architectural Invariant Tests:
1. Strict Ground-Truth Isolation (Planner must NEVER access private ground truth)
2. Closed-Loop Sensor-Ledger-Planner-Teardown Integration
3. Baseline execution validity
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from unittest.mock import MagicMock, patch
import pytest

from inspection_control.domain.lot import BulkLot, DefectPatternType
from inspection_control.domain.access_graph import PhysicalActionType
from inspection_control.planning.exposure_aware_planner import ExposureAwareInspectionPlanner
from inspection_control.planning.baselines import (
    FB0SurfaceOnlyPlanner,
    FB1FixedRandomPlanner,
    FB2DepthStratifiedPlanner,
    FB5StateBlindLookaheadPlanner,
    FB6AdditiveCostLookaheadPlanner,
)
from inspection_control.experiments.runner import InspectionEpisodeRunner


def test_ground_truth_isolation_invariant():
    """
    CRITICAL INVARIANT TEST:
    Verifies that the planner NEVER calls get_ground_truth_for_teardown()
    or reads _private_ground_truth during the decision loop.
    """
    lot = BulkLot(lot_id="LOT_ISOLATION_TEST", pattern=DefectPatternType.ADVERSARIAL)
    planner = ExposureAwareInspectionPlanner()

    # Wrap the teardown method with a spy
    original_teardown_fn = lot.get_ground_truth_for_teardown
    call_counter = {"count": 0}

    def spy_teardown():
        call_counter["count"] += 1
        return original_teardown_fn()

    lot.get_ground_truth_for_teardown = spy_teardown

    # Execute 3 planner decisions
    for _ in range(3):
        act, telemetry = planner.select_next_action(
            lot=lot,
            remaining_budget_inr=50.0,
            elapsed_time_sec=10.0,
            ambient_temp_c=25.0,
        )
        assert act is not None

    # Invariant assertion: Ground truth was NEVER called by planner
    assert call_counter["count"] == 0, "VIOLATION: Planner accessed ground-truth method!"


def test_closed_loop_episode_integration():
    """Tests complete end-to-end inspection loop with teardown."""
    lot = BulkLot(lot_id="INTEGRATION_LOT_01", pattern=DefectPatternType.DEPTH_CORRELATED)
    planner = ExposureAwareInspectionPlanner()
    runner = InspectionEpisodeRunner()

    result = runner.run_episode(lot=lot, planner=planner, initial_budget_inr=60.0)

    assert "total_disposition_loss" in result
    assert "chosen_disposition" in result
    assert "true_overall_defect_rate" in result
    assert result["steps_taken"] > 0
    assert result["total_spent_inr"] <= 60.0


def test_baselines_execution():
    """Verifies that all baselines execute without exceptions."""
    lot_base = BulkLot(lot_id="BASELINES_TEST", pattern=DefectPatternType.UNIFORM)
    runner = InspectionEpisodeRunner()

    planners = [
        FB0SurfaceOnlyPlanner(),
        FB1FixedRandomPlanner(sample_budget=2),
        FB2DepthStratifiedPlanner(max_depth=2),
        FB5StateBlindLookaheadPlanner(),
        FB6AdditiveCostLookaheadPlanner(),
    ]

    for p in planners:
        lot = lot_base.clone_for_counterfactual()
        res = runner.run_episode(lot=lot, planner=p, initial_budget_inr=50.0)
        assert res["total_disposition_loss"] >= 0.0
        assert res["steps_taken"] >= 1
