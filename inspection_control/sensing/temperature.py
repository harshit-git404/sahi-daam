"""
inspection_control/sensing/temperature.py
Dual-probe temperature sensor drivers (produce core and ambient environment).
Supports hardware serial (Arduino/ESP32) and calibrated simulation mock.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional
import time


class ITemperatureSensor(ABC):
    @abstractmethod
    def read_temperatures(self) -> Tuple[bool, float, float, Dict[str, Any]]:
        """Returns (success, stratum_core_temp_c, ambient_temp_c, metadata)."""
        pass


class RealSerialTemperatureSensor(ITemperatureSensor):
    """
    Reads thermal probe data from a microcontroller (e.g. ESP32 / Arduino / DS18B20)
    via USB Serial COM port.
    """

    def __init__(self, port: str = "COM5", baudrate: int = 115200, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self._connect()

    def _connect(self) -> bool:
        try:
            import serial
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            return True
        except Exception as e:
            self.serial_conn = None
            return False

    def read_temperatures(self) -> Tuple[bool, float, float, Dict[str, Any]]:
        if not self.serial_conn:
            if not self._connect():
                return False, 0.0, 0.0, {"error": "TEMPERATURE_UNCERTAIN", "detail": "Serial probe disconnected"}

        try:
            line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
            # Expected format: "CORE:14.2,AMBIENT:26.5"
            parts = dict(item.split(":") for item in line.split(",") if ":" in item)
            core = float(parts.get("CORE", 15.0))
            ambient = float(parts.get("AMBIENT", 25.0))
            return True, core, ambient, {"sensor": "RealSerialTemperatureSensor", "port": self.port}
        except Exception as e:
            return False, 0.0, 0.0, {"error": "TEMPERATURE_READ_ERROR", "detail": str(e)}


class MockTemperatureSensor(ITemperatureSensor):
    """
    Calibrated thermal model: produce warms toward ambient via Newton's law of cooling.
    """

    def __init__(
        self,
        initial_produce_temp_c: float = 12.0,
        ambient_temp_c: float = 28.5,
        thermal_inertia_k: float = 0.0008, # Slow thermal transfer rate
    ):
        self.core_temp = initial_produce_temp_c
        self.ambient_temp = ambient_temp_c
        self.k = thermal_inertia_k
        self.last_update = time.time()

    def advance_time(self, elapsed_sec: float, is_exposed: bool = True) -> None:
        effective_k = self.k * 3.5 if is_exposed else self.k
        delta = (self.ambient_temp - self.core_temp) * (1.0 - (2.71828 ** (-effective_k * elapsed_sec)))
        self.core_temp += delta

    def read_temperatures(self) -> Tuple[bool, float, float, Dict[str, Any]]:
        now = time.time()
        elapsed = now - self.last_update
        self.advance_time(elapsed, is_exposed=True)
        self.last_update = now
        return True, round(self.core_temp, 2), round(self.ambient_temp, 2), {
            "sensor": "MockTemperatureSensor",
            "delta_t": round(self.ambient_temp - self.core_temp, 2),
            "timestamp": now,
        }
