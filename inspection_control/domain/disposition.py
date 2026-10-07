"""
inspection_control/domain/disposition.py
Terminal disposition decisions and downstream loss matrix.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any


class DispositionDecision(str, Enum):
    ACCEPT = "ACCEPT"           # Premium market grade
    MARKDOWN = "MARKDOWN"       # Discounted commercial grade
    REJECT = "REJECT"           # Full scrap / dump
    REROUTE = "REROUTE"         # Processing / juicing / starch conversion
    SPLIT_LOT = "SPLIT_LOT"     # Physical sorting / separation of upper vs lower strata
    ESCALATE = "ESCALATE"       # Human expert laboratory review


@dataclass
class DispositionLossConfig:
    """
    Economic loss parameters (in INR).
    Ground truth lot defect rate theta in [0, 1].
    Accept threshold theta_A = 0.08
    Markdown threshold theta_M = 0.20
    Reroute threshold theta_R = 0.35
    """
    threshold_accept: float = 0.08
    threshold_markdown: float = 0.20
    threshold_reroute: float = 0.35
    
    # Penalty costs
    cost_false_accept: float = 850.0      # Rotten batch shipped to client (reputation + refund)
    cost_false_reject: float = 400.0      # Dumping good produce
    cost_false_markdown: float = 180.0    # Selling good produce at steep discount
    cost_under_markdown: float = 300.0    # Selling bad produce at mild discount (downstream spoilage)
    cost_split_labor: float = 120.0       # Manual sorting cost
    cost_escalation: float = 150.0        # Inspector overtime cost
    base_lot_value: float = 1200.0


class DispositionEvaluator:
    """Computes terminal disposition loss against ground truth defect rate."""

    def __init__(self, config: DispositionLossConfig = DispositionLossConfig()):
        self.config = config

    def evaluate_loss(
        self,
        decision: DispositionDecision,
        true_lot_defect_rate: float,
        inspection_cost_inr: float = 0.0,
        deterioration_loss_inr: float = 0.0,
    ) -> Dict[str, float]:
        cfg = self.config
        penalty = 0.0
        is_false_accept = False
        is_false_reject = False
        is_correct = False

        if decision == DispositionDecision.ACCEPT:
            if true_lot_defect_rate > cfg.threshold_accept:
                penalty = cfg.cost_false_accept * (true_lot_defect_rate / cfg.threshold_accept)
                is_false_accept = True
            else:
                penalty = 0.0
                is_correct = True

        elif decision == DispositionDecision.REJECT:
            if true_lot_defect_rate <= cfg.threshold_accept:
                penalty = cfg.cost_false_reject
                is_false_reject = True
            elif true_lot_defect_rate <= cfg.threshold_markdown:
                penalty = cfg.cost_false_reject * 0.5
            else:
                penalty = 0.0
                is_correct = True

        elif decision == DispositionDecision.MARKDOWN:
            if true_lot_defect_rate <= cfg.threshold_accept:
                penalty = cfg.cost_false_markdown
            elif true_lot_defect_rate > cfg.threshold_reroute:
                penalty = cfg.cost_under_markdown
                is_false_accept = True
            else:
                penalty = 0.0
                is_correct = True

        elif decision == DispositionDecision.REROUTE:
            if true_lot_defect_rate <= cfg.threshold_markdown:
                penalty = cfg.cost_false_markdown * 0.8
            else:
                penalty = 0.0
                is_correct = True

        elif decision == DispositionDecision.SPLIT_LOT:
            penalty = cfg.cost_split_labor
            is_correct = True

        elif decision == DispositionDecision.ESCALATE:
            penalty = cfg.cost_escalation
            is_correct = True

        total_loss = penalty + inspection_cost_inr + deterioration_loss_inr

        return {
            "disposition_penalty": penalty,
            "inspection_cost": inspection_cost_inr,
            "deterioration_loss": deterioration_loss_inr,
            "total_disposition_loss": total_loss,
            "is_false_accept": 1.0 if is_false_accept else 0.0,
            "is_false_reject": 1.0 if is_false_reject else 0.0,
            "is_correct": 1.0 if is_correct else 0.0,
        }
