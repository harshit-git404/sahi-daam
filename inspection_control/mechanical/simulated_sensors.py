"""
inspection_control/mechanical/simulated_sensors.py
High-Fidelity Simulated Mechanical Sensors.

LABEL: SIMULATED HARDWARE
NOTE: All values and models in this file are engineering simulation assumptions.
No actual physical sensor hardware is claimed or represented.
"""

from typing import Dict, Any, Optional
import numpy as np
from inspection_control.mechanical.sensor_interface import (
    MechanicalSensorInterface,
    SensorReading,
)


class SimulatedMechanicalSensors(MechanicalSensorInterface):
    """
    Simulated Hardware Suite integrating Load Cells, Displacement Encoders,
    and Tactile Pressure Mats.

    Explicit Label: SIMULATED HARDWARE
    All parameters are configurable engineering simulation assumptions.
    """

    def __init__(
        self,
        n_strata: int = 5,
        load_range_n: float = 1000.0,       # 0 - 100 kg equivalent (approx 1000 N)
        load_resolution_n: float = 0.1,     # ~0.01 kg resolution
        load_noise_std_n: float = 0.5,      # Gaussian noise std
        load_bias_n: float = 0.0,           # Calibration offset/bias
        load_drift_rate_per_sec: float = 0.001, # Sensor thermal drift
        dropout_probability: float = 0.0,   # Sensor frame drop probability
        quantization: bool = True,
        calibration_error_pct: float = 0.0, # Gain calibration error (+/- %)
        latency_sec: float = 0.01,          # Sensor readout latency
        seed: Optional[int] = 42,
    ):
        self.n_strata = n_strata
        self.load_range_n = load_range_n
        self.load_resolution_n = load_resolution_n
        self.load_noise_std_n = load_noise_std_n
        self.load_bias_n = load_bias_n
        self.load_drift_rate_per_sec = load_drift_rate_per_sec
        self.dropout_probability = dropout_probability
        self.quantization = quantization
        self.calibration_scale = 1.0 + (calibration_error_pct / 100.0)
        self.latency_sec = latency_sec
        self._rng = np.random.default_rng(seed)

        # Internal true physical states provided by the physical simulator
        self._ground_truth_forces: np.ndarray = np.zeros(n_strata)
        self._ground_truth_displacement: np.ndarray = np.zeros(n_strata)
        self._ground_truth_pressures: np.ndarray = np.zeros(n_strata)
        self._tare_offset: np.ndarray = np.zeros(n_strata)
        self._start_time_sec: float = 0.0

    def update_ground_truth(
        self,
        forces: np.ndarray,
        displacements: np.ndarray,
        pressures: np.ndarray,
    ) -> None:
        """Physical simulation engine feeds ground truth into sensor transducer."""
        self._ground_truth_forces = np.array(forces, dtype=float)
        self._ground_truth_displacement = np.array(displacements, dtype=float)
        self._ground_truth_pressures = np.array(pressures, dtype=float)

    def read_forces(self, timestamp_sec: float) -> SensorReading:
        """Simulate reading normal load from bottom and inter-layer load cells."""
        if self._rng.uniform(0.0, 1.0) < self.dropout_probability:
            return SensorReading(
                timestamp_sec=timestamp_sec + self.latency_sec,
                sensor_id="sim_load_cell_array",
                values=np.zeros(self.n_strata),
                units="Newtons",
                status="DROPOUT",
                uncertainty_sigma=999.0,
                is_simulated=True,
            )

        # Apply calibration scale, bias, thermal drift
        drift = self.load_drift_rate_per_sec * max(0.0, timestamp_sec - self._start_time_sec)
        noise = self._rng.normal(0.0, self.load_noise_std_n, size=self.n_strata)
        raw_vals = (self._ground_truth_forces - self._tare_offset) * self.calibration_scale + self.load_bias_n + drift + noise

        # Saturation & Range clipping
        clipped = np.clip(raw_vals, 0.0, self.load_range_n)

        # Quantization
        if self.quantization and self.load_resolution_n > 0.0:
            clipped = np.round(clipped / self.load_resolution_n) * self.load_resolution_n

        return SensorReading(
            timestamp_sec=timestamp_sec + self.latency_sec,
            sensor_id="sim_load_cell_array",
            values=clipped,
            units="Newtons",
            status="OK",
            uncertainty_sigma=float(self.load_noise_std_n),
            is_simulated=True,
        )

    def read_displacement(self, timestamp_sec: float) -> SensorReading:
        """Simulate reading vertical column and inter-strata displacement in cm."""
        if self._rng.uniform(0.0, 1.0) < self.dropout_probability:
            return SensorReading(
                timestamp_sec=timestamp_sec + self.latency_sec,
                sensor_id="sim_lvdt_encoder",
                values=np.zeros(self.n_strata),
                units="cm",
                status="DROPOUT",
                uncertainty_sigma=999.0,
                is_simulated=True,
            )

        noise = self._rng.normal(0.0, 0.02, size=self.n_strata) # 0.2 mm noise
        measured = np.clip(self._ground_truth_displacement + noise, 0.0, 30.0)

        return SensorReading(
            timestamp_sec=timestamp_sec + self.latency_sec,
            sensor_id="sim_lvdt_encoder",
            values=measured,
            units="cm",
            status="OK",
            uncertainty_sigma=0.02,
            is_simulated=True,
        )

    def read_pressures(self, timestamp_sec: float) -> SensorReading:
        """Simulate reading tactile contact pressure in kPa."""
        if self._rng.uniform(0.0, 1.0) < self.dropout_probability:
            return SensorReading(
                timestamp_sec=timestamp_sec + self.latency_sec,
                sensor_id="sim_tactile_mat",
                values=np.zeros(self.n_strata),
                units="kPa",
                status="DROPOUT",
                uncertainty_sigma=999.0,
                is_simulated=True,
            )

        noise = self._rng.normal(0.0, 0.2, size=self.n_strata) # 0.2 kPa
        measured = np.clip(self._ground_truth_pressures + noise, 0.0, 50.0)

        return SensorReading(
            timestamp_sec=timestamp_sec + self.latency_sec,
            sensor_id="sim_tactile_mat",
            values=measured,
            units="kPa",
            status="OK",
            uncertainty_sigma=0.2,
            is_simulated=True,
        )

    def tare(self) -> None:
        """Set zero-offset."""
        self._tare_offset = self._ground_truth_forces.copy()

    def get_health_status(self) -> Dict[str, Any]:
        return {
            "driver": "SimulatedMechanicalSensors",
            "is_simulated": True,
            "connected": True,
            "status": "OPERATIONAL_SIMULATION",
            "noise_std_n": self.load_noise_std_n,
            "dropout_rate": self.dropout_probability,
            "notice": "SIMULATED HARDWARE. Values are engineering simulation assumptions.",
        }
