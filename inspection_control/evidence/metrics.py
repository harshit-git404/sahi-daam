"""
inspection_control/evidence/metrics.py
Statistical Metrics, Paired Significance Testing, and Bootstrap Confidence Intervals.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from scipy import stats


def compute_bootstrap_ci(data: List[float], n_bootstraps: int = 1000, ci: float = 0.95) -> Tuple[float, float]:
    """Computes percentile bootstrap confidence interval."""
    if len(data) < 2:
        val = data[0] if data else 0.0
        return val, val
    arr = np.array(data)
    boot_means = []
    rng = np.random.default_rng(42)
    for _ in range(n_bootstraps):
        sample = rng.choice(arr, size=len(arr), replace=True)
        boot_means.append(float(np.mean(sample)))
    low_pct = (1.0 - ci) / 2.0 * 100.0
    high_pct = (1.0 - (1.0 - ci) / 2.0) * 100.0
    return float(np.percentile(boot_means, low_pct)), float(np.percentile(boot_means, high_pct))


def compute_summary_statistics(values: List[float]) -> Dict[str, float]:
    """Computes mean, median, std, min, max, and 95% bootstrap CI."""
    if not values:
        return {"mean": 0.0, "median": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "ci_low": 0.0, "ci_high": 0.0}
    arr = np.array(values)
    ci_low, ci_high = compute_bootstrap_ci(values)
    return {
        "mean": round(float(np.mean(arr)), 3),
        "median": round(float(np.median(arr)), 3),
        "std": round(float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0, 3),
        "min": round(float(np.min(arr)), 3),
        "max": round(float(np.max(arr)), 3),
        "ci_low": round(ci_low, 3),
        "ci_high": round(ci_high, 3),
    }


def compare_paired_planners(
    proposed_losses: List[float],
    baseline_losses: List[float],
) -> Dict[str, Any]:
    """Paired difference statistical tests (Paired t-test, Wilcoxon, Cohen's d)."""
    assert len(proposed_losses) == len(baseline_losses), "Mismatched trial counts"
    n = len(proposed_losses)
    diffs = np.array(baseline_losses) - np.array(proposed_losses)
    
    mean_diff = float(np.mean(diffs))
    wins = int(np.sum(diffs > 0.01))
    ties = int(np.sum(np.abs(diffs) <= 0.01))
    losses = int(np.sum(diffs < -0.01))
    
    # Paired t-test
    if np.all(diffs == 0):
        t_stat, p_val = 0.0, 1.0
    else:
        t_stat, p_val = stats.ttest_rel(baseline_losses, proposed_losses)

    # Cohen's d
    s_diff = float(np.std(diffs, ddof=1)) if len(diffs) > 1 else 1.0
    cohen_d = float(mean_diff / s_diff) if s_diff > 1e-6 else 0.0

    b_mean = float(np.mean(baseline_losses))
    p_mean = float(np.mean(proposed_losses))
    loss_reduction_pct = float(((b_mean - p_mean) / max(0.01, b_mean)) * 100.0)

    return {
        "n_trials": n,
        "baseline_mean_loss": round(b_mean, 2),
        "proposed_mean_loss": round(p_mean, 2),
        "mean_loss_reduction_pct": round(loss_reduction_pct, 2),
        "cohen_d": round(cohen_d, 3),
        "p_value": float(p_val),
        "win_rate_pct": round((wins / n) * 100.0, 2),
        "tie_rate_pct": round((ties / n) * 100.0, 2),
        "loss_rate_pct": round((losses / n) * 100.0, 2),
    }
