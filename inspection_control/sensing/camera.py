"""
inspection_control/sensing/camera.py
Camera driver supporting real OpenCV webcam capture and deterministic mock mode.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
import os
import time
import numpy as np
import cv2


class ICameraDriver(ABC):
    @abstractmethod
    def capture_frame(self, target_stratum: int) -> Tuple[bool, Optional[np.ndarray], Dict[str, Any]]:
        """Returns (success, frame_bgr_array, metadata)."""
        pass

    @abstractmethod
    def release(self) -> None:
        pass


class RealOpenCVCameraDriver(ICameraDriver):
    """Real physical camera driver accessing video index 0."""

    def __init__(self, camera_index: int = 0, save_dir: str = "evidence/captures"):
        self.camera_index = camera_index
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        self.cap: Optional[cv2.VideoCapture] = None
        self._init_camera()

    def _init_camera(self) -> bool:
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if self.cap.isOpened():
                # Set standard resolution
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                return True
        except Exception as e:
            print(f"[RealOpenCVCameraDriver] Init failed: {e}")
            self.cap = None
        return False

    def capture_frame(self, target_stratum: int) -> Tuple[bool, Optional[np.ndarray], Dict[str, Any]]:
        if self.cap is None or not self.cap.isOpened():
            if not self._init_camera():
                return False, None, {"error": "NO_IMAGE_AVAILABLE", "sensor": "RealOpenCVCamera"}

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return False, None, {"error": "FRAME_CAPTURE_FAILED", "sensor": "RealOpenCVCamera"}

        # Calculate visual metrics (mean brightness, blur/sharpness)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        # Save artifact image
        timestamp = int(time.time())
        filename = f"capture_s{target_stratum}_{timestamp}.jpg"
        filepath = os.path.join(self.save_dir, filename)
        cv2.imwrite(filepath, frame)

        meta = {
            "sensor": "RealOpenCVCamera",
            "device_index": self.camera_index,
            "brightness": brightness,
            "sharpness": sharpness,
            "image_path": filepath,
            "resolution": f"{frame.shape[1]}x{frame.shape[0]}",
            "timestamp": timestamp,
        }
        return True, frame, meta

    def release(self) -> None:
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None


class MockCameraDriver(ICameraDriver):
    """Deterministic simulated RGB camera for automated testing and counterfactuals."""

    def __init__(self, save_dir: str = "evidence/captures"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

    def capture_frame(self, target_stratum: int) -> Tuple[bool, Optional[np.ndarray], Dict[str, Any]]:
        # Generate synthetic 640x480 frame with potato/onion tones
        frame = np.full((480, 640, 3), (120, 160, 200), dtype=np.uint8)
        # Add synthetic produce contours
        cv2.circle(frame, (320, 240), 120, (80, 130, 180), -1)
        
        timestamp = int(time.time())
        filename = f"mock_capture_s{target_stratum}_{timestamp}.jpg"
        filepath = os.path.join(self.save_dir, filename)
        cv2.imwrite(filepath, frame)

        meta = {
            "sensor": "MockCameraDriver",
            "device_index": -1,
            "brightness": 128.0,
            "sharpness": 250.0,
            "image_path": filepath,
            "resolution": "640x480",
            "timestamp": timestamp,
        }
        return True, frame, meta

    def release(self) -> None:
        pass
