# Simulation Protocol: Mechanical State-Altering Inspection

**LABEL:** SIMULATED PHYSICAL ENVIRONMENT  
**Status:** Engineering Simulation Protocol (TRL 3)

---

## 1. Physical Mechanics Formulation

The bulk perishable lot is modeled as a 5-stratum stack (S0 to S4) with discrete vertical stress equilibrium:

$$F_i(t) = W_i + \sum_{j < i, j \in \text{present}} W_j + \Delta F_{redist}(i)$$

### Load Redistribution on Stratum Removal
When stratum $k$ is removed:
1. Stratum $k$ is removed from the active stack ($F_k = 0$).
2. Direct vertical gravity load on strata $j > k$ drops by $W_k$.
3. Crate wall friction and collapse of granular lateral arches transfer stress back onto remaining strata:
   $$\Delta F_{redist}(j) = N_{removed} \cdot \alpha_{trans} \cdot g \cdot 1.5$$

### Viscoelastic Hysteresis and Memory
- Strain creeps towards steady state:
  $$C_i(t) = (1 - \alpha) C_i(t - \Delta t) + \alpha \frac{F_i}{k_i}$$
- Plastic deformation accumulates under excessive sustained contact stress:
  $$D_{perm, i}(t) = D_{perm, i} + \gamma \beta_i \max(0, F_i - F_{yield}) \frac{\Delta t}{100}$$
- Incomplete recovery upon unloading creates path dependence between identical loading durations applied under different sequences.

---

## 2. Sensor Abstraction Layer
The controller accesses sensors through `MechanicalSensorInterface`:
- `SimulatedLoadCell`: Range 0–1000 N, resolution 0.1 N, Gaussian noise, thermal drift.
- `SimulatedDisplacementSensor`: LVDT simulation measuring settlement in cm.
- `SimulatedPressureMat`: Tactile grid contact pressure in kPa.
- All sensor transducers inject configurable noise, bias, quantization, and frame dropout.
