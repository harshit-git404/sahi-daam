"""
simulation/experiments/ablation.py
Ablation Study Experiment (Section 12).

Tests B7 variants with individual mechanisms stripped away:
- Full B7 (Baseline Reference)
- Ablation A: No Exposure-Conditioned Bias
- Ablation B: No Option Value (Myopic Lookahead)
- Ablation C: No State-Change Modelling (Ignores Deterioration)
- Ablation E: No Contagion Modelling
- Ablation F: No Disposition Loss (Raw Variance Proxy)
- Ablation G: No Receding-Horizon (Open Loop)
- Ablation H: No Access Constraints (Artificially Direct)
- Ablation I: No Stopping Certificate (Forces Max Budget)
"""

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

from simulation.environment.lot import BulkPerishableLot, DefectPattern, LotConfig, PresentationBias
from simulation.planners.b7_proposed import AblationConfig, B7ProposedPlanner
from simulation.experiments.runner import SimulationTrialRunner, TrialMetrics
from simulation.metrics.statistics import BenchmarkStatisticsCalculator, ComparisonStats


def run_ablation_study(
    n_trials: int = 300,
    base_seed: int = 50000,
) -> Tuple[pd.DataFrame, Dict[str, ComparisonStats]]:
    """
    Executes all ablation configurations against full B7.
    """
    lot_cfg = LotConfig(
        n_strata=5,
        units_per_stratum=100,
        defect_pattern=DefectPattern.HIDDEN_BOTTOM,
        presentation_bias=PresentationBias.ADVERSARIAL,
        base_defect_rate=0.25,
    )

    runner = SimulationTrialRunner(lot_config=lot_cfg, budget_limit=180.0)

    ablation_variants = {
        "Full_B7": AblationConfig(),
        "Abl_A_NoBiasModel": AblationConfig(disable_presentation_bias=True),
        "Abl_B_NoOptionValue": AblationConfig(disable_option_value=True),
        "Abl_C_NoStateChange": AblationConfig(disable_state_change=True),
        "Abl_E_NoContagion": AblationConfig(disable_contagion=True),
        "Abl_F_NoDispositionLoss": AblationConfig(disable_disposition_loss=True),
        "Abl_G_NoRecedingHorizon": AblationConfig(disable_receding_horizon=True),
        "Abl_H_NoAccessConstraints": AblationConfig(disable_access_constraints=True),
        "Abl_I_NoStoppingCert": AblationConfig(disable_stopping_certificate=True),
    }

    all_results: List[Dict] = []
    losses_by_variant: Dict[str, List[float]] = {k: [] for k in ablation_variants}
    fa_by_variant: Dict[str, List[int]] = {k: [] for k in ablation_variants}

    for i in range(n_trials):
        seed = base_seed + i
        rng = np.random.default_rng(seed)
        lot = BulkPerishableLot(config=lot_cfg, rng=rng)

        for name, abl_cfg in ablation_variants.items():
            planner = B7ProposedPlanner(ablation=abl_cfg)
            planner.name = name
            metrics = runner.run_single_trial(planner, lot, seed)
            all_results.append({**metrics.__dict__, "ablation_variant": name})
            losses_by_variant[name].append(metrics.total_loss)
            fa_by_variant[name].append(1 if metrics.is_false_accept else 0)

    df = pd.DataFrame(all_results)

    # Compare each ablation against Full_B7
    full_losses = np.array(losses_by_variant["Full_B7"])
    full_fa = np.array(fa_by_variant["Full_B7"])
    stats_dict: Dict[str, ComparisonStats] = {}

    for name in ablation_variants:
        if name == "Full_B7":
            continue
        v_losses = np.array(losses_by_variant[name])
        v_fa = np.array(fa_by_variant[name])
        # In this comparison: baseline is the ablated variant, proposed is Full_B7.
        # Positive diff means Full_B7 is better than the ablated variant.
        stat = BenchmarkStatisticsCalculator.calculate_paired_comparison(
            baseline_losses=v_losses,
            proposed_losses=full_losses,
            baseline_fa=v_fa,
            proposed_fa=full_fa,
            baseline_name=name,
            proposed_name="Full_B7",
        )
        stats_dict[name] = stat

    return df, stats_dict
