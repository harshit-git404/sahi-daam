# Sensor Placement Protocol for Tabletop Produce Lot Station

## 1. Geometric Coordinate Setup
- **Reference Origin (0,0,0)**: Top center of the tabletop produce crate enclosure.
- **Z-Axis**: Vertical downward axis corresponding to physical strata depth:
  - Stratum 0 ($S_0$, Exposed Surface): $Z = 0\text{ cm}$
  - Stratum 1 ($S_1$, Near Surface): $Z = 5\text{ cm}$
  - Stratum 2 ($S_2$, Middle Tray): $Z = 10\text{ cm}$
  - Stratum 3 ($S_3$, Deep Layer): $Z = 15\text{ cm}$
  - Stratum 4 ($S_4$, Container Floor): $Z = 20\text{ cm}$

## 2. Optical Sensor Placement
- **Camera Mount**: Rigid overhead boom arm positioned at $Z = -45\text{ cm}$ perpendicular to the crate surface.
- **Illumination**: Dual diffused 5500K LED array flanking the crate at 45° incident angles to prevent direct specular glare on produce skin.
- **Field of View**: Fully spans the $40\text{ cm} \times 30\text{ cm}$ crate footprint.

## 3. Physical Probing Placement Protocol (When Microcontroller Connected)
- **Probe 1 (Ambient)**: Located at $Z = -20\text{ cm}$, 15 cm lateral to crate sidewall, shielded from direct airflow.
- **Probe 2 ($S_0$ Surface)**: Penetration depth 5 mm beneath epidermal skin of central produce unit in top layer.
- **Probe 3 ($S_2$ Core)**: Positioned within intermediate produce tray.
- **Probe 4 ($S_4$ Floor)**: Positioned at base of container adjacent to lower drainage holes.
