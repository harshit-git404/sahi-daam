"""
inspection_control/mechanical/sensor_interface.py
Abstract Mechanical Sensor Interface and Physical Driver Placeholder.

This abstraction guarantees that production controllers (FB6, FB7) interact
strictly through generic sensor methods, allowing future physical load cells,
strain gauges, and displacement encoders to be plugged in with ZERO changes
to the planning controller or evaluation framework.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import numpy as np


@dataclass
class SensorReading:
    """Standardized sensor measurement frame."""
    timestamp_sec: float
    sensor_id: str
    values: np.ndarray
    units: str
    status: str  # "OK", "DROPOUT", "SATURATED", "CALIBRATING"
    uncertainty_sigma: float
    is_simulated: bool = True


class MechanicalSensorInterface(ABC):
    """
    Hardware-agnostic interface for mechanical sensing.
    All controllers and estimators interact solely through this API.
    """

    @abstractmethod
    def read_forces(self, timestamp_sec: float) -> SensorReading:
        """Return normal force vector across strata [F_0, ..., F_n-1] in Newtons."""
        pass

    @abstractmethod
    def read_displacement(self, timestamp_sec: float) -> SensorReading:
        """Return top surface and inter-strata displacement vector in cm."""
        pass

    @abstractmethod
    def read_pressures(self, timestamp_sec: float) -> SensorReading:
        """Return contact pressure vector or grid across strata in kPa."""
        pass

    @abstractmethod
    def tare(self) -> None:
        """Zero the sensor reading with current tare load."""
        pass

    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """Return driver diagnostics, calibration date, and communication status."""
        pass


class PhysicalMechanicalSensorStub(MechanicalSensorInterface):
    """
    Physical hardware driver stub for laboratory instrumentation.
    Currently raises HardwareUnavailableError until physical hardware is procured.
    """

    def __init__(self, port: str = "COM5", baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.connected = False

    def read_forces(self, timestamp_sec: float) -> SensorReading:
        raise RuntimeError(
            f"Physical mechanical load cell array at {self.port} is NOT connected. "
            "Physical hardware is currently unavailable. Use SimulatedLoadCell."
        )

    def read_displacement(self, timestamp_sec: float) -> SensorReading:
        raise RuntimeError(
            f"Physical displacement encoder at {self.port} is NOT connected. "
            "Use SimulatedDisplacementSensor."
        )

    def read_pressures(self, timestamp_sec: float) -> SensorReading:
        raise RuntimeError(
            f"Physical tactile pressure mat at {self.port} is NOT connected. "
            "Use SimulatedPressureSensor."
        )

    def tare(self) -> None:
        pass

    def get_health_status(self) -> Dict[str, Any]:
        return {
            "driver": "PhysicalMechanicalSensorStub",
            "connected": False,
            "error": "HARDWARE_NOT_ATTACHED",
            "physical_evidence": False,
        }
