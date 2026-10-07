# External Hardware Sensor Models

## Optical Sensor
- **Model:** Integrated / USB UVC Compliant Optical Camera
- **Device Index:** 0 (OpenCV UVC Backend)
- **Native Resolution:** 640 x 480 px BGR
- **Frame Rate:** 30 fps
- **Operational Status:** ACTIVE & OPERATIONAL
- **Measured Metrics:** Mean luminance, contrast, Laplacian sharpness score, surface defect segmentation.

## Thermal Probes
- **Model:** External Contact Thermocouple / DS18B20 Multi-Stratum Array
- **Intended Specification:** 3-5 probes inserted at Stratum S0 (surface), S1, S2, S3, S4 (bottom).
- **Physical Connection Status:** UNMEASURED / NOT CONNECTED
- **Hardware Bus:** USB-UART / Serial COM bus scanned: only Bluetooth RFCOMM ports (COM4, COM5, COM6) and virtual Communications Port (COM3) detected; no external physical temperature microcontroller/probe recognized.
- **Hardware Status:** UNMEASURED. In accordance with Section 6, synthetic thermal data is NOT substituted.
