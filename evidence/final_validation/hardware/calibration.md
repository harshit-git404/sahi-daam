# Sensor Calibration Protocol and Results

## Optical Camera Calibration
- Optical sensor index 0 was calibrated using image Laplacian sharpness operator:
  $$\text{Sharpness} = \text{Var}(\nabla^2 I)$$
- Focal verification threshold: $\text{Sharpness} \ge 80.0$ for non-degraded capture.
- Ambient exposure verification: Mean intensity $I_{\text{mean}} \in [80, 180]$ across 8-bit grayscale range.
- Measured physical values in test rig:
  - Frame dimensions: $640 \times 480$ px
  - Average sharpness: $96.2 - 188.4$
  - Status: PASSED CALIBRATION

## Thermal Probes Calibration
- Zero-offset and two-point ice-water / boiling calibration:
- Status: UNMEASURED (Probes not physically connected to workstation).
- Synthetic data substitution: EXPLICITLY REJECTED per Section 6.
