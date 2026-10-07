"""
simulation/experiments/stress_tests.py
Stress Tests Experiment (Section 13).

Evaluates 12 boundary regimes:
- Case 1: Visible surface representative
- Case 2: Visible surface moderately biased
- Case 3: Visible surface strongly biased
- Case 4: Defects concentrated deep in lot
- Case 5: Defects clustered spatially
- Case 6: Access is cheap
- Case 7: Access is expensive
- Case 8: High deterioration rate
- Case 9: False acceptance extremely expensive
- Case 10: False rejection extremely expensive
- Case 11: Myopic trap
- Case 12: Adversarial presentation
"""

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

from simulation.environment.access_graph import AccessGraphConfig
from simulation.environment.lot import BulkPerishableLot, DefectPattern, LotConfig, PresentationBias
from simulation.models.disposition import DispositionEvaluator, LossMatrixConfig
from simulation.baselines.b0_surface import B0SurfaceOnlyPlanner
from simulation.baselines.b2_depth_stratified import B2DepthStratifiedSamplingPlanner
from simulation.baselines.b4_myopic_voi import B4MyopicVOIPlanner
from simulation.baselines.b6_access_aware import B6AccessAwarePlanner
from simulation.planners.b7_proposed import B7ProposedPlanner
from simulation.experiments.runner import SimulationTrialRunner, TrialMetrics


def run_stress_tests(
    n_trials_per_case: int = 100,
    base_seed: int = 70000,
) -> pd.DataFrame:
    """
    Executes the 12 stress test scenarios.
    """
    cases = [
        ("Case_1_Representative", LotConfig(presentation_bias=PresentationBias.LOW, defect_pattern=DefectPattern.UNIFORM), None, None),
        ("Case_2_Mod_Biased", LotConfig(presentation_bias=PresentationBias.MEDIUM, defect_pattern=DefectPattern.DEPTH_CORRELATED), None, None),
        ("Case_3_Strong_Biased", LotConfig(presentation_bias=PresentationBias.HIGH, defect_pattern=DefectPattern.DEPTH_CORRELATED), None, None),
        ("Case_4_Deep_Defects", LotConfig(defect_pattern=DefectPattern.HIDDEN_BOTTOM, presentation_bias=PresentationBias.MEDIUM), None, None),
        ("Case_5_Clustered", LotConfig(defect_pattern=DefectPattern.CLUSTERED, presentation_bias=PresentationBias.MEDIUM), None, None),
        ("Case_6_Cheap_Access", LotConfig(), AccessGraphConfig(cost_remove_layer=5.0), None),
        ("Case_7_Expensive_Access", LotConfig(), AccessGraphConfig(cost_remove_layer=75.0), None),
        ("Case_8_High_Deterioration", LotConfig(deterioration_rate=0.015), None, None),
        ("Case_9_Severe_FA_Penalty", LotConfig(), None, LossMatrixConfig(cost_per_defective_accepted=150.0)),
        ("Case_10_Severe_FR_Penalty", LotConfig(), None, LossMatrixConfig(cost_false_reject_good_unit=65.0)),
        ("Case_11_Myopic_Trap", LotConfig(defect_pattern=DefectPattern.HIDDEN_BOTTOM, presentation_bias=PresentationBias.ADVERSARIAL), None, None),
        ("Case_12_Adversarial", LotConfig(defect_pattern=DefectPattern.ADVERSARIAL, presentation_bias=PresentationBias.ADVERSARIAL), None, None),
    ]

    planners = [
        B0SurfaceOnlyPlanner(),
        B2DepthStratifiedSamplingPlanner(),
        B4MyopicVOIPlanner(),
        B6AccessAwarePlanner(),
        B7ProposedPlanner(),
    ]

    all_results: List[Dict] = []
    case_counter = 0

    for case_name, lot_cfg, access_cfg, loss_cfg in cases:
        evaluator = DispositionEvaluator(config=loss_cfg) if loss_cfg else DispositionEvaluator()
        runner = SimulationTrialRunner(lot_config=lot_cfg, evaluator=evaluator, budget_limit=180.0)

        for i in range(n_trials_per_case):
            seed = base_seed + (case_counter * n_trials_per_case) + i
            rng = np.random.default_rng(seed)
            lot = BulkPerishableLot(config=lot_cfg, rng=rng)

            for p in planners:
                metrics = runner.run_single_trial(p, lot, seed)
                all_results.append({
                    **metrics.__dict__,
                    "stress_case": case_name,
                })

        case_counter += 1

    return pd.DataFrame(all_results)
