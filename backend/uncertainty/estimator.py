"""Uncertainty estimation module for visual quality assessment.

Distinguishes epistemic/aleatoric uncertainty from raw model softmax confidence.
Transparent deterministic formulation combining multiple observable quality signals.
"""

from typing import Dict, Any, Optional
from core.schemas import Observation


class UncertaintyEstimator:
    """
    Computes an explainable, deterministic uncertainty score for quality estimates.
    
    Mathematical Formulation:
    -------------------------
    Uncertainty U_quality in [0.0, 1.0] is computed as a weighted composition:
    
        U_quality = w_conf * (1.0 - confidence)
                  + w_disagree * model_disagreement
                  + w_img * image_quality_penalty
                  + w_coverage * visual_coverage_penalty
                  + w_ambiguity * ambiguity_penalty
                  
    where:
      - (1.0 - confidence): Inverted primary model confidence.
      - model_disagreement: Divergence between independent models (e.g., VLM vs local CNN).
      - image_quality_penalty: Degradation due to blur, low resolution, or poor lighting.
      - visual_coverage_penalty: Penalty for single-view occlusion (e.g., only 1 surface observed).
      - ambiguity_penalty: Narrow margin between top-1 and top-2 classification candidates.
    """

    def __init__(
        self,
        weight_confidence: float = 0.35,
        weight_disagreement: float = 0.25,
        weight_image_quality: float = 0.15,
        weight_coverage: float = 0.15,
        weight_ambiguity: float = 0.10,
    ):
        self.w_conf = weight_confidence
        self.w_disagree = weight_disagreement
        self.w_img = weight_image_quality
        self.w_cov = weight_coverage
        self.w_amb = weight_ambiguity

    def estimate_quality_uncertainty(
        self,
        confidence: float,
        model_disagreement: float = 0.0,
        image_quality_score: float = 0.85,
        lighting_score: float = 0.80,
        observation_count: int = 1,
        prediction_margin: float = 0.50,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates quality uncertainty and returns composite metric plus sub-factor breakdown.
        """
        # 1. Inverted confidence component [0.0, 1.0]
        clamped_conf = max(0.0, min(1.0, confidence))
        conf_penalty = 1.0 - clamped_conf

        # 2. Model disagreement component [0.0, 1.0]
        disagreement_penalty = max(0.0, min(1.0, model_disagreement))

        # 3. Image quality & lighting degradation penalty [0.0, 1.0]
        # Lower image quality/lighting yields higher penalty
        avg_img_clarity = (max(0.0, min(1.0, image_quality_score)) + max(0.0, min(1.0, lighting_score))) / 2.0
        image_penalty = 1.0 - avg_img_clarity

        # 4. Visual coverage penalty [0.0, 1.0]
        # A single photo only sees ~35-50% of spherical produce surface.
        # Two complementary views cover ~80%, three views cover ~95%.
        if observation_count <= 1:
            coverage_penalty = 0.60
        elif observation_count == 2:
            coverage_penalty = 0.20
        else:
            coverage_penalty = 0.05

        # 5. Ambiguity / narrow prediction margin penalty [0.0, 1.0]
        # A large margin (e.g. 0.8) means unambiguous classification (penalty -> 0)
        # A small margin (e.g. 0.05) means high ambiguity (penalty -> 1.0)
        ambiguity_penalty = max(0.0, min(1.0, 1.0 - prediction_margin))

        # Weighted combination
        raw_uncertainty = (
            self.w_conf * conf_penalty
            + self.w_disagree * disagreement_penalty
            + self.w_img * image_penalty
            + self.w_cov * coverage_penalty
            + self.w_amb * ambiguity_penalty
        )

        final_uncertainty = round(max(0.0, min(1.0, raw_uncertainty)), 3)

        return {
            "uncertainty": final_uncertainty,
            "components": {
                "inverted_confidence_penalty": round(conf_penalty, 3),
                "model_disagreement_penalty": round(disagreement_penalty, 3),
                "image_quality_penalty": round(image_penalty, 3),
                "visual_coverage_penalty": round(coverage_penalty, 3),
                "ambiguity_penalty": round(ambiguity_penalty, 3),
            },
            "observation_count": observation_count,
            "formula": (
                "U = 0.35*(1-conf) + 0.25*disagree + 0.15*img_pen + 0.15*cov_pen + 0.10*amb_pen"
            ),
        }
