"""Multi-Observation Fusion Engine.

Harmonizes sequential visual observations across multiple views.
Evaluates inter-observation agreement/disagreement to dynamically reduce
or retain visual quality uncertainty.
"""

from typing import List, Dict, Any, Optional
from core.schemas import QualityEstimate, Observation
from uncertainty.estimator import UncertaintyEstimator


class ObservationFusionEngine:
    """
    Fuses multiple quality estimates derived from successive views of a produce item.
    
    Fusion Principles:
    ------------------
    1. Complementary Surface Inspection: An item with pristine top but rot on reverse side
       must NOT hide the defect through naive averaging. The fused score heavily penalizes
       local defects:
           Q_fused = 0.5 * min(Q_i) + 0.5 * mean(Q_i)
    2. Agreement / Disagreement Uncertainty Scaling:
       - If views agree closely (|Q_1 - Q_2| < 0.10): visual coverage penalty drops and
         uncertainty decreases significantly (e.g., -35%).
       - If views disagree sharply (|Q_1 - Q_2| > 0.35): visual ambiguity remains high,
         preventing premature certainty.
    """

    def __init__(self, uncertainty_estimator: Optional[UncertaintyEstimator] = None):
        self.uncertainty_estimator = uncertainty_estimator or UncertaintyEstimator()

    def fuse_estimates(
        self,
        estimates: List[QualityEstimate],
        observations: Optional[List[Observation]] = None
    ) -> QualityEstimate:
        if not estimates:
            raise ValueError("Cannot fuse empty list of quality estimates.")

        if len(estimates) == 1:
            return estimates[0]

        obs_count = len(estimates)
        commodity = estimates[-1].commodity

        # Extract quality scores and confidences
        scores = [e.quality_score for e in estimates]
        confidences = [e.confidence for e in estimates]
        uncertainties = [e.uncertainty for e in estimates]

        min_score = min(scores)
        mean_score = sum(scores) / float(obs_count)

        # Conservative quality score honoring localized decay/blemishes
        fused_quality = round((0.45 * min_score) + (0.55 * mean_score), 3)
        fused_freshness = round(fused_quality, 3)

        # Inter-observation divergence
        max_diff = max(scores) - min(scores)

        # Fused Confidence increases with multiple observations
        # Base confidence weighted average
        weighted_conf_sum = sum(c * s for c, s in zip(confidences, scores))
        total_conf = sum(confidences)
        avg_conf = (weighted_conf_sum / total_conf) if total_conf > 0 else 0.80
        fused_confidence = round(min(0.98, avg_conf + (0.08 * (obs_count - 1)) - (0.10 * max_diff)), 3)

        # Uncertainty reduction calculation
        # Agreement discount: if views agree, uncertainty shrinks substantially
        avg_prior_unc = sum(uncertainties) / float(obs_count)
        
        if max_diff <= 0.12:
            # Strong agreement: sharp reduction in uncertainty
            agreement_factor = 0.65  # 35% reduction
            consensus_note = "Multi-view consistency confirmed; coverage uncertainty reduced."
        elif max_diff <= 0.28:
            # Moderate agreement
            agreement_factor = 0.82  # 18% reduction
            consensus_note = "Moderate multi-view agreement observed."
        else:
            # Sharp disagreement (e.g. one side bruised)
            agreement_factor = 1.05  # Slight penalty or retained uncertainty
            consensus_note = "Significant visual variance detected across different sides of the produce."

        fused_uncertainty = round(max(0.06, min(0.90, avg_prior_unc * agreement_factor)), 3)

        # Qualitative Class
        if fused_quality >= 0.78:
            quality_class = "Fresh"
            quality_adj = 0.0
            adj_label = "Confirmed fresh across views"
        elif fused_quality >= 0.48:
            quality_class = "Slightly Aged"
            quality_adj = -2.0
            adj_label = "Multi-view inspection indicates moderate softness"
        else:
            quality_class = "Overripe"
            quality_adj = -5.0
            adj_label = "Localized decay detected"

        all_used_ids: List[str] = []
        for e in estimates:
            all_used_ids.extend(e.observations_used)

        return QualityEstimate(
            commodity=commodity,
            quality_score=fused_quality,
            freshness_score=fused_freshness,
            quality_class=quality_class,
            confidence=fused_confidence,
            uncertainty=fused_uncertainty,
            observations_used=list(set(all_used_ids)),
            freshness_percent=int(fused_freshness * 100),
            freshness_note=f"Fused from {obs_count} views. {consensus_note}",
            quality_adjustment_suggested=quality_adj,
            quality_adjustment_label=adj_label,
            details={
                "fusion_method": "conservative_defect_weighted_fusion",
                "observation_count": obs_count,
                "inter_view_max_diff": round(max_diff, 3),
                "agreement_factor": agreement_factor,
                "prior_uncertainties": uncertainties,
                "consensus_note": consensus_note,
            }
        )
