"""Model-agnostic quality estimation interfaces and implementations.

Supports Gemini VLM, local PyTorch/Keras ensembles, hybrid execution, and
deterministic simulated estimators for offline testing.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import base64

from core.schemas import Observation, QualityEstimate
from uncertainty.estimator import UncertaintyEstimator


class IQualityEstimator(ABC):
    """Abstract interface for produce quality and freshness estimation."""

    @abstractmethod
    def estimate_quality(
        self,
        observation: Observation,
        commodity_hint: Optional[str] = None
    ) -> QualityEstimate:
        """Estimate quality features and associated confidence from an observation."""
        pass


class HybridQualityEstimator(IQualityEstimator):
    """
    Standard production estimator: Attempts Gemini Multimodal VLM,
    cross-references with local models where available, and computes
    epistemic uncertainty via UncertaintyEstimator.
    """

    def __init__(self, uncertainty_estimator: Optional[UncertaintyEstimator] = None):
        self.uncertainty_estimator = uncertainty_estimator or UncertaintyEstimator()

    def estimate_quality(
        self,
        observation: Observation,
        commodity_hint: Optional[str] = None
    ) -> QualityEstimate:
        commodity = (commodity_hint or "tomato").lower()
        image_bytes: Optional[bytes] = None

        if observation.image_b64:
            try:
                b64_data = observation.image_b64
                if "," in b64_data:
                    b64_data = b64_data.split(",", 1)[1]
                image_bytes = base64.b64decode(b64_data)
            except Exception:
                image_bytes = None

        # Try Gemini VLM first
        gemini_result: Optional[Dict[str, Any]] = None
        if image_bytes:
            try:
                from ml.gemini_analysis import analyze_with_gemini
                gemini_result = analyze_with_gemini(image_bytes)
            except Exception:
                gemini_result = None

        # Try Local Ensemble
        local_result: Optional[Dict[str, Any]] = None
        if image_bytes:
            try:
                from ml.produce_classifier import identify_produce
                from ml.freshness_model import predict_freshness
                id_res = identify_produce(image_bytes)
                fresh_res = predict_freshness(image_bytes, id_res["produce_type"])
                local_result = {
                    "produce_type": id_res["produce_type"],
                    "confidence": id_res["produce_confidence"] / 100.0,
                    "freshness_percent": fresh_res["freshness_percent"],
                    "freshness_label": fresh_res["freshness_label"],
                    "quality_adjustment": fresh_res["quality_adjustment"],
                    "freshness_note": fresh_res["freshness_note"],
                }
            except Exception:
                local_result = None

        # Fusion & Disagreement Analysis
        if gemini_result and local_result:
            detected_commodity = gemini_result.get("produce_type", commodity).lower()
            gemini_freshness = float(gemini_result.get("freshness_percent", 80))
            local_freshness = float(local_result.get("freshness_percent", 80))
            freshness_diff = abs(gemini_freshness - local_freshness) / 100.0
            model_disagreement = min(1.0, freshness_diff * 1.5)

            # Combined confidence
            conf = min(0.98, (gemini_result.get("produce_confidence", 85) / 100.0) * 0.7 + (local_result.get("confidence", 0.8)) * 0.3)
            f_score = ((gemini_freshness * 0.7) + (local_freshness * 0.3)) / 100.0
            q_class = gemini_result.get("freshness_label", "Fresh")
            f_percent = round(f_score * 100)
            f_note = gemini_result.get("freshness_note", "")
            q_adj = gemini_result.get("quality_adjustment", 0.0)
            q_adj_label = gemini_result.get("quality_adjustment_label", "")
            method = "hybrid_vlm_and_local_cnn"

        elif gemini_result:
            detected_commodity = gemini_result.get("produce_type", commodity).lower()
            conf = gemini_result.get("produce_confidence", 85) / 100.0
            f_score = gemini_result.get("freshness_percent", 85) / 100.0
            q_class = gemini_result.get("freshness_label", "Fresh")
            f_percent = int(gemini_result.get("freshness_percent", 85))
            f_note = gemini_result.get("freshness_note", "Visual inspection completed.")
            q_adj = float(gemini_result.get("quality_adjustment", 0))
            q_adj_label = gemini_result.get("quality_adjustment_label", "Standard quality")
            model_disagreement = 0.05
            method = "gemini_vlm"

        elif local_result:
            detected_commodity = local_result.get("produce_type", commodity).lower()
            conf = local_result.get("confidence", 0.80)
            f_score = local_result.get("freshness_percent", 80) / 100.0
            q_class = local_result.get("freshness_label", "Fresh")
            f_percent = int(local_result.get("freshness_percent", 80))
            f_note = local_result.get("freshness_note", "Local vision inference completed.")
            q_adj = float(local_result.get("quality_adjustment", 0))
            q_adj_label = local_result.get("quality_adjustment_label", "")
            model_disagreement = 0.10
            method = "local_vit_cnn_ensemble"

        else:
            # Fallback when no image or ML failed
            detected_commodity = commodity
            conf = 0.60
            f_score = 0.75
            q_class = "Fresh"
            f_percent = 75
            f_note = f"Baseline catalog profile applied for {commodity}."
            q_adj = 0.0
            q_adj_label = "No visual deductions"
            model_disagreement = 0.20
            method = "catalog_baseline"

        # Compute uncertainty
        unc_calc = self.uncertainty_estimator.estimate_quality_uncertainty(
            confidence=conf,
            model_disagreement=model_disagreement,
            image_quality_score=observation.image_quality_score,
            lighting_score=observation.lighting_score,
            observation_count=observation.observation_index,
            prediction_margin=0.60 if conf > 0.8 else 0.30,
        )

        quality_score = f_score

        return QualityEstimate(
            commodity=detected_commodity,
            quality_score=round(quality_score, 3),
            freshness_score=round(f_score, 3),
            quality_class=q_class,
            confidence=round(conf, 3),
            uncertainty=unc_calc["uncertainty"],
            observations_used=[observation.observation_id],
            freshness_percent=f_percent,
            freshness_note=f_note,
            quality_adjustment_suggested=q_adj,
            quality_adjustment_label=q_adj_label,
            details={
                "method": method,
                "model_disagreement": model_disagreement,
                "uncertainty_breakdown": unc_calc["components"],
                "view": observation.view.value,
            }
        )


class SimulatedQualityEstimator(IQualityEstimator):
    """
    Deterministic test estimator for validation scenarios.
    Allows exact replication of low-confidence, high-disagreement,
    or pristine observation scenarios.
    """

    def __init__(
        self,
        fixed_commodity: str = "tomato",
        fixed_quality: float = 0.85,
        fixed_confidence: float = 0.90,
        fixed_disagreement: float = 0.05,
        uncertainty_estimator: Optional[UncertaintyEstimator] = None,
    ):
        self.fixed_commodity = fixed_commodity
        self.fixed_quality = fixed_quality
        self.fixed_confidence = fixed_confidence
        self.fixed_disagreement = fixed_disagreement
        self.uncertainty_estimator = uncertainty_estimator or UncertaintyEstimator()

    def estimate_quality(
        self,
        observation: Observation,
        commodity_hint: Optional[str] = None
    ) -> QualityEstimate:
        commodity = commodity_hint or self.fixed_commodity
        conf = self.fixed_confidence
        f_score = self.fixed_quality

        unc_calc = self.uncertainty_estimator.estimate_quality_uncertainty(
            confidence=conf,
            model_disagreement=self.fixed_disagreement,
            image_quality_score=observation.image_quality_score,
            lighting_score=observation.lighting_score,
            observation_count=observation.observation_index,
            prediction_margin=0.70 if conf > 0.8 else 0.25,
        )

        q_class = "Fresh" if f_score >= 0.70 else "Slightly Aged" if f_score >= 0.40 else "Overripe"

        return QualityEstimate(
            commodity=commodity,
            quality_score=round(f_score, 3),
            freshness_score=round(f_score, 3),
            quality_class=q_class,
            confidence=round(conf, 3),
            uncertainty=unc_calc["uncertainty"],
            observations_used=[observation.observation_id],
            freshness_percent=int(f_score * 100),
            freshness_note="Simulated test observation.",
            quality_adjustment_suggested=0.0 if f_score >= 0.70 else -2.0 if f_score >= 0.40 else -5.0,
            quality_adjustment_label="Test calibration",
            details={
                "method": "simulated_harness",
                "uncertainty_breakdown": unc_calc["components"],
                "view": observation.view.value,
            }
        )
