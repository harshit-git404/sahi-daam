"""
inspection_control/sensing/humidity.py
Relative humidity and dew-point estimation for produce condensation tracking.
"""

from typing import Tuple, Dict, Any
import math
import time


class HumiditySensor:
    """Reads or estimates relative humidity and calculates dew point."""

    def __init__(self, default_rh_pct: float = 78.0):
        self.rh_pct = default_rh_pct

    def read_humidity(self, ambient_temp_c: float) -> Tuple[bool, float, float, Dict[str, Any]]:
        """
        Returns (success, rh_pct, dew_point_c, metadata).
        Uses Magnus-Tetens approximation for dew point calculation.
        """
        a = 17.27
        b = 237.7
        alpha = ((a * ambient_temp_c) / (b + ambient_temp_c)) + math.log(self.rh_pct / 100.0)
        dew_point = (b * alpha) / (a - alpha)

        return True, round(self.rh_pct, 1), round(dew_point, 1), {
            "sensor": "HumiditySensor",
            "rh_pct": self.rh_pct,
            "dew_point_c": round(dew_point, 1),
            "timestamp": time.time(),
        }
