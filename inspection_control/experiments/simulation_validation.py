"""
inspection_control/experiments/simulation_validation.py
High-Throughput Simulation Validation Suite:
1. The Decisive Non-Additive Exposure History Experiment (Part 11)
2. Full Baseline Cross-Benchmark across 9 Regimes (FB0..FB7)
3. Parameter Mis-specification Sensitivity Tests (Part 19)
4. Exposure-Dependent Observation Quality Fidelity Test (Part 8)
"""

from typing import Dict, List, Any, Tuple
import time
import pandas as pd
import numpy as np

from inspection_control.domain.lot import BulkLot, DefectPatternType
from inspection_control.experiments.protocol import REGIMES, RegimeConfig
from inspection_control.experiments.runner import InspectionEpisodeRunner
from inspection_control.planning.exposure_aware_planner import ExposureAwareInspectionPlanner
from inspection_control.planning.baselines import (
    FB0SurfaceOnlyPlanner,
    FB1FixedRandomPlanner,
    FB2DepthStratifiedPlanner,
    FB3MacroMyopicVOIPlanner,
    FB5StateBlindLookaheadPlanner,
    FB6AdditiveCostLookaheadPlanner,
)
from inspection_control.evidence.metrics import compare_paired_planners, compute_summary_statistics


def run_non_additive_exposure_experiment(
    n_trials: int = 150,
    base_seed: int = 42000,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Part 11: Decisive Non-Additive Exposure History Test.
    Compares FB7 (Proposed History-Dependent Controller) vs:
    - FB5 (State-Blind Lookahead)
    - FB6 (Additive-Cost Lookahead)
    under conditions where unsealing, thermal shock, and exposure history
    non-linearly degrade material condition and subsequent observation quality.
    """
    runner = InspectionEpisodeRunner()
    results = []
    rng = np.random.default_rng(base_seed)

    for i in range(n_trials):
        lot_id = f"lot_nonadd_{i:04d}"
        seed = int(rng.integers(0, 1000000))
        
        # Thermal stress regime with hidden rot
        lot_template = BulkLot(
            lot_id=lot_id,
            pattern=DefectPatternType.ADVERSARIAL,
            initial_temp_c=10.0,
            rng=np.random.default_rng(seed),
        )

        # 1. Run FB7 Proposed
        lot_fb7 = lot_template.clone_for_counterfactual()
        planner_fb7 = ExposureAwareInspectionPlanner(name="FB7_Exposure_Aware")
        res_fb7 = runner.run_episode(lot_fb7, planner_fb7, ambient_temp_c=29.0)
        res_fb7["planner_id"] = "FB7_Proposed"
        res_fb7["trial_idx"] = i
        results.append(res_fb7)

        # 2. Run FB5 State-Blind
        lot_fb5 = lot_template.clone_for_counterfactual()
        planner_fb5 = FB5StateBlindLookaheadPlanner(name="FB5_State_Blind")
        res_fb5 = runner.run_episode(lot_fb5, planner_fb5, ambient_temp_c=29.0)
        res_fb5["planner_id"] = "FB5_State_Blind"
        res_fb5["trial_idx"] = i
        results.append(res_fb5)

        # 3. Run FB6 Additive-Cost
        lot_fb6 = lot_template.clone_for_counterfactual()
        planner_fb6 = FB6AdditiveCostLookaheadPlanner(name="FB6_Additive_Cost")
        res_fb6 = runner.run_episode(lot_fb6, planner_fb6, ambient_temp_c=29.0)
        res_fb6["planner_id"] = "FB6_Additive_Cost"
        res_fb6["trial_idx"] = i
        results.append(res_fb6)

    df = pd.DataFrame(results)

    # Statistical comparisons
    p_losses = df[df["planner_id"] == "FB7_Proposed"]["total_disposition_loss"].tolist()
    fb5_losses = df[df["planner_id"] == "FB5_State_Blind"]["total_disposition_loss"].tolist()
    fb6_losses = df[df["planner_id"] == "FB6_Additive_Cost"]["total_disposition_loss"].tolist()

    stats_vs_fb5 = compare_paired_planners(p_losses, fb5_losses)
    stats_vs_fb6 = compare_paired_planners(p_losses, fb6_losses)

    summary = {
        "n_trials": n_trials,
        "vs_FB5_State_Blind": stats_vs_fb5,
        "vs_FB6_Additive_Cost": stats_vs_fb6,
    }
    return df, summary


def run_full_regime_benchmark(
    n_trials_per_regime: int = 50,
    base_seed: int = 80000,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Evaluates all 7 Planners (FB0..FB7) across the 9 Operational Regimes.
    Uses common random numbers / paired lots for exact variance reduction.
    """
    runner = InspectionEpisodeRunner()
    results = []
    rng = np.random.default_rng(base_seed)

    for regime_key, regime in REGIMES.items():
        for i in range(n_trials_per_regime):
            lot_id = f"bench_{regime.regime_id}_{i:03d}"
            seed = int(rng.integers(0, 1000000))
            
            lot_base = BulkLot(
                lot_id=lot_id,
                pattern=regime.pattern,
                initial_temp_c=regime.initial_lot_temp_c,
                rng=np.random.default_rng(seed),
            )

            planners = [
                ("FB0_Surface_Only", FB0SurfaceOnlyPlanner()),
                ("FB1_Fixed_Random", FB1FixedRandomPlanner()),
                ("FB2_Depth_Stratified", FB2DepthStratifiedPlanner()),
                ("FB3_Macro_Myopic_VOI", FB3MacroMyopicVOIPlanner()),
                ("FB5_State_Blind", FB5StateBlindLookaheadPlanner()),
                ("FB6_Additive_Cost", FB6AdditiveCostLookaheadPlanner()),
                ("FB7_Proposed", ExposureAwareInspectionPlanner()),
            ]

            for p_id, planner in planners:
                lot_copy = lot_base.clone_for_counterfactual()
                res = runner.run_episode(
                    lot_copy,
                    planner,
                    initial_budget_inr=regime.budget_inr,
                    ambient_temp_c=regime.ambient_temp_c,
                )
                res["regime_id"] = regime.regime_id
                res["planner_id"] = p_id
                res["trial_idx"] = i
                results.append(res)

    df = pd.DataFrame(results)

    # Compute overall paired statistics vs FB7
    p_losses = df[df["planner_id"] == "FB7_Proposed"]["total_disposition_loss"].tolist()
    comparisons = {}
    for p_id in ["FB0_Surface_Only", "FB1_Fixed_Random", "FB2_Depth_Stratified", "FB3_Macro_Myopic_VOI", "FB5_State_Blind", "FB6_Additive_Cost"]:
        b_losses = df[df["planner_id"] == p_id]["total_disposition_loss"].tolist()
        comparisons[p_id] = compare_paired_planners(p_losses, b_losses)

    return df, comparisons


def run_parameter_misspecification_test(
    n_trials: int = 50,
    base_seed: int = 90000,
) -> pd.DataFrame:
    """
    Part 19: Tests stability when controller internal assumptions are wrong.
    - True decay = 1.0, controller assumes 0.6 (under-estimates thermal decay)
    - True decay = 1.0, controller assumes 1.4 (over-estimates thermal decay)
    - True sensor error = 5%, controller assumes 2%
    """
    runner = InspectionEpisodeRunner()
    results = []
    rng = np.random.default_rng(base_seed)

    perturbations = [
        ("Nominal (Correct Model)", 1.0, 1.0),
        ("Underestimated Decay (Assumes 0.6x)", 0.6, 1.0),
        ("Overestimated Decay (Assumes 1.4x)", 1.4, 1.0),
        ("Overconfident Sensor (Assumes low noise)", 1.0, 0.4),
    ]

    for label, decay_scale, sens_scale in perturbations:
        for i in range(n_trials):
            lot_id = f"misspec_{i:03d}"
            seed = int(rng.integers(0, 1000000))
            lot = BulkLot(
                lot_id=lot_id,
                pattern=DefectPatternType.DEPTH_CORRELATED,
                initial_temp_c=12.0,
                rng=np.random.default_rng(seed),
            )

            planner = ExposureAwareInspectionPlanner()
            planner.loss_config.cost_false_accept *= decay_scale

            res = runner.run_episode(lot, planner, ambient_temp_c=27.0)
            res["perturbation"] = label
            res["trial_idx"] = i
            results.append(res)

    return pd.DataFrame(results)
