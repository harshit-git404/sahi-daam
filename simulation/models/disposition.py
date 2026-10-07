"""
simulation/models/disposition.py
Downstream Lot Disposition Decision and Economic Loss Matrix.

Evaluates terminal decisions (ACCEPT, MARKDOWN, REJECT, REROUTE, SPLIT_LOT)
against ground truth lot conditions, computing:
- False acceptance loss (inventory spoilage, customer claim)
- False rejection loss (procurement forfeiture)
- Suboptimal markdown loss
- Inspection labor and access costs
- Material consumption / destructive sampling loss
- Cumulative physical deterioration loss
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple
import numpy as np

from simulation.environment.lot import BulkPerishableLot


class DispositionDecision(str, Enum):
    ACCEPT = "accept"          # Accept for prime retail
    MARKDOWN = "markdown"      # Discount 35% for secondary market / quick sale
    REJECT = "reject"          # Reject lot back to supplier / dump
    REROUTE = "reroute"        # Divert to industrial processing (starch/feed) at 60% loss
    SPLIT_LOT = "split_lot"    # Disassemble lot, cull bad strata, keep good strata


@dataclass
class LossMatrixConfig:
    lot_nominal_value: float = 10000.0     # Base wholesale value of clean 500-unit lot (INR)
    cost_per_defective_accepted: float = 45.0  # Spoilage, packout rot, buyer penalty per bad unit
    cost_false_reject_good_unit: float = 18.0  # Lost margin / disposal of good unit
    markdown_price_discount: float = 0.35      # 35% price markdown
    reroute_price_discount: float = 0.60       # 60% recovery loss for industrial reroute
    culling_cost_per_stratum: float = 120.0    # Labor cost to split/sort a stratum
    unit_nominal_price: float = 20.0           # Nominal price per kg/unit
    tolerance_threshold_accept: float = 0.08   # Up to 8% defect allowed for ACCEPT
    tolerance_threshold_markdown: float = 0.22 # 8% - 22% defect allowed for MARKDOWN
    tolerance_threshold_reroute: float = 0.40  # 22% - 40% defect allowed for REROUTE
    # Above 40% defect must be REJECT


@dataclass
class DecisionLossResult:
    decision: DispositionDecision
    optimal_decision: DispositionDecision
    is_correct_disposition: bool
    disposition_loss: float
    inspection_monetary_cost: float
    destroyed_unit_loss: float
    deterioration_loss: float
    total_loss: float
    is_false_accept: bool
    is_false_reject: bool
    true_defect_rate: float
    estimated_defect_rate: float


class DispositionEvaluator:
    """
    Computes downstream economic loss for any given disposition decision.
    """

    def __init__(self, config: Optional[LossMatrixConfig] = None):
        self.config = config or LossMatrixConfig()

    def get_optimal_disposition(self, true_defect_rate: float) -> DispositionDecision:
        """Determines oracle Bayes-optimal decision given perfect ground truth defect rate."""
        cfg = self.config
        if true_defect_rate <= cfg.tolerance_threshold_accept:
            return DispositionDecision.ACCEPT
        elif true_defect_rate <= cfg.tolerance_threshold_markdown:
            return DispositionDecision.MARKDOWN
        elif true_defect_rate <= cfg.tolerance_threshold_reroute:
            return DispositionDecision.REROUTE
        else:
            return DispositionDecision.REJECT

    def evaluate_decision(
        self,
        decision: DispositionDecision,
        lot: BulkPerishableLot,
        inspection_cost: float,
        deterioration_loss: float,
        estimated_defect_rate: float,
    ) -> DecisionLossResult:
        """
        Evaluates chosen decision against true lot ground-truth condition.
        """
        cfg = self.config
        true_defect_rate = lot.ground_truth_defect_prevalence
        total_remaining = lot.total_remaining_units
        destroyed_units = lot.units_destroyed
        destroyed_unit_loss = destroyed_units * cfg.unit_nominal_price

        optimal_dec = self.get_optimal_disposition(true_defect_rate)
        is_correct = (decision == optimal_dec)

        true_defect_count = int(np.round(true_defect_rate * total_remaining))
        true_good_count = total_remaining - true_defect_count

        disposition_loss = 0.0
        is_fa = False
        is_fr = False

        if decision == DispositionDecision.ACCEPT:
            if true_defect_rate > cfg.tolerance_threshold_accept:
                # FALSE ACCEPT: Defective units slipped into retail inventory
                excess_defects = max(0, true_defect_count - int(cfg.tolerance_threshold_accept * total_remaining))
                disposition_loss = excess_defects * cfg.cost_per_defective_accepted
                is_fa = True
            else:
                disposition_loss = 0.0

        elif decision == DispositionDecision.MARKDOWN:
            if true_defect_rate <= cfg.tolerance_threshold_accept:
                # Unnecessary markdown on a clean lot: lost potential revenue
                disposition_loss = total_remaining * cfg.unit_nominal_price * cfg.markdown_price_discount
            elif true_defect_rate > cfg.tolerance_threshold_markdown:
                # Under-discounted heavily defective lot: still causes downstream spoilage
                excess_defects = max(0, true_defect_count - int(cfg.tolerance_threshold_markdown * total_remaining))
                disposition_loss = excess_defects * (cfg.cost_per_defective_accepted * 0.7)
                is_fa = True
            else:
                disposition_loss = 0.0

        elif decision == DispositionDecision.REJECT:
            if true_defect_rate < cfg.tolerance_threshold_reroute:
                # FALSE REJECT: Wrongly rejected a usable/clean lot
                disposition_loss = true_good_count * cfg.cost_false_reject_good_unit
                is_fr = True
            else:
                # Correct rejection: zero penalty (supplier absorbs cost or scrap value matches dump)
                disposition_loss = 0.0

        elif decision == DispositionDecision.REROUTE:
            if true_defect_rate <= cfg.tolerance_threshold_markdown:
                # Rerouted material that could have been sold at higher value
                disposition_loss = total_remaining * cfg.unit_nominal_price * (cfg.reroute_price_discount - cfg.markdown_price_discount)
            elif true_defect_rate > cfg.tolerance_threshold_reroute:
                # Still excessive defect for industrial
                disposition_loss = (true_defect_count - int(cfg.tolerance_threshold_reroute * total_remaining)) * 15.0
            else:
                disposition_loss = 0.0

        elif decision == DispositionDecision.SPLIT_LOT:
            # Physical sorting: cull strata where defect > 20%, keep clean strata
            sorting_cost = len(lot.strata) * cfg.culling_cost_per_stratum
            culled_units = 0
            remaining_bad = 0
            for s in lot.strata.values():
                if s.defect_prevalence > 0.20:
                    culled_units += s.remaining_units
                else:
                    remaining_bad += int(np.sum(s.defect_mask))
            disposition_loss = sorting_cost + (remaining_bad * cfg.cost_per_defective_accepted)

        total_loss = disposition_loss + inspection_cost + destroyed_unit_loss + deterioration_loss

        return DecisionLossResult(
            decision=decision,
            optimal_decision=optimal_dec,
            is_correct_disposition=is_correct,
            disposition_loss=disposition_loss,
            inspection_monetary_cost=inspection_cost,
            destroyed_unit_loss=destroyed_unit_loss,
            deterioration_loss=deterioration_loss,
            total_loss=total_loss,
            is_false_accept=is_fa,
            is_false_reject=is_fr,
            true_defect_rate=true_defect_rate,
            estimated_defect_rate=estimated_defect_rate,
        )

    def select_best_disposition_for_belief(self, expected_defect_rate: float) -> DispositionDecision:
        """Chooses best disposition according to expected posterior defect rate."""
        cfg = self.config
        if expected_defect_rate <= cfg.tolerance_threshold_accept:
            return DispositionDecision.ACCEPT
        elif expected_defect_rate <= cfg.tolerance_threshold_markdown:
            return DispositionDecision.MARKDOWN
        elif expected_defect_rate <= cfg.tolerance_threshold_reroute:
            return DispositionDecision.REROUTE
        else:
            return DispositionDecision.REJECT
