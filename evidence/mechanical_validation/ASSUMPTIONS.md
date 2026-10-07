# Simulation Assumptions and Engineering Model Parameters

**Status:** SIMULATED HARDWARE & SIMULATED PHYSICAL ENVIRONMENT  
**Notice:** These values are engineering simulation assumptions. No real physical load cell or laboratory measurements were collected during this sprint.

---

## 1. Physical Stack and Bulk Produce Properties

A bulk crate containing 5 discrete vertical strata ($S_0$ through $S_4$) of agricultural produce (representative commodity: potato / apple):

- **Number of strata:** 5 ($S_0$: surface, $S_1$: upper-middle, $S_2$: core, $S_3$: lower-middle, $S_4$: crate floor).
- **Units per stratum:** 50 units (total lot size: 250 units).
- **Nominal mass per stratum:** 10.0 kg (nominal total crate mass: 50.0 kg / ~490.5 N).
- **Mass variation:** Gaussian $\sigma = 0.5$ kg per stratum.
- **Strata stiffness ($k_i$):**
  - $S_0$: $120.0$ N/cm
  - $S_1$: $140.0$ N/cm
  - $S_2$: $160.0$ N/cm (denser core packing)
  - $S_3$: $180.0$ N/cm
  - $S_4$: $210.0$ N/cm (support base)
- **Viscoelastic relaxation time constant ($\tau$):** 30.0 seconds.
- **Permanent plastic deformation threshold:** $180.0$ N sustained contact force.

---

## 2. Load Transfer and Redistribution Mechanics

Vertical loading does not behave as an ideal decoupled gravity stack. Lateral wall friction and granular bridging transfer part of the load to crate sidewalls and adjacent strata.

- **Load transfer coefficient ($\alpha_{ij}$):** When stratum $k$ is removed, remaining strata experience a redistribution factor:
  $$\Delta F_i = -W_k \cdot \delta_{i > k} + \sum_{j \neq k} \mathbf{K}_{ij} \cdot W_k$$
  where $\mathbf{K}$ captures lateral force relief and arching collapse.
- **Dynamic settling spike:** Immediate physical disturbance during removal introduces a transient impulse load factor of $1.15 \times$ on the stratum directly underneath before settling.

---

## 3. Viscoelastic Recovery and Mechanical Memory

When load is removed (unloading), stratum deformation $D_i(t)$ does not instantaneously return to zero. It follows a two-component recovery curve:

$$D_i(t) = D_{elastic} + D_{viscous}(t) + D_{plastic}$$
- **Elastic recovery:** Instantaneous rebound (30–60% of total strain depending on produce freshness).
- **Viscoelastic recovery:** Time-dependent relaxation governed by $\tau$:
  $$D_{viscous}(t) = D_{viscous}(0) \cdot \exp(-t / \tau)$$
- **Plastic deformation:** Irreversible strain that accumulates when peak load exceeds yield threshold.
- **`mechanical_memory_strength` parameter:** Scaler $\gamma \in [0.0, 1.0]$:
  - $\gamma = 0.0$: Null memory (ideal elastic; instantaneous recovery; no hysteresis).
  - $\gamma = 0.2$: Low memory.
  - $\gamma = 0.5$: Medium memory (standard viscoelastic perishable behavior).
  - $\gamma = 1.0$: High memory (pronounced plastic settling and creep).

---

## 4. Observability Coupling Model

Mechanical state modifies surface geometry, inter-item contact gaps, and optical defect visibility:

- **Visibility factor:** $V_i = \max(0.2, 1.0 - \lambda_{obs} \cdot (C_i / C_{max}))$, where $\lambda_{obs} \in [0.0, 0.8]$ is the observation coupling strength.
- Under heavy compression, items are tightly packed, reducing lateral facet visibility and occluding basal rot.
- Under decompression (unloading), items settle and separate, improving defect contrast after a settling time delay.

---

## 5. Condition Coupling (Mechanical Damage) Model

Excessive sustained mechanical load induces bruising and accelerated tissue breakdown:

- **Damage threshold:** $F_{thresh} = 150.0$ N.
- **Damage rate:** When $F_i > F_{thresh}$, produce condition deteriorates at rate:
  $$\Delta \theta_i = \lambda_{dmg} \cdot \frac{F_i - F_{thresh}}{F_{thresh}} \cdot \frac{\Delta t}{3600}$$
  where $\lambda_{dmg} \in [0.0, 0.05]$ is the damage coupling strength.
- When $\lambda_{dmg} = 0.0$, mechanical inspection causes zero produce damage (null regime).

---

## 6. Simulated Sensor Specifications (Engineering Assumptions)

| Sensor Type | Nominal Range | Resolution | Gaussian Noise ($\sigma$) | Bias ($\mu$) | Dropout Rate | Sampling Rate |
|---|---|---|---|---|---|---|
| **Simulated Load Cell** (Bottom Mat) | 0 – 100 kg | 0.01 kg | 0.05 kg | $\pm 0.02$ kg | 0.00 – 0.05 | 10 Hz |
| **Simulated Pressure Grid** (Inter-strata) | 0 – 50 kPa | 0.05 kPa | 0.2 kPa | $\pm 0.1$ kPa | 0.00 – 0.05 | 5 Hz |
| **Simulated Displacement Sensor** (LVDT/Optical) | 0 – 30 cm | 0.05 mm | 0.2 mm | $\pm 0.1$ mm | 0.00 – 0.02 | 10 Hz |

*Explicit Notice: These values are engineering simulation assumptions.*
