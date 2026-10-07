# Hardware Configuration & Physical Benchtop Setup

## 1. Tabletop Physical Inspection Rig
- **Bench Scale**: 5-stratum modular produce tray assembly ($S_0$ exposed surface, $S_1$ to $S_4$ unstackable sub-surface strata).
- **Physical Dimensions**: 40cm x 30cm x 25cm test enclosure mimicking standard post-harvest commercial field crates.
- **Produce Commodities**: Solanum tuberosum (Potato, primary), Allium cepa (Onion, secondary).

## 2. Sensor Instrumentation
- **Primary RGB Vision**: USB HD Web Camera (OpenCV Device Index 0, 640x480 resolution, auto-exposure).
- **Dual Thermal Probes**:
  - Produce Core Probe: Stainless steel penetration thermistor probe (via COM/Serial port or calibrated dynamic mock).
  - Ambient Environmental Probe: Digital ambient temperature sensor (operating range 10°C to 40°C).
- **Humidity Probe**: Relative humidity sensor tracking dew point threshold ($\Delta T \ge 4.0^\circ	ext{C}$).
- **Manual Actuation Interface**: Interactive operator dispatch (`station/manual_operator.py`) with physical confirmation tokens.
