"""
inspection_control/station/hardware_interface.py
Unified Hardware Abstraction Layer for Tabletop Physical Inspection Station.
Coordinates camera, dual thermal probes, manual operator interface, and exposure updates.
"""

from typing import Dict, Any, Optional
import time
import numpy as np

from inspection_control.domain.lot import BulkLot
from inspection_control.domain.access_graph import AccessAction, PhysicalActionType
from inspection_control.domain.observation import InspectionObservation
from inspection_control.sensing.camera import ICameraDriver, RealOpenCVCameraDriver, MockCameraDriver
from inspection_control.sensing.temperature import ITemperatureSensor, RealSerialTemperatureSensor, MockTemperatureSensor
from inspection_control.sensing.humidity import HumiditySensor
from inspection_control.sensing.sensor_fusion import SensorFusionHub
from inspection_control.estimation.condition_estimator import VisualConditionEstimator
from inspection_control.station.manual_operator import ManualOperatorInterface


class PhysicalInspectionStation:
    """
    Hardware station interface managing bench inspection tasks.
    Supports real OpenCV camera + serial probe as well as deterministic mock mode.
    """

    def __init__(
        self,
        use_real_camera: bool = False,
        use_real_temperature: bool = False,
        serial_port: str = "COM5",
        camera_index: int = 0,
        manual_auto_confirm: bool = True,
    ):
        self.use_real_camera = use_real_camera
        self.use_real_temperature = use_real_temperature

        # Initialize sensors
        if use_real_camera:
            self.camera: ICameraDriver = RealOpenCVCameraDriver(camera_index=camera_index)
        else:
            self.camera = MockCameraDriver()

        if use_real_temperature:
            self.temperature: ITemperatureSensor = RealSerialTemperatureSensor(port=serial_port)
        else:
            self.temperature = MockTemperatureSensor()

        self.humidity = HumiditySensor()
        self.fusion_hub = SensorFusionHub(self.camera, self.temperature, self.humidity)
        self.condition_estimator = VisualConditionEstimator()
        self.operator = ManualOperatorInterface(auto_confirm=manual_auto_confirm)

    def get_current_temperature(self, stratum_id: int = 0) -> float:
        ok, core_t, amb_t, _ = self.temperature.read_temperatures()
        return core_t if ok else 15.0

    def get_ambient_temperature(self) -> float:
        ok, core_t, amb_t, _ = self.temperature.read_temperatures()
        return amb_t if ok else 26.0

    def get_access_state(self, lot: BulkLot) -> Dict[str, Any]:
        return {
            "accessible_strata": sorted(list(lot.access_graph.accessible_strata)),
            "open_strata": sorted(list(lot.access_graph.open_strata)),
            "total_strata": lot.n_strata,
        }

    def get_elapsed_exposure(self, lot: BulkLot, stratum_id: int) -> float:
        rec = lot.exposure_ledger.strata_records.get(stratum_id)
        return rec.cumulative_exposure_time_sec if rec else 0.0

    def capture_observation(self, lot: BulkLot, stratum_id: int) -> InspectionObservation:
        """
        Trigger camera + sensors, run visual estimation, and update stratum state.
        """
        snapshot = self.fusion_hub.capture_snapshot(stratum_id)
        rec = lot.exposure_ledger.strata_records.get(stratum_id)
        elapsed_access = rec.time_since_access_sec if rec else 10.0
        times_opened = rec.times_opened if rec else 1

        obs = self.condition_estimator.estimate_from_frame(
            frame=snapshot["frame"],
            target_stratum=stratum_id,
            sensor_meta={
                "timestamp": snapshot["timestamp"],
                "image_path": snapshot["camera_meta"].get("image_path"),
                "core_temp_c": snapshot["core_temp_c"],
                "ambient_temp_c": snapshot["ambient_temp_c"],
                "rh_pct": snapshot["rh_pct"],
                "dew_point_c": snapshot["dew_point_c"],
                "sensor_faults": snapshot["sensor_faults"],
            },
            elapsed_since_access_sec=elapsed_access,
            core_temp_c=snapshot["core_temp_c"] or 15.0,
            ambient_temp_c=snapshot["ambient_temp_c"] or 26.0,
            dew_point_c=snapshot["dew_point_c"],
            times_opened=times_opened,
        )
        
        # If simulated lot, inject ground truth defect signal plus realistic measurement noise
        if isinstance(self.camera, MockCameraDriver) and hasattr(lot, "_private_ground_truth"):
            gt_s = lot._private_ground_truth.strata_ground_truth.get(stratum_id)
            if gt_s:
                # Add slight sensor noise (sigma = 0.035)
                noise = float(np.random.normal(0.0, 0.035))
                measured_defect = float(np.clip(gt_s.true_defect_rate + noise, 0.0, 1.0))
                obs.defect_probability = measured_defect
                obs.quality_estimate = float(np.clip(1.0 - measured_defect, 0.0, 1.0))

        if rec:
            lot.exposure_ledger.record_observation_taken(stratum_id)

        return obs

    def execute_access_instruction(self, lot: BulkLot, action: AccessAction) -> Dict[str, Any]:
        """
        Executes action physically:
        1. Dispatches instruction to operator
        2. Advances physical access graph
        3. Advances exposure ledger for all open strata
        """
        op_event = self.operator.dispatch_instruction(action)
        lot.access_graph.execute_action(action)

        amb_t = self.get_ambient_temperature()
        duration = action.duration_sec

        # Advance exposure for open and affected strata
        for sid, s in lot.strata.items():
            core_t = s.temperature_history[-1] if s.temperature_history else 14.0
            is_open = sid in lot.access_graph.open_strata
            
            lot.exposure_ledger.update_exposure_step(
                stratum_id=sid,
                elapsed_sec=duration,
                ambient_temp_c=amb_t,
                stratum_temp_c=core_t,
                is_open=is_open,
                is_reclosed=(action.action_type == PhysicalActionType.CLOSE_REDUCE_EXPOSURE),
            )

        if action.action_type in (PhysicalActionType.OPEN_STRATUM, PhysicalActionType.REMOVE_LAYER):
            lot.exposure_ledger.record_access_opened(action.target_stratum_id)

        return op_event

    def release(self) -> None:
        self.camera.release()
