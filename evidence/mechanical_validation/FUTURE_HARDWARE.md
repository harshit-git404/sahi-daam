# Future Physical Hardware Specification (Engineering Design Specification)

**Notice:** THIS IS A FUTURE ENGINEERING DESIGN SPECIFICATION.  
**Physical Hardware Status:** NOT CURRENTLY PROCURED OR CONNECTED.  
Do not interpret this document as evidence that physical hardware was measured or demonstrated.

---

## 1. Physical Instrumentation Concept

To transition the software architecture from TRL 3 simulation to TRL 4 laboratory validation without software refactoring, the following hardware subsystem is specified:

```
+-----------------------------------------------------------+
|               Overhead RGB-D Optical Camera               |
|            (RealSense D435 / Basler ace 2 4K)             |
+-----------------------------------------------------------+
                             |
                             v
+-----------------------------------------------------------+
|                  Stratum S0 (Top Layer)                   |
+-----------------------------------------------------------+
|  [Tactile Pressure Matrix P1: Tekscan 5101 / Piezo-mat]   |
+-----------------------------------------------------------+
|                  Stratum S1 (Upper-Mid)                   |
+-----------------------------------------------------------+
|                  Stratum S2 (Core Layer)                  |
+-----------------------------------------------------------+
|                  Stratum S3 (Lower-Mid)                   |
+-----------------------------------------------------------+
|  [Linear Displacement Encoder D1: Keyence LVDT 0-300mm]   |
+-----------------------------------------------------------+
|                  Stratum S4 (Base Floor)                  |
+-----------------------------------------------------------+
|  [Multi-Point Base Load Cell Tray: 4x HBM SP4M 50kg, 24b] |
+-----------------------------------------------------------+
                             |
                             v
            Industrial ADC & Signal Conditioner
                  (HX711 / National Instruments DAQ)
                             |
                             v
               USB-Serial / Ethernet Stream
                             |
                             v
            `PhysicalMechanicalSensorDriver` Python Module
```

---

## 2. Sensor Components and Specifications

### 2.1 Base Load Cell Array
- **Model Recommendation:** 4x Strain-gauge single-point load cells (e.g., HBM SP4M or Vishay Celtron LOC, 50 kg capacity each, total 200 kg platform capacity).
- **Summing Junction & ADC:** 24-bit delta-sigma ADC (ADS1232 or HX711 dual-channel) running at 10–80 samples/sec.
- **Physical Placement:** Mounted beneath the 4 corners of an isolated rigid false-bottom baseplate supporting the produce crate.
- **Accuracy Class:** OIML R60 C3 (3000 verification divisions).
- **Tare Weight Handling:** Electronic tare of empty crate tare mass (3.5 kg) via software zero.

### 2.2 Inter-Strata Tactile Pressure Mats
- **Model Recommendation:** Tekscan I-Scan 5101 thin-film piezoresistive pressure mat (0.1 mm thickness to avoid altering contact mechanics).
- **Sensing Area:** 400 mm x 300 mm active area, 44 x 44 sensing sensels (1,936 sensels).
- **Pressure Range:** 0 to 50 kPa.
- **Placement:** Placed beneath stratum $S_0$ and stratum $S_2$ to record inter-stratum load transfer and bridge formation.

### 2.3 Vertical Displacement & Settlement Sensor
- **Model Recommendation:** Keyence GT2 series contact LVDT or Micro-Epsilon optoNCDT 1420 laser triangulation sensor (0–300 mm range).
- **Resolution:** $0.01$ mm.
- **Placement:** Mounted to a top fixture gantry measuring vertical height delta of the produce column during progressive removal and resting phases.

---

## 3. Communication Protocol and Driver Interface

All sensors must output data via standard serial/TCP JSON streams conforming to the `MechanicalSensorInterface` Python abstraction:

```json
{
  "timestamp_iso": "2026-10-07T18:00:00.000Z",
  "base_load_kg": 48.32,
  "base_forces_n": [118.5, 122.1, 115.8, 117.9],
  "interstrata_pressures_kpa": [12.4, 28.6, 42.1],
  "column_displacement_mm": 14.82,
  "status": "OK",
  "calibration_checksum": "0xA93F"
}
```

The software driver `PhysicalMechanicalSensorDriver` implements:
- `read_force_vector() -> np.ndarray`
- `read_compression_vector() -> np.ndarray`
- `read_displacement() -> float`
- `tare_sensor() -> None`

This ensures **zero modifications to the planning controllers (FB6, FB7)** when transitioning from `SimulatedLoadCell` to real physical hardware.
