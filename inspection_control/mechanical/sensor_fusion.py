"""
inspection_control/mechanical/sensor_fusion.py
Mechanical Sensor Fusion Engine.

Synthesizes noisy, multi-modal sensor inputs (load cells, displacement encoders,
tactile pressure mats, and optical inspections) into a robust, filtered belief
state with explicit uncertainty bounds.
"""

from typing import Dict, Any, List, Optional
import numpy as np

from inspection_control.mechanical.sensor_interface import (
    MechanicalSensorInterface,
    SensorReading,
)
from inspection_control.mechanical.mechanical_state import MechanicalStratumState


class MechanicalSensorFusion:
    """
    Kalman-style state filter combining multi-modal physical measurements
    with physics-based prediction priors.
    """

    def __init__(
        self,
        n_strata: int = 5,
        process_noise_sigma: float = 1.0,
        sensor_interface: Optional[MechanicalSensorInterface] = None,
    ):
        self.n_strata = n_strata
        self.process_noise_sigma = process_noise_sigma
        self.sensor_interface = sensor_interface

        # Filter state vectors: estimated mean and covariance
        self.est_forces = np.zeros(n_strata)
        self.est_displacements = np.zeros(n_strata)
        self.est_compressions = np.zeros(n_strata)
        self.cov_forces = np.eye(n_strata) * 10.0
        self.cov_displacements = np.eye(n_strata) * 0.5
        self.last_update_sec = 0.0

    def initialize(self, strata: Dict[int, MechanicalStratumState]) -> None:
        for i in range(self.n_strata):
            if i in strata and strata[i].is_present:
                self.est_forces[i] = strata[i].force_n
                self.est_compressions[i] = strata[i].compression_cm
                self.est_displacements[i] = strata[i].displacement_cm
            else:
                self.est_forces[i] = 0.0
                self.est_compressions[i] = 0.0
                self.est_displacements[i] = 0.0
        self.cov_forces = np.eye(self.n_strata) * 5.0
        self.cov_displacements = np.eye(self.n_strata) * 0.1

    def fuse_step(
        self,
        timestamp_sec: float,
        action_name: str,
        target_stratum_id: int,
        nominal_stiffness: List[float],
        camera_obs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes prediction step (physics dynamics) + measurement update step.
        Handles sensor dropout and anomalous readouts gracefully.
        """
        dt = max(0.01, timestamp_sec - self.last_update_sec)
        self.last_update_sec = timestamp_sec

        # 1. Prediction step: process noise inflates covariance
        self.cov_forces += np.eye(self.n_strata) * (self.process_noise_sigma * dt)
        self.cov_displacements += np.eye(self.n_strata) * (0.01 * dt)

        # 2. Measurement acquisition from sensor interface
        load_reading: Optional[SensorReading] = None
        disp_reading: Optional[SensorReading] = None

        if self.sensor_interface:
            load_reading = self.sensor_interface.read_forces(timestamp_sec)
            disp_reading = self.sensor_interface.read_displacement(timestamp_sec)

        # 3. Measurement Update: Load Cells
        if load_reading and load_reading.status == "OK":
            z_f = load_reading.values
            r_f = max(0.01, load_reading.uncertainty_sigma ** 2)
            for i in range(self.n_strata):
                # Kalman gain for scalar components
                k_gain = self.cov_forces[i, i] / (self.cov_forces[i, i] + r_f)
                self.est_forces[i] += k_gain * (z_f[i] - self.est_forces[i])
                self.cov_forces[i, i] *= (1.0 - k_gain)
        else:
            # Dropout occurred - rely purely on model prediction
            pass

        # 4. Measurement Update: Displacement
        if disp_reading and disp_reading.status == "OK":
            z_d = disp_reading.values
            r_d = max(0.001, disp_reading.uncertainty_sigma ** 2)
            for i in range(self.n_strata):
                k_gain = self.cov_displacements[i, i] / (self.cov_displacements[i, i] + r_d)
                self.est_displacements[i] += k_gain * (z_d[i] - self.est_displacements[i])
                self.cov_displacements[i, i] *= (1.0 - k_gain)

        # 5. Consistency check: update estimated compression from forces and stiffness
        for i in range(self.n_strata):
            stiff = nominal_stiffness[i] if i < len(nominal_stiffness) else 150.0
            self.est_compressions[i] = self.est_forces[i] / max(1.0, stiff)

        # Confidence calculation
        diag_var = np.diag(self.cov_forces)
        avg_std = float(np.mean(np.sqrt(np.clip(diag_var, 0.001, 100.0))))
        confidence = float(np.clip(1.0 / (1.0 + 0.1 * avg_std), 0.1, 0.99))

        return {
            "timestamp_sec": timestamp_sec,
            "estimated_forces_n": self.est_forces.copy(),
            "estimated_compressions_cm": self.est_compressions.copy(),
            "estimated_displacements_cm": self.est_displacements.copy(),
            "force_uncertainty_sigma": np.sqrt(np.clip(diag_var, 0.001, 100.0)),
            "overall_confidence": confidence,
            "sensor_status": load_reading.status if load_reading else "NO_SENSOR",
        }
