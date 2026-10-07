# Hardware Sensor Models and Audit Status

## 1. Vision System (Physical Optical Sensor)
- **Model**: DirectShow / UVC-Compatible USB Integrated RGB Camera
- **Device Index**: `0` (OpenCV `cv2.VideoCapture(0)`)
- **Native Resolution**: 640 x 480 @ 30 FPS
- **Color Format**: BGR24 (8-bit per channel)
- **Optical Lens Type**: Fixed focal length, 65° FOV top-down perspective mount
- **Measurement Output**: Raw frame arrays, Laplacian edge-variance sharpness, HSV color distribution metrics
- **Physical Verification Status**: **CONFIRMED & OPERATIONAL** (Probed via OpenCV VideoCapture; physical captures acquired and archived).

## 2. Thermal Probes (Environmental & Core Produce Probes)
- **Designed Specification**: 
  - Produce Core: Maxim DS18B20 digital stainless-steel penetration thermistor probe (±0.5°C accuracy, -10°C to +85°C)
  - Ambient Environment: NTC 10K thermistor / digital ambient probe
- **Host Interface**: USB-to-UART Serial (CP2102 / CH340 / FTDI COM port)
- **Hardware Bus Probe Result**:
  - Scanned COM ports: `COM3`, `COM4`, `COM5`, `COM6`.
  - Device identification: Windows Bluetooth RFCOMM links (`BTHENUM`) and standard motherboard communications port.
  - No active USB-serial microcontroller device (ESP32/Arduino/DS18B20 adapter) was detected on the USB hub during scan.
- **Audit Decision (Criterion 2 Compliance)**:
  - Per Criterion 2: *"If a sensor is unavailable, explicitly mark that variable as unmeasured and remove it from the demonstrated mechanism."*
  - **Status: UNMEASURED PHYSICAL PROBE**. Synthetic thermal values are strictly disallowed during physical validation. The controller is evaluated with ambient exposure time as the primary physical observable.

## 3. Humidity Sensing
- **Designed Specification**: Sensirion SHT31 / DHT22 digital relative humidity sensor
- **Hardware Bus Probe Result**: No I2C/OneWire hardware bridge attached.
- **Audit Decision (Criterion 2 Compliance)**:
  - **Status: UNMEASURED**. Explicitly omitted from the empirical physical claim.

## 4. Optical Observation Degradation (Condensation / Vibration)
- **Audit Decision (Criterion 16 Compliance)**:
  - Per Criterion 16: *"Do NOT make condensation/dew/vibration observation degradation part of the patent core unless physical experiments actually demonstrate it."*
  - Because humidity probes and thermal refrigeration chambers are not physically interfaced on this workstation, condensation dew on lenses was not physically produced.
  - **Status: REMOVED FROM TRL-4 CORE CLAIM**; marked strictly as future industrial dock research.
