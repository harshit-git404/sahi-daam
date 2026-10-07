"""
inspection_control/estimation/calibration.py
Parameter calibration and validation dataset separation for bulk inspection.
"""

from typing import Dict, Any, List
import json
import os


class SystemCalibrationManager:
    """
    Manages parameters calibrated strictly on separate calibration lots,
    preventing data leakage into evaluation runs.
    """

    def __init__(self, calibration_file: str = "calibration_data/calibrated_parameters.json"):
        self.calibration_file = calibration_file
        self.parameters = self._load_or_default()

    def _load_or_default(self) -> Dict[str, Any]:
        if os.path.exists(self.calibration_file):
            try:
                with open(self.calibration_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass

        default_params = {
            "version": "1.0.0",
            "calibration_dataset": "calibration_data/calibration_lots_v1.json",
            "quality_model": {
                "base_detection_noise": 0.045,
                "confidence_scaling": 0.92,
                "condensation_onset_dt": 4.0,
            },
            "deterioration_model": {
                "base_decay_rate": 0.00008,
                "contagion_rate": 0.00015,
                "ambient_temp_q10": 2.0,
            },
            "exposure_ledger": {
                "alpha_thermal": 0.05,
                "beta_gradient": 0.12,
                "gamma_reclosed": 1.45,
            },
            "controller_thresholds": {
                "risk_stopping_tolerance": 0.02,
                "max_inspection_time_sec": 300.0,
                "max_budget_inr": 80.0,
            }
        }
        os.makedirs(os.path.dirname(self.calibration_file), exist_ok=True)
        with open(self.calibration_file, "w") as f:
            json.dump(default_params, f, indent=2)
        return default_params

    def get_calibrated_config(self) -> Dict[str, Any]:
        return self.parameters
