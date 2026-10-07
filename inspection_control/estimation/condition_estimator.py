"""
inspection_control/estimation/condition_estimator.py
Model-agnostic produce defect and condition estimator using OpenCV visual analysis.
"""

from typing import Dict, Any, Optional, Tuple
import cv2
import numpy as np

from inspection_control.domain.observation import InspectionObservation
from inspection_control.dynamics.observation_quality_model import ObservationQualityModel


class VisualConditionEstimator:
    """
    Analyzes visual produce frames (potatoes/onions) to extract
    defect probability, quality score, and confidence.
    """

    def __init__(self, quality_model: Optional[ObservationQualityModel] = None):
        self.quality_model = quality_model or ObservationQualityModel()

    def estimate_from_frame(
        self,
        frame: Optional[np.ndarray],
        target_stratum: int,
        sensor_meta: Dict[str, Any],
        elapsed_since_access_sec: float = 10.0,
        core_temp_c: float = 14.0,
        ambient_temp_c: float = 25.0,
        dew_point_c: Optional[float] = None,
        times_opened: int = 1,
    ) -> InspectionObservation:
        """
        Process visual frame and synthesize observation with exposure fidelity.
        """
        obs_id = f"obs_s{target_stratum}_{int(sensor_meta.get('timestamp', 0))}"

        # 1. Evaluate physical observation fidelity
        fid_metrics = self.quality_model.evaluate_observation_fidelity(
            elapsed_since_access_sec=elapsed_since_access_sec,
            core_temp_c=core_temp_c,
            ambient_temp_c=ambient_temp_c,
            dew_point_c=dew_point_c,
            times_opened=times_opened,
        )

        # 2. If frame is None or sensor faulted
        if frame is None:
            return InspectionObservation(
                observation_id=obs_id,
                visible_stratum=target_stratum,
                quality_estimate=0.5,
                defect_probability=0.2,
                confidence=0.1, # Extremely low confidence due to sensor failure
                units_observed=0,
                sensor_metadata={**sensor_meta, "fault": "NO_IMAGE_AVAILABLE"},
            )

        # 3. Computer Vision feature extraction (HSV color segmentation for rot/blemish)
        defect_ratio, visual_conf = self._analyze_produce_defects(frame)

        # Combine CV confidence with environmental fidelity
        combined_confidence = float(np.clip(visual_conf * fid_metrics.fidelity_score, 0.05, 0.98))
        quality_score = float(np.clip(1.0 - defect_ratio, 0.0, 1.0))

        return InspectionObservation(
            observation_id=obs_id,
            visible_stratum=target_stratum,
            quality_estimate=quality_score,
            defect_probability=defect_ratio,
            confidence=combined_confidence,
            units_observed=15,
            sensor_metadata={
                **sensor_meta,
                "fidelity_score": fid_metrics.fidelity_score,
                "condensation_loss": fid_metrics.condensation_attenuation,
                "settling_loss": fid_metrics.settling_penalty,
            },
            image_path=sensor_meta.get("image_path"),
        )

    def _analyze_produce_defects(self, frame: np.ndarray) -> Tuple[float, float]:
        """
        Segment produce vs background, detect dark necrotic rot patches or greening.
        """
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Produce mask: warm potato/onion hues (hue 10..35, sat 40..255)
            lower_produce = np.array([10, 40, 40], dtype=np.uint8)
            upper_produce = np.array([35, 255, 255], dtype=np.uint8)
            produce_mask = cv2.inRange(hsv, lower_produce, upper_produce)
            
            produce_pixels = int(np.count_nonzero(produce_mask))
            if produce_pixels < 500:
                # If lighting or framing is off, default to full image area
                produce_pixels = frame.shape[0] * frame.shape[1]
                produce_mask = np.ones((frame.shape[0], frame.shape[1]), dtype=np.uint8)

            # Defect mask 1: Dark soft rot / black browning (low value)
            lower_dark_rot = np.array([0, 0, 0], dtype=np.uint8)
            upper_dark_rot = np.array([180, 255, 55], dtype=np.uint8)
            dark_rot_mask = cv2.inRange(hsv, lower_dark_rot, upper_dark_rot)
            
            # Defect mask 2: Greenish solanine / fungal mold (hue 36..85)
            lower_green = np.array([36, 40, 40], dtype=np.uint8)
            upper_green = np.array([85, 255, 255], dtype=np.uint8)
            green_mask = cv2.inRange(hsv, lower_green, upper_green)

            total_defect_mask = cv2.bitwise_or(dark_rot_mask, green_mask)
            defect_in_produce = cv2.bitwise_and(total_defect_mask, produce_mask)
            
            defect_pixels = int(np.count_nonzero(defect_in_produce))
            defect_ratio = float(np.clip(defect_pixels / max(1, produce_pixels), 0.0, 1.0))

            # Visual confidence based on image contrast and sharpness
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            visual_conf = float(np.clip(sharpness / 300.0, 0.4, 0.95))

            return defect_ratio, visual_conf
        except Exception:
            return 0.15, 0.50
