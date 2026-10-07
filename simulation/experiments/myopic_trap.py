"""
simulation/experiments/myopic_trap.py
Dedicated Myopic Trap Experiment (Section 9).

Constructs lots where:
- Surface is mostly pristine (<3% defect prevalence)
- Deep strata have substantial hidden rot (35% to 60% defect prevalence)
- Deep strata CANNOT be observed without first performing REMOVE_LAYER
- REMOVE_LAYER yields ZERO immediate observation data
- Layer removal incurs non-zero monetary and labor costs.

Direct head-to-head evaluation:
B4 Myopic VOI vs B7 Proposed Planner.
"""

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

from simulation.environment.lot import BulkPerishableLot, DefectPattern, LotConfig, PresentationBias
from simulation.baselines.b4_myopic_voi import B4MyopicVOIPlanner
from simulation.planners.b7_proposed import B7ProposedPlanner
from simulation.experiments.runner import SimulationTrialRunner, TrialMetrics
from simulation.metrics.statistics import BenchmarkStatisticsCalculator, ComparisonStats


def run_myopic_trap_experiment(
    n_trials: int = 500,
    base_seed: int = 42000,
) -> Tuple[pd.DataFrame, ComparisonStats]:
    """
    Executes the critical Myopic Trap kill-test experiment.
    """
    lot_cfg = LotConfig(
        n_strata=5,
        units_per_stratum=100,
        defect_pattern=DefectPattern.HIDDEN_BOTTOM,
        presentation_bias=PresentationBias.ADVERSARIAL,
        base_defect_rate=0.25,
    )

    runner = SimulationTrialRunner(lot_config=lot_cfg, budget_limit=180.0)
    p_b4 = B4MyopicVOIPlanner()
    p_b7 = B7ProposedPlanner()

    results: List[Dict] = []
    b4_losses = []
    b7_losses = []
    b4_fa = []
    b7_fa = []

    for i in range(n_trials):
        seed = base_seed + i
        rng = np.random.default_rng(seed)
        lot = BulkPerishableLot(config=lot_cfg, rng=rng)

        # Counterfactual evaluation on the exact same lot
        res_b4 = runner.run_single_trial(p_b4, lot, seed)
        res_b7 = runner.run_single_trial(p_b7, lot, seed)

        results.append({**res_b4.__dict__, "experiment": "myopic_trap"})
        results.append({**res_b7.__dict__, "experiment": "myopic_trap"})

        b4_losses.append(res_b4.total_loss)
        b7_losses.append(res_b7.total_loss)
        b4_fa.append(1 if res_b4.is_false_accept else 0)
        b7_fa.append(1 if res_b7.is_false_accept else 0)

    df = pd.DataFrame(results)

    stats = BenchmarkStatisticsCalculator.calculate_paired_comparison(
        baseline_losses=np.array(b4_losses),
        proposed_losses=np.array(b7_losses),
        baseline_fa=np.array(b4_fa),
        proposed_fa=np.array(b7_fa),
        baseline_name="B4_Myopic_VOI",
        proposed_name="B7_Proposed",
    )

    return df, stats
