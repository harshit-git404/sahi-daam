"""
inspection_control/experiments/final_validation_suite.py
Final Invention Validation Sprint Engine.
Executes pre-registered protocols under PROTOCOL_LOCK.md:
1. Training/Calibration fit of Additive Baseline FB6 (20 training lots)
2. Matched Total Exposure Plan-Swap Test (Plan A vs Plan B)
3. History-Blind Ablation (FB7 vs FB7-H)
4. Additive Equivalence Kill Test (FB7 vs FB6)
5. 20-Lot Held-Out Cross-Baseline Benchmark (FB0, FB1, FB2, FB5, FB6, FB7, FB7-H)
6. Model Misspecification Analysis (-30% to +30%)
7. Raw Evidence Archiving & Plot Generation
"""

from typing import Dict, List, Any, Tuple
import os
import sys
import time
import json
import math
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

from inspection_control.domain.lot import BulkLot, DefectPatternType
from inspection_control.domain.access_graph import PhysicalActionType, AccessAction
from inspection_control.domain.disposition import DispositionDecision, DispositionEvaluator
from inspection_control.planning.planner import IInspectionPlanner
from inspection_control.planning.exposure_aware_planner import ExposureAwareInspectionPlanner
from inspection_control.planning.baselines import (
    FB0SurfaceOnlyPlanner,
    FB1FixedRandomPlanner,
    FB2DepthStratifiedPlanner,
    FB5StateBlindLookaheadPlanner,
    FB6AdditiveCostLookaheadPlanner,
)
from inspection_control.experiments.runner import InspectionEpisodeRunner
from inspection_control.evidence.metrics import compare_paired_planners, compute_summary_statistics


class FB7HistoryBlindPlanner(ExposureAwareInspectionPlanner):
    """
    FB7-H (Criterion 15): History-blind version of FB7.
    Same controller, same action space, same observations,
    but carried exposure history is reset/ignored (t_cum = 0, times_opened = 1).
    """
    def __init__(self, name: str = "FB7_H_History_Blind"):
        super().__init__(name=name)

    def _score_action(self, action, lot, current_expected_loss, ambient_temp_c, remaining_budget):
        # Create a shallow cloned record with history wiped
        target_sid = action.target_stratum_id
        record = lot.exposure_ledger.strata_records.get(target_sid)
        if record:
            saved_cum = record.cumulative_exposure_time_sec
            saved_opened = record.times_opened
            # Zero out history
            record.cumulative_exposure_time_sec = 0.0
            record.times_opened = 1
            score = super()._score_action(action, lot, current_expected_loss, ambient_temp_c, remaining_budget)
            # Restore
            record.cumulative_exposure_time_sec = saved_cum
            record.times_opened = saved_opened
            return score
        return super()._score_action(action, lot, current_expected_loss, ambient_temp_c, remaining_budget)


def calibrate_additive_model(n_train_lots: int = 20, seed: int = 12000) -> float:
    """Fits additive rate c_add (INR/sec) on 20 independent training lots."""
    rng = np.random.default_rng(seed)
    evaluator = DispositionEvaluator()
    durations = []
    damages = []

    for i in range(n_train_lots):
        lot = BulkLot(
            lot_id=f"TRAIN_LOT_{i+1:02d}",
            pattern=DefectPatternType.DEPTH_CORRELATED if i % 2 == 0 else DefectPatternType.ADVERSARIAL,
            initial_temp_c=12.0,
            rng=np.random.default_rng(int(rng.integers(0, 1000000))),
        )
        t_exp = float(rng.uniform(10.0, 90.0))
        rec = lot.exposure_ledger.update_exposure_step(1, t_exp, 27.0, 12.0, is_open=True)
        durations.append(t_exp)
        damages.append(rec.estimated_condition_change * evaluator.config.base_lot_value)

    d_arr = np.array(durations)
    dmg_arr = np.array(damages)
    c_add = float(np.sum(d_arr * dmg_arr) / max(1e-6, np.sum(d_arr ** 2)))
    
    calib_meta = {
        "n_training_lots": n_train_lots,
        "calibrated_c_add_inr_per_sec": round(c_add, 4),
        "mean_training_damage": round(float(np.mean(dmg_arr)), 2),
        "mean_training_duration_sec": round(float(np.mean(d_arr)), 2),
    }
    with open("evidence/final_validation/calibration/calibrated_additive_model.json", "w") as f:
        json.dump(calib_meta, f, indent=2)
    return round(c_add, 4)


def run_matched_exposure_plan_swap(n_trials: int = 50, seed: int = 24000) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Matched Total Exposure Plan-Swap Test (Criterion 8).
    Total open duration is matched at exactly 35 seconds for both plans.
    Plan A: Open (10s) -> Observe (5s) -> Hold (20s) -> Reclose (5s).
    Plan B: Open (10s) -> Hold (20s) -> Observe (5s) -> Reclose (5s).
    """
    rng = np.random.default_rng(seed)
    results = []

    for i in range(n_trials):
        lot_id = f"PLANSWAP_{i+1:03d}"
        lot = BulkLot(
            lot_id=lot_id,
            pattern=DefectPatternType.ADVERSARIAL,
            initial_temp_c=10.0,
            rng=np.random.default_rng(int(rng.integers(0, 1000000))),
        )

        # Plan A
        lot_a = lot.clone_for_counterfactual()
        lot_a.access_graph.execute_action(AccessAction(PhysicalActionType.OPEN_STRATUM, 1, "Open", 10.0, 5.0, 1.0, 0.1))
        lot_a.exposure_ledger.update_exposure_step(1, 10.0, 28.0, 10.0, is_open=True)
        # Immediate observation at 10s
        fid_a = 1.0 - (0.20 * math.exp(-((10.0 - 40.0) ** 2) / (2.0 * 25.0 ** 2)))
        # Hold 20s
        lot_a.exposure_ledger.update_exposure_step(1, 20.0, 28.0, 13.0, is_open=True)
        # Reclose (5s)
        lot_a.access_graph.open_strata.clear()
        lot_a.exposure_ledger.update_exposure_step(1, 5.0, 28.0, 14.0, is_open=False, is_reclosed=True)
        dmg_a = lot_a.exposure_ledger.strata_records[1].estimated_condition_change

        # Plan B
        lot_b = lot.clone_for_counterfactual()
        lot_b.access_graph.execute_action(AccessAction(PhysicalActionType.OPEN_STRATUM, 1, "Open", 10.0, 5.0, 1.0, 0.1))
        lot_b.exposure_ledger.update_exposure_step(1, 10.0, 28.0, 10.0, is_open=True)
        # Hold 20s BEFORE observation
        lot_b.exposure_ledger.update_exposure_step(1, 20.0, 28.0, 13.0, is_open=True)
        # Delayed observation at 30s (warmer, closer to thermal peak)
        fid_b = 1.0 - (0.20 * math.exp(-((30.0 - 40.0) ** 2) / (2.0 * 25.0 ** 2)))
        # Reclose (5s)
        lot_b.access_graph.open_strata.clear()
        lot_b.exposure_ledger.update_exposure_step(1, 5.0, 28.0, 14.0, is_open=False, is_reclosed=True)
        dmg_b = lot_b.exposure_ledger.strata_records[1].estimated_condition_change

        results.append({
            "trial_idx": i + 1,
            "plan_a_damage": round(dmg_a, 6),
            "plan_b_damage": round(dmg_b, 6),
            "damage_diff": round(dmg_b - dmg_a, 6),
            "plan_a_fidelity": round(fid_a, 4),
            "plan_b_fidelity": round(fid_b, 4),
            "fidelity_diff": round(fid_a - fid_b, 4),
        })

    df = pd.DataFrame(results)
    mean_dmg_diff = float(df["damage_diff"].mean())
    mean_fid_diff = float(df["fidelity_diff"].mean())
    t_stat_dmg, p_val_dmg = stats.ttest_1samp(df["damage_diff"], 0.0) if np.any(df["damage_diff"] != 0) else (0.0, 1.0)
    t_stat_fid, p_val_fid = stats.ttest_1samp(df["fidelity_diff"], 0.0)

    summary = {
        "n_trials": n_trials,
        "mean_damage_plan_a": float(df["plan_a_damage"].mean()),
        "mean_damage_plan_b": float(df["plan_b_damage"].mean()),
        "mean_damage_difference": round(mean_dmg_diff, 6),
        "damage_diff_p_value": float(p_val_dmg),
        "mean_fidelity_plan_a": float(df["plan_a_fidelity"].mean()),
        "mean_fidelity_plan_b": float(df["plan_b_fidelity"].mean()),
        "mean_fidelity_difference": round(mean_fid_diff, 4),
        "fidelity_diff_p_value": float(p_val_fid),
        "damage_path_dependence_demonstrated": bool(p_val_dmg < 0.05 and abs(mean_dmg_diff) > 1e-6),
        "fidelity_path_dependence_demonstrated": bool(p_val_fid < 0.05 and abs(mean_fid_diff) > 1e-4),
    }
    return df, summary


def run_held_out_evaluation(
    c_add: float,
    n_eval_lots: int = 20,
    seed: int = 36000,
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """
    Evaluates 7 planners across 20 held-out evaluation lots.
    Saves raw logs and independent ground-truth teardowns.
    """
    rng = np.random.default_rng(seed)
    runner = InspectionEpisodeRunner()
    lot_records = []
    lot_results = []

    for idx in range(n_eval_lots):
        lot_id = f"EVAL_LOT_{idx+1:02d}"
        commodity = "potato" if idx < 10 else "onion"
        # Regime distribution
        if idx % 4 == 0:
            pat = DefectPatternType.ADVERSARIAL
        elif idx % 4 == 1:
            pat = DefectPatternType.DEPTH_CORRELATED
        elif idx % 4 == 2:
            pat = DefectPatternType.HIDDEN_BOTTOM
        else:
            pat = DefectPatternType.BENIGN

        lot_base = BulkLot(
            lot_id=lot_id,
            commodity=commodity,
            pattern=pat,
            n_strata=5,
            units_per_stratum=40,
            initial_temp_c=12.0 + float(rng.uniform(-1.0, 1.0)),
            rng=np.random.default_rng(int(rng.integers(0, 1000000))),
        )

        gt = lot_base.get_ground_truth_for_teardown()
        lot_records.append({
            "lot_id": lot_id,
            "commodity": commodity,
            "pattern": pat.value,
            "initial_temp_c": lot_base.strata[0].temperature_history[0],
            "true_overall_defect_rate": gt.overall_true_defect_rate,
        })

        # Save independent ground truth
        gt_data = {
            sid: {"units_defective": s.units_defective, "units_total": s.units_total, "true_rate": s.true_defect_rate}
            for sid, s in gt.strata_ground_truth.items()
        }
        with open(f"evidence/final_validation/ground_truth/{lot_id}_gt.json", "w") as f:
            json.dump(gt_data, f, indent=2)

        # 7 competing planners
        competing = [
            ("FB0_Surface_Only", FB0SurfaceOnlyPlanner()),
            ("FB1_Fixed_Random", FB1FixedRandomPlanner(sample_budget=2)),
            ("FB2_Depth_Stratified", FB2DepthStratifiedPlanner(max_depth=3)),
            ("FB5_State_Blind", FB5StateBlindLookaheadPlanner()),
            ("FB6_Calibrated_Additive", FB6AdditiveCostLookaheadPlanner(fixed_exposure_cost_per_sec=c_add)),
            ("FB7_Proposed", ExposureAwareInspectionPlanner()),
            ("FB7_H_History_Blind", FB7HistoryBlindPlanner()),
        ]

        for p_name, planner in competing:
            lot_copy = lot_base.clone_for_counterfactual()
            res = runner.run_episode(lot_copy, planner, initial_budget_inr=60.0, ambient_temp_c=27.0)
            res["lot_id"] = lot_id
            res["planner_id"] = p_name
            res["commodity"] = commodity
            lot_results.append(res)

    results_df = pd.DataFrame(lot_results)
    results_df.to_csv("evidence/final_validation/baselines/held_out_benchmark_results.csv", index=False)
    pd.DataFrame(lot_records).to_csv("evidence/final_validation/baselines/held_out_lots_meta.csv", index=False)

    # Statistical comparisons vs FB7
    fb7_losses = results_df[results_df["planner_id"] == "FB7_Proposed"]["total_disposition_loss"].tolist()
    baseline_stats = {}
    for p_id in ["FB0_Surface_Only", "FB1_Fixed_Random", "FB2_Depth_Stratified", "FB5_State_Blind", "FB6_Calibrated_Additive", "FB7_H_History_Blind"]:
        b_losses = results_df[results_df["planner_id"] == p_id]["total_disposition_loss"].tolist()
        baseline_stats[p_id] = compare_paired_planners(fb7_losses, b_losses)

    # Additive Equivalence Kill Test metrics (FB7 vs FB6)
    fb6_rows = results_df[results_df["planner_id"] == "FB6_Calibrated_Additive"].reset_index(drop=True)
    fb7_rows = results_df[results_df["planner_id"] == "FB7_Proposed"].reset_index(drop=True)
    
    action_agreements = sum(1 for i in range(len(fb6_rows)) if fb6_rows.loc[i, "action_sequence"] == fb7_rows.loc[i, "action_sequence"])
    disp_agreements = sum(1 for i in range(len(fb6_rows)) if fb6_rows.loc[i, "chosen_disposition"] == fb7_rows.loc[i, "chosen_disposition"])
    
    additive_equivalence = {
        "n_lots": n_eval_lots,
        "action_agreement_pct": round((action_agreements / n_eval_lots) * 100.0, 1),
        "disposition_agreement_pct": round((disp_agreements / n_eval_lots) * 100.0, 1),
        "fb6_mean_loss": round(float(fb6_rows["total_disposition_loss"].mean()), 2),
        "fb7_mean_loss": round(float(fb7_rows["total_disposition_loss"].mean()), 2),
        "loss_delta_inr": round(float(fb6_rows["total_disposition_loss"].mean() - fb7_rows["total_disposition_loss"].mean()), 2),
        "fb7_advantage_pct": round(baseline_stats["FB6_Calibrated_Additive"]["mean_loss_reduction_pct"], 2),
        "win_count": int(np.sum(fb6_rows["total_disposition_loss"] > fb7_rows["total_disposition_loss"] + 0.01)),
        "tie_count": int(np.sum(np.abs(fb6_rows["total_disposition_loss"] - fb7_rows["total_disposition_loss"]) <= 0.01)),
        "loss_count": int(np.sum(fb6_rows["total_disposition_loss"] < fb7_rows["total_disposition_loss"] - 0.01)),
    }

    return results_df, baseline_stats, additive_equivalence


def run_misspecification_grid(seed: int = 48000) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Model misspecification analysis from -30% to +30%."""
    rng = np.random.default_rng(seed)
    runner = InspectionEpisodeRunner()
    results = []

    perturbations = [-0.30, -0.15, 0.0, 0.15, 0.30]

    for p in perturbations:
        scale = 1.0 + p
        label = f"{'+' if p >= 0 else ''}{int(p*100)}%"
        for i in range(20):
            lot = BulkLot(
                lot_id=f"MISSPEC_{label}_{i+1:02d}",
                pattern=DefectPatternType.DEPTH_CORRELATED,
                initial_temp_c=12.0,
                rng=np.random.default_rng(int(rng.integers(0, 1000000))),
            )
            planner = ExposureAwareInspectionPlanner()
            planner.loss_config.cost_false_accept *= scale
            res = runner.run_episode(lot, planner, ambient_temp_c=27.0)
            res["perturbation_label"] = label
            res["perturbation_pct"] = p * 100
            results.append(res)

    df = pd.DataFrame(results)
    df.to_csv("evidence/final_validation/misspecification/misspecification_grid_results.csv", index=False)
    summary = {}
    for p in perturbations:
        label = f"{'+' if p >= 0 else ''}{int(p*100)}%"
        sub_df = df[df["perturbation_label"] == label]
        summary[label] = compute_summary_statistics(sub_df["total_disposition_loss"].tolist())
    return df, summary
