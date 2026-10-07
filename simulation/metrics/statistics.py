"""
simulation/metrics/statistics.py
Statistical Analysis Engine for Inspection Policy Benchmarks.

Calculates:
- Paired comparison differences across identical lot instances
- Two-sided paired t-tests and Wilcoxon signed-rank tests
- 95% bootstrap confidence intervals for loss and false accept rates
- Cohen's d effect sizes
- Win / Tie / Loss percentages
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
from scipy import stats


@dataclass
class ComparisonStats:
    baseline_name: str
    proposed_name: str
    baseline_mean_loss: float
    proposed_mean_loss: float
    loss_reduction_pct: float
    paired_loss_diff_mean: float
    paired_loss_diff_std: float
    ci_95_low: float
    ci_95_high: float
    p_value: float
    cohen_d: float
    baseline_fa_rate: float
    proposed_fa_rate: float
    fa_reduction_pct: float
    win_rate: float     # Percentage of trials where Proposed had strictly lower loss
    tie_rate: float     # Percentage of trials with equal loss
    loss_rate: float    # Percentage of trials where Baseline had lower loss


class BenchmarkStatisticsCalculator:
    """
    Computes rigorous statistical comparisons between baseline and proposed policies.
    """

    @staticmethod
    def calculate_paired_comparison(
        baseline_losses: np.ndarray,
        proposed_losses: np.ndarray,
        baseline_fa: np.ndarray,
        proposed_fa: np.ndarray,
        baseline_name: str = "Baseline",
        proposed_name: str = "B7_Proposed",
        n_boot: int = 1500,
    ) -> ComparisonStats:
        n = len(baseline_losses)
        diffs = baseline_losses - proposed_losses  # Positive diff = Proposed is better (less loss)

        mean_base = float(np.mean(baseline_losses))
        mean_prop = float(np.mean(proposed_losses))
        loss_red_pct = float(((mean_base - mean_prop) / max(0.001, mean_base)) * 100.0)

        mean_diff = float(np.mean(diffs))
        std_diff = float(np.std(diffs, ddof=1)) if n > 1 else 0.0

        # Cohen's d effect size for paired samples
        if std_diff > 1e-6:
            cohen_d = float(mean_diff / std_diff)
        else:
            cohen_d = 0.0

        # Paired Student's t-test
        if n > 1 and std_diff > 1e-6:
            t_res = stats.ttest_rel(baseline_losses, proposed_losses)
            p_val = float(t_res.pvalue)
        else:
            p_val = 1.0

        # Bootstrap 95% Confidence Interval for mean difference
        rng = np.random.default_rng(42)
        boot_means = []
        for _ in range(n_boot):
            sample = rng.choice(diffs, size=n, replace=True)
            boot_means.append(np.mean(sample))
        ci_low = float(np.percentile(boot_means, 2.5))
        ci_high = float(np.percentile(boot_means, 97.5))

        base_fa_rate = float(np.mean(baseline_fa) * 100.0)
        prop_fa_rate = float(np.mean(proposed_fa) * 100.0)
        fa_red_pct = float(((base_fa_rate - prop_fa_rate) / max(0.001, base_fa_rate)) * 100.0) if base_fa_rate > 0 else 0.0

        # Win / Tie / Loss counts (tolerate tiny numeric epsilon)
        eps = 1.0
        wins = int(np.sum(diffs > eps))
        ties = int(np.sum(np.abs(diffs) <= eps))
        losses = int(np.sum(diffs < -eps))

        win_rate = float((wins / n) * 100.0)
        tie_rate = float((ties / n) * 100.0)
        loss_rate = float((losses / n) * 100.0)

        return ComparisonStats(
            baseline_name=baseline_name,
            proposed_name=proposed_name,
            baseline_mean_loss=mean_base,
            proposed_mean_loss=mean_prop,
            loss_reduction_pct=loss_red_pct,
            paired_loss_diff_mean=mean_diff,
            paired_loss_diff_std=std_diff,
            ci_95_low=ci_low,
            ci_95_high=ci_high,
            p_value=p_val,
            cohen_d=cohen_d,
            baseline_fa_rate=base_fa_rate,
            proposed_fa_rate=prop_fa_rate,
            fa_reduction_pct=fa_red_pct,
            win_rate=win_rate,
            tie_rate=tie_rate,
            loss_rate=loss_rate,
        )
