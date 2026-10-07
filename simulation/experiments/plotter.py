"""
simulation/experiments/plotter.py
Visualizations generator for the Kill-Test Simulation Suite.
Produces publication-quality figures saved to simulation/plots/.
"""

import os
from typing import Dict, List
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def generate_all_plots(
    benchmark_df: pd.DataFrame,
    myopic_df: pd.DataFrame,
    ablation_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    output_dir: str = "simulation/plots",
) -> None:
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # 1. MYOPIC TRAP PLOT
    _plot_myopic_trap(myopic_df, os.path.join(output_dir, "myopic_trap.png"))

    # 2. BENCHMARK COMPARISON PLOT
    _plot_benchmark(benchmark_df, os.path.join(output_dir, "benchmark_comparison.png"))

    # 3. ABLATION STUDY PLOT
    _plot_ablation(ablation_df, os.path.join(output_dir, "ablation_study.png"))

    # 4. STRESS TESTS PLOT
    _plot_stress_tests(stress_df, os.path.join(output_dir, "stress_tests.png"))


def _plot_myopic_trap(df: pd.DataFrame, out_path: str) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), dpi=150)
    b4 = df[df["planner_name"] == "B4_Myopic_VOI"]
    b7 = df[df["planner_name"] == "B7_Proposed"]

    # Total Loss Boxplot / Bar
    means = [b4["total_loss"].mean(), b7["total_loss"].mean()]
    stds = [b4["total_loss"].std(), b7["total_loss"].std()]
    axes[0].bar(["B4: Myopic VOI", "B7: Proposed Planner"], means, yerr=stds, capsize=5, color=["#dc2626", "#16a34a"], alpha=0.85)
    axes[0].set_ylabel("Total Economic Loss (INR)")
    axes[0].set_title("Total Expected Loss\n(Lower is Better)", fontweight="bold")
    for idx, v in enumerate(means):
        axes[0].text(idx, v * 0.5, f"₹{v:.1f}", ha="center", color="white", fontweight="bold")

    # False Accept Rate
    fa_rates = [b4["is_false_accept"].mean() * 100.0, b7["is_false_accept"].mean() * 100.0]
    axes[1].bar(["B4: Myopic VOI", "B7: Proposed Planner"], fa_rates, color=["#dc2626", "#16a34a"], alpha=0.85)
    axes[1].set_ylabel("False Accept Rate (%)")
    axes[1].set_title("False Accept Rate\n(Rot Entering Inventory)", fontweight="bold")
    for idx, v in enumerate(fa_rates):
        axes[1].text(idx, max(2.0, v * 0.5), f"{v:.1f}%", ha="center", color="white", fontweight="bold")

    # Access Operations (Layer Removals)
    access_ops = [b4["access_operations_count"].mean(), b7["access_operations_count"].mean()]
    axes[2].bar(["B4: Myopic VOI", "B7: Proposed Planner"], access_ops, color=["#dc2626", "#16a34a"], alpha=0.85)
    axes[2].set_ylabel("Layer Excavations (Count)")
    axes[2].set_title("Deep Access Operations\n(Overcoming Myopic Trap)", fontweight="bold")
    for idx, v in enumerate(access_ops):
        axes[2].text(idx, max(0.1, v * 0.5), f"{v:.2f}", ha="center", color="white", fontweight="bold")

    plt.suptitle("KILL-TEST: Myopic Trap Experiment (Surface Clean, Deep Rot Hidden)", fontsize=13, fontweight="bold", y=1.03)
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()


def _plot_benchmark(df: pd.DataFrame, out_path: str) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), dpi=150)
    order = [
        "B0_Surface_Only",
        "B1_Fixed_Random",
        "B2_Depth_Stratified",
        "B3_Sahi_Daam_Heuristic",
        "B4_Myopic_VOI",
        "B5_Lookahead_VOI",
        "B6_Access_Aware",
        "B7_Proposed",
    ]
    labels = ["B0\nSurface", "B1\nRandom", "B2\nDepth", "B3\nSahiDaam", "B4\nMyopic", "B5\nLookahead", "B6\nAccess", "B7\nProposed"]
    colors = ["#94a3b8", "#94a3b8", "#94a3b8", "#f59e0b", "#ef4444", "#3b82f6", "#6366f1", "#10b981"]

    grp = df.groupby("planner_name")
    losses = [grp.get_group(p)["total_loss"].mean() for p in order]
    fas = [grp.get_group(p)["is_false_accept"].mean() * 100.0 for p in order]
    costs = [grp.get_group(p)["inspection_monetary_cost"].mean() for p in order]
    times = [grp.get_group(p)["inspection_time_minutes"].mean() for p in order]

    axes[0, 0].bar(labels, losses, color=colors, alpha=0.85)
    axes[0, 0].set_ylabel("Total Loss (INR)")
    axes[0, 0].set_title("Expected Total Loss (Primary Metric)", fontweight="bold")

    axes[0, 1].bar(labels, fas, color=colors, alpha=0.85)
    axes[0, 1].set_ylabel("False Accept Rate (%)")
    axes[0, 1].set_title("False Accept Rate (Rot Escaping Inspection)", fontweight="bold")

    axes[1, 0].bar(labels, costs, color=colors, alpha=0.85)
    axes[1, 0].set_ylabel("Inspection Cost (INR)")
    axes[1, 0].set_title("Monetary Inspection Cost Incurred", fontweight="bold")

    axes[1, 1].bar(labels, times, color=colors, alpha=0.85)
    axes[1, 1].set_ylabel("Time (Minutes)")
    axes[1, 1].set_title("Physical Inspection Duration", fontweight="bold")

    plt.suptitle("Benchmark Comparison Across Planners B0 through B7", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()


def _plot_ablation(df: pd.DataFrame, out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    grp = df.groupby("ablation_variant")["total_loss"].mean().sort_values(ascending=False)
    variants = grp.index.tolist()
    values = grp.values.tolist()

    # Highlight Full_B7 in green, others in slate
    colors = ["#10b981" if v == "Full_B7" else "#64748b" for v in variants]
    bars = ax.barh(variants, values, color=colors, alpha=0.85)
    ax.set_xlabel("Total Expected Loss (INR) — Lower is Better")
    ax.set_title("Ablation Study: Economic Loss When Individual Mechanisms Are Stripped", fontweight="bold")

    for bar, val in zip(bars, values):
        ax.text(val + 10, bar.get_y() + bar.get_height() / 2, f"₹{val:.1f}", va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()


def _plot_stress_tests(df: pd.DataFrame, out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(12, 6), dpi=150)
    cases = sorted(df["stress_case"].unique())
    p_b7 = df[df["planner_name"] == "B7_Proposed"].groupby("stress_case")["total_loss"].mean()
    p_b4 = df[df["planner_name"] == "B4_Myopic_VOI"].groupby("stress_case")["total_loss"].mean()
    p_b2 = df[df["planner_name"] == "B2_Depth_Stratified"].groupby("stress_case")["total_loss"].mean()

    x = np.arange(len(cases))
    width = 0.25

    ax.bar(x - width, [p_b4.get(c, 0) for c in cases], width, label="B4: Myopic VOI", color="#ef4444", alpha=0.8)
    ax.bar(x, [p_b2.get(c, 0) for c in cases], width, label="B2: Depth Stratified", color="#f59e0b", alpha=0.8)
    ax.bar(x + width, [p_b7.get(c, 0) for c in cases], width, label="B7: Proposed Planner", color="#10b981", alpha=0.85)

    ax.set_xticks(x)
    clean_labels = [c.replace("Case_", "C").replace("_", "\n") for c in cases]
    ax.set_xticklabels(clean_labels, fontsize=8)
    ax.set_ylabel("Total Loss (INR)")
    ax.set_title("Stress Tests: B7 vs Baselines Across 12 Operational Regimes", fontweight="bold")
    ax.legend()

    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
