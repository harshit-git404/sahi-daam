"""
inspection_control/sensing/sensor_fusion.py
Synchronous multi-sensor acquisition and fault-tolerant fusion hub.
"""

from typing import Dict, Any, Optional
import time

from inspection_control.sensing.camera import ICameraDriver
from inspection_control.sensing.temperature import ITemperatureSensor
from inspection_control.sensing.humidity import HumiditySensor


class SensorFusionHub:
    """
    Coordinates hardware sensors, monitors failures, and outputs
    unified telemetry snapshots without fabricating data.
    """

    def __init__(
        self,
        camera: ICameraDriver,
        temperature: ITemperatureSensor,
        humidity: Optional[HumiditySensor] = None,
    ):
        self.camera = camera
        self.temperature = temperature
        self.humidity = humidity or HumiditySensor()

    def capture_snapshot(self, target_stratum: int) -> Dict[str, Any]:
        timestamp = time.time()
        
        # 1. Camera acquisition
        cam_ok, frame, cam_meta = self.camera.capture_frame(target_stratum)
        
        # 2. Thermal acquisition
        temp_ok, core_t, amb_t, temp_meta = self.temperature.read_temperatures()
        
        # 3. Humidity acquisition
        hum_ok, rh, dew_point, hum_meta = (False, 0.0, 0.0, {})
        if temp_ok:
            hum_ok, rh, dew_point, hum_meta = self.humidity.read_humidity(amb_t)

        snapshot = {
            "timestamp": timestamp,
            "target_stratum": target_stratum,
            "camera_ok": cam_ok,
            "frame": frame,
            "camera_meta": cam_meta,
            "temperature_ok": temp_ok,
            "core_temp_c": core_t if temp_ok else None,
            "ambient_temp_c": amb_t if temp_ok else None,
            "temp_meta": temp_meta,
            "humidity_ok": hum_ok,
            "rh_pct": rh if hum_ok else None,
            "dew_point_c": dew_point if hum_ok else None,
            "sensor_faults": [],
        }

        if not cam_ok:
            snapshot["sensor_faults"].append("NO_IMAGE_AVAILABLE")
        if not temp_ok:
            snapshot["sensor_faults"].append("TEMPERATURE_UNCERTAIN")

        return snapshot
