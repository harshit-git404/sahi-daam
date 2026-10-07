# Code Audit: Mechanical State-Altering Inspection System

**Date:** October 2026  
**System:** Sahi Daam Mechanical Inspection Subsystem (`inspection_control/mechanical`)  
**Context:** Engineering sprint evaluating transition from failed thermal/exposure-history mechanism to load-history-aware mechanical state-altering inspection.

---

## 1. Executive Summary

This audit assesses existing modules in `inspection_control/`, determines reusability for the mechanical state-altering inspection mechanism, and specifies architectural changes required to evaluate whether mechanical load history provides a viable inventive step over calibrated additive baselines.

---

## 2. Inventory of Existing Modules and Reusability Assessment

| Existing Module | Path | Status | Reusability / Role | Modifications Required |
|---|---|---|---|---|
| **BulkLot** | `inspection_control/domain/lot.py` | Reused / Extended | Core lot abstraction with strict public/private isolation. | Extracted ground truth, defect distributions; extended by `MechanicalLot`. |
| **StratumState** | `inspection_control/domain/stratum.py` | Reused / Extended | Data structure for per-stratum public state. | Augmented with mechanical state attributes ($F_i, C_i, u_i, L_i^{acc}, R_i$). |
| **AccessGraph** | `inspection_control/domain/access_graph.py` | Reused / Extended | Precedence-constrained physical DAG. | Retained for layer accessibility; augmented with mechanical actions (`HOLD`, `RECONFIGURE`). |
| **DispositionEvaluator** | `inspection_control/domain/disposition.py` | Reused | Terminal economic loss matrix (ACCEPT, MARKDOWN, REJECT, REROUTE, SPLIT, ESCALATE). | Unchanged to preserve identical economic penalty evaluation. |
| **ExposureLedger** | `inspection_control/domain/exposure_state.py` | Deprecated (Thermal) | Thermal exposure accumulation ledger. | Replaced by `MechanicalStateLedger` tracking load-deformation history. |
| **IInspectionPlanner** | `inspection_control/planning/planner.py` | Reused | Universal planner contract: `select_next_action()`, `recommend_terminal_disposition()`. | Maintained for FB0–FB7 interoperability. |
| **Baselines (FB0–FB6)** | `inspection_control/planning/baselines.py` | Reused / Adapted | Reference baselines (surface-only, random, depth, VOI, state-blind, additive). | Re-implemented under mechanical cost and observation interfaces. |
| **Runner** | `inspection_control/experiments/runner.py` | Reused / Adapted | Closed-loop episode execution harness. | Adapted for mechanical sensor fusion and state updating. |
| **AuditLogger** | `inspection_control/evidence/logger.py` | Reused | Structured CSV/JSON telemetry audit trail. | Log fields updated for load cell readings, compression, and mechanical state. |
| **Backend Tests** | `backend/tests/` (77 tests) | Preserved | Core Sahi Daam web application, pricing engine, authentication. | ZERO modifications. Must continue to pass 100%. |

---

## 3. New Modules Created

The new subsystem is located in `inspection_control/mechanical/`:

1. **`sensor_interface.py`**:
   - `MechanicalSensorInterface`: Abstract sensor driver contract for load cells, pressure mats, and displacement sensors.
   - `PhysicalMechanicalSensorStub`: Production hardware driver stub allowing zero-rearchitecture drop-in of real load cells in future physical validation.
2. **`simulated_sensors.py`**:
   - `SimulatedLoadCell`: Multi-axis load cell simulation with configurable noise, bias, drift, quantization, latency, and dropout.
   - `SimulatedDisplacementSensor`: Optical/linear encoder simulator tracking top-surface and inter-stratum settlement.
   - `SimulatedPressureSensor`: Tactile grid sensor measuring contact pressure distribution.
   - Explicitly marked: `SIMULATED HARDWARE`.
3. **`mechanical_state.py`**:
   - `MechanicalStratumState`: Per-stratum state carrying normal force $F_i$, compression $C_i$, displacement $u_i$, accumulated load history $L_i^{acc}$, recovery state $R_i$, and residual deformation $D_i$.
   - `MechanicalStateLedger`: Tracks cumulative and transient mechanical history across inspection steps.
4. **`lot_mechanical_model.py`**:
   - `MechanicalBulkLot`: 5-stratum bulk perishable lot with heterogeneous stiffness ($k_i$), deformation susceptibility ($\beta_i$), and load redistribution matrix ($\mathbf{K}$).
   - Load redistribution physics: Removal of stratum $k$ redistributes normal load to remaining strata via load-transfer coefficients, rather than simple gravity subtraction.
   - Mechanical memory / hysteresis model: Viscoelastic relaxation and plastic settling parameterized by `mechanical_memory_strength`.
5. **`observability_model.py`**:
   - `MechanicalObservabilityModel`: Coupled observation operator $G(\theta_i, C_i, u_i, \epsilon)$ where mechanical compression and deformation modify visual defect occlusion and contrast.
6. **`condition_model.py`**:
   - `MechanicalConditionModel`: Coupled deterioration operator simulating pressure-induced bruising, internal tissue damage, and defect activation under excessive or prolonged mechanical stress.
7. **`sensor_fusion.py`**:
   - `MechanicalSensorFusion`: Kalman-style state estimator synthesizing noisy load cell, displacement, and camera signals into a filtered mechanical state belief with confidence intervals.
8. **`planners/`**:
   - `fb7_mechanical_planner.py`: Receding-horizon state-aware controller accounting for carried mechanical state, future load redistribution, and inspection-induced damage.
   - `fb6_mechanical_additive.py`: Calibrated additive baseline mapping physical actions to static additive costs without carried state.
   - `fb5_state_blind.py`: Lookahead planner optimizing purely for information gain without mechanical awareness.
   - `oracle_planner.py`: Oracle with full access to latent ground truth and deterministic mechanical dynamics.
9. **`experiment_runner.py`**:
   - High-throughput simulation harness supporting 10,000+ training and 10,000+ evaluation episodes, parameter freezes, and ablation sweeps.

---

## 4. Key Modeling Assumptions & Justifications

1. **Discrete Layered Stacking (5 Strata):** Bulk produce (e.g. potatoes, apples, onions) in standard shipping crates (50–60 kg, ~40–60 cm depth) behaves as a discrete stratified column where vertical gravity stress increases monotonically with depth.
2. **Nonlinear Load Redistribution:** Removing a layer releases normal stress but causes redistribution due to container friction, bridging, and lateral settling ($\mathbf{F}_{rem} = \mathbf{A}_{redist} \mathbf{F}$).
3. **Viscoelastic producing response:** Fresh agricultural commodities exhibit viscoelastic behavior (Maxwell-Wiechert / Kelvin-Voigt equivalent), leading to time-dependent creep under load and partial recovery upon unloading.
4. **Strict Architectural Isolation:** The planner never accesses latent stratum defect rates or true simulated state variables directly. It interacts only through noisy sensor fusion outputs and public stratum descriptors.

---

## 5. Known Limitations

1. **Simulation Fidelity:** While modeling viscoelastic deformation and load redistribution, the simulator does not compute 3D finite element analysis (FEA) or discrete element method (DEM) granular particles.
2. **Hardware Status:** Real load cells and displacement encoders are NOT physically connected. All hardware outputs are generated by high-fidelity mathematical simulations and explicitly labeled as such.
3. **Economic Calibration:** Loss parameters match the accepted Sahi Daam wholesale agricultural pricing and disposition schedule.
