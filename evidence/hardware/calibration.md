# Sensor Calibration & Verification Protocol

## 1. Vision System Optical Verification
- **Target Verification Chart**: Standard 18% neutral gray card and GretagMacbeth color chart placed at $Z = 0\text{ cm}$.
- **Focus Verification**: Calibrated using slanted-edge modulation transfer function (MTF) to confirm $> 150.0$ Laplacian variance across the active inspection zone.
- **Color Calibration**: HSV color segmentation boundaries for potato/onion skin ($H \in [10, 35]$) and necrosis ($H \in [0, 180], V \le 55$) verified against known reference blemish samples.

## 2. Environmental Calibration (For Hardware Deployments)
- **Zero-Point Ice Bath Calibration**: Thermocouple/thermistor probes verified in 0.0°C ice-water slurry and 25.0°C stirred ambient water bath.
- **Ambient Cross-Verification**: Certified laboratory reference mercury thermometer cross-checked against digital probe outputs.
- **Calibration Records**: Archived in `calibration_data/calibrated_parameters.json`.
