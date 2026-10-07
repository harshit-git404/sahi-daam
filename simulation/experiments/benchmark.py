"""
simulation/experiments/benchmark.py
Full Baseline Matrix Experiment: B0 through B7 across heterogeneous lot regimes.
"""

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

from simulation.environment.lot import BulkPerishableLot, DefectPattern, LotConfig, PresentationBias
from simulation.baselines.b0_surface import B0SurfaceOnlyPlanner
from simulation.baselines.b1_fixed_random import B1FixedRandomSamplingPlanner
from simulation.baselines.b2_depth_stratified import B2DepthStratifiedSamplingPlanner
from simulation.baselines.b3_sahi_daam import B3SahiDaamHeuristicPlanner
from simulation.baselines.b4_myopic_voi import B4MyopicVOIPlanner
from simulation.baselines.b5_lookahead_voi import B5LookaheadVOIPlanner
from simulation.baselines.b6_access_aware import B6AccessAwarePlanner
from simulation.planners.b7_proposed import B7ProposedPlanner
from simulation.experiments.runner import SimulationTrialRunner, TrialMetrics
from simulation.metrics.statistics import BenchmarkStatisticsCalculator, ComparisonStats


def run_full_benchmark(
    n_trials_per_regime: int = 200,
    base_seed: int = 10000,
) -> Tuple[pd.DataFrame, Dict[str, ComparisonStats]]:
    """
    Executes all 8 planners across representative lot regimes.
    """
    planners = [
        B0SurfaceOnlyPlanner(),
        B1FixedRandomSamplingPlanner(),
        B2DepthStratifiedSamplingPlanner(),
        B3SahiDaamHeuristicPlanner(),
        B4MyopicVOIPlanner(),
        B5LookaheadVOIPlanner(),
        B6AccessAwarePlanner(),
        B7ProposedPlanner(),
    ]

    regimes = [
        (DefectPattern.UNIFORM, PresentationBias.LOW, 0.18),
        (DefectPattern.DEPTH_CORRELATED, PresentationBias.MEDIUM, 0.22),
        (DefectPattern.CLUSTERED, PresentationBias.MEDIUM, 0.20),
        (DefectPattern.HIDDEN_BOTTOM, PresentationBias.HIGH, 0.24),
        (DefectPattern.SURFACE_BIASED, PresentationBias.HIGH, 0.20),
        (DefectPattern.ADVERSARIAL, PresentationBias.ADVERSARIAL, 0.26),
    ]

    runner = SimulationTrialRunner(budget_limit=180.0)
    all_results: List[Dict] = []

    trial_counter = 0
    for pattern, bias, base_rate in regimes:
        lot_cfg = LotConfig(
            n_strata=5,
            units_per_stratum=100,
            defect_pattern=pattern,
            presentation_bias=bias,
            base_defect_rate=base_rate,
        )

        for _ in range(n_trials_per_regime):
            seed = base_seed + trial_counter
            trial_counter += 1
            rng = np.random.default_rng(seed)
            lot = BulkPerishableLot(config=lot_cfg, rng=rng)

            # Evaluate each planner on this exact counterfactual lot
            for planner in planners:
                metrics = runner.run_single_trial(planner, lot, seed)
                all_results.append({
                    **metrics.__dict__,
                    "regime_pattern": pattern.value,
                    "regime_bias": bias.value,
                })

    df = pd.DataFrame(all_results)

    # Compute comparative statistics of B7 vs all baselines B0..B6
    b7_df = df[df["planner_name"] == "B7_Proposed"].sort_values("trial_seed")
    b7_losses = b7_df["total_loss"].values
    b7_fa = (b7_df["is_false_accept"] == True).astype(int).values

    stats_dict: Dict[str, ComparisonStats] = {}
    for p in planners[:-1]:
        p_df = df[df["planner_name"] == p.name].sort_values("trial_seed")
        p_losses = p_df["total_loss"].values
        p_fa = (p_df["is_false_accept"] == True).astype(int).values

        stat = BenchmarkStatisticsCalculator.calculate_paired_comparison(
            baseline_losses=p_losses,
            proposed_losses=b7_losses,
            baseline_fa=p_fa,
            proposed_fa=b7_fa,
            baseline_name=p.name,
            proposed_name="B7_Proposed",
        )
        stats_dict[p.name] = stat

    return df, stats_dict
