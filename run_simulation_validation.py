"""
run_simulation_validation.py
Master Orchestrator for High-Throughput Simulation Validation.
Executes:
1. The Decisive Non-Additive Exposure History Experiment (Part 11)
2. The 9-Regime Cross-Benchmark Matrix (FB0..FB7)
3. Model Parameter Misspecification Sensitivity Analysis (Part 19)
Generates evaluation CSVs and figures in evidence/
"""

import os
import sys
import time
import json
import pandas as pd
import matplotlib.pyplot as plt

from inspection_control.experiments.simulation_validation import (
    run_non_additive_exposure_experiment,
    run_full_regime_benchmark,
    run_parameter_misspecification_test,
)


def generate_evaluation_plots(
    non_add_df: pd.DataFrame,
    bench_df: pd.DataFrame,
    misspec_df: pd.DataFrame,
    output_dir: str = "evidence/plots",
):
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # 1. Plot 1: Decisive Non-Additive Exposure History Comparison
    plt.figure(figsize=(9, 5))
    planners = ["FB5_State_Blind", "FB6_Additive_Cost", "FB7_Proposed"]
    labels = ["FB5 (State-Blind)", "FB6 (Additive-Cost)", "FB7 (Proposed Exposure-Aware)"]
    colors = ["#ef4444", "#f59e0b", "#10b981"]
    
    means = [non_add_df[non_add_df["planner_id"] == p]["total_disposition_loss"].mean() for p in planners]
    stds = [non_add_df[non_add_df["planner_id"] == p]["total_disposition_loss"].std() for p in planners]
    
    bars = plt.bar(labels, means, yerr=stds, capsize=6, color=colors, alpha=0.85, edgecolor="#334155")
    plt.ylabel("Mean Total Disposition Loss (INR)", fontsize=11, fontweight="bold")
    plt.title("Part 11: Decisive Non-Additive Exposure History Experiment\n(Lower is Better)", fontsize=12, fontweight="bold")
    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., h + 2, f"₹{h:.1f}", ha="center", va="bottom", fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "non_additive_exposure_comparison.png"), dpi=200)
    plt.close()

    # 2. Plot 2: Benchmark Comparison across Planners
    plt.figure(figsize=(11, 5.5))
    bench_planners = sorted(bench_df["planner_id"].unique())
    bench_means = [bench_df[bench_df["planner_id"] == p]["total_disposition_loss"].mean() for p in bench_planners]
    bench_fa = [bench_df[bench_df["planner_id"] == p]["is_false_accept"].mean() * 100 for p in bench_planners]

    x = range(len(bench_planners))
    plt.bar(x, bench_means, color="#0284c7", alpha=0.8, edgecolor="#0f172a")
    plt.xticks(x, [p.replace("_", "\n") for p in bench_planners], fontsize=9)
    plt.ylabel("Mean Disposition Loss (INR)", fontsize=11, fontweight="bold")
    plt.title("Cross-Benchmark Performance Across 9 Operational Regimes", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "benchmark_loss_comparison.png"), dpi=200)
    plt.close()

    # 3. Plot 3: Parameter Mis-specification Robustness
    plt.figure(figsize=(10, 5))
    perturb_order = ["Nominal (Correct Model)", "Underestimated Decay (Assumes 0.6x)", "Overestimated Decay (Assumes 1.4x)", "Overconfident Sensor (Assumes low noise)"]
    p_means = [misspec_df[misspec_df["perturbation"] == p]["total_disposition_loss"].mean() for p in perturb_order]
    p_stds = [misspec_df[misspec_df["perturbation"] == p]["total_disposition_loss"].std() for p in perturb_order]
    plt.bar([p.replace(" ", "\n") for p in perturb_order], p_means, yerr=p_stds, capsize=5, color="#6366f1", alpha=0.85)
    plt.ylabel("Total Disposition Loss (INR)", fontsize=11, fontweight="bold")
    plt.title("Parameter Mis-Specification Sensitivity Analysis", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "parameter_misspecification.png"), dpi=200)
    plt.close()


def main():
    print("=" * 80)
    print("EXECUTING INSPECTION CONTROL SIMULATION VALIDATION SUITE")
    print("=" * 80)
    os.makedirs("evidence/plots", exist_ok=True)
    os.makedirs("evidence/results", exist_ok=True)

    # 1. Non-Additive Exposure History Experiment (Part 11)
    print("\n[1/3] Running Decisive Non-Additive Exposure History Experiment (150 paired trials)...")
    t0 = time.time()
    non_add_df, non_add_stats = run_non_additive_exposure_experiment(n_trials=150, base_seed=42000)
    non_add_df.to_csv("evidence/results/non_additive_experiment_results.csv", index=False)
    print(f"      Completed in {time.time() - t0:.2f}s.")
    print(f"      vs FB5 (State-Blind Lookahead): Loss Reduction = {non_add_stats['vs_FB5_State_Blind']['mean_loss_reduction_pct']:.1f}% | Cohen's d = {non_add_stats['vs_FB5_State_Blind']['cohen_d']:.2f} | p = {non_add_stats['vs_FB5_State_Blind']['p_value']:.2e} | Win Rate = {non_add_stats['vs_FB5_State_Blind']['win_rate_pct']:.1f}%")
    print(f"      vs FB6 (Additive-Cost Lookahead): Loss Reduction = {non_add_stats['vs_FB6_Additive_Cost']['mean_loss_reduction_pct']:.1f}% | Cohen's d = {non_add_stats['vs_FB6_Additive_Cost']['cohen_d']:.2f} | p = {non_add_stats['vs_FB6_Additive_Cost']['p_value']:.2e} | Win Rate = {non_add_stats['vs_FB6_Additive_Cost']['win_rate_pct']:.1f}%")

    # 2. Full Benchmark across 9 regimes
    print("\n[2/3] Running Full 9-Regime Benchmark Matrix across 7 Planners (350 trials)...")
    t0 = time.time()
    bench_df, bench_stats = run_full_regime_benchmark(n_trials_per_regime=40, base_seed=80000)
    bench_df.to_csv("evidence/results/regime_benchmark_results.csv", index=False)
    print(f"      Completed in {time.time() - t0:.2f}s.")
    for b_id, stat in bench_stats.items():
        print(f"      vs {b_id:<22}: Loss Reduction = {stat['mean_loss_reduction_pct']:>5.1f}% | Cohen's d = {stat['cohen_d']:>5.2f} | Win Rate = {stat['win_rate_pct']:>4.1f}%")

    # 3. Parameter Mis-specification Sensitivity Tests
    print("\n[3/3] Running Parameter Mis-specification Sensitivity Analysis (200 trials)...")
    t0 = time.time()
    misspec_df = run_parameter_misspecification_test(n_trials=50, base_seed=90000)
    misspec_df.to_csv("evidence/results/parameter_misspecification_results.csv", index=False)
    print(f"      Completed in {time.time() - t0:.2f}s.")

    # 4. Generate Figures
    print("\nGenerating evaluation figures in evidence/plots/...")
    generate_evaluation_plots(non_add_df, bench_df, misspec_df, output_dir="evidence/plots")
    print("      Plots generated: non_additive_exposure_comparison.png, benchmark_loss_comparison.png, parameter_misspecification.png")

    # Save summary JSON
    summary_data = {
        "non_additive_experiment": non_add_stats,
        "benchmark_summary": bench_stats,
    }
    with open("evidence/results/validation_summary.json", "w") as f:
        json.dump(summary_data, f, indent=2)

    print("\nValidation suite complete. Results stored in evidence/results/ and evidence/plots/.")


if __name__ == "__main__":
    main()
