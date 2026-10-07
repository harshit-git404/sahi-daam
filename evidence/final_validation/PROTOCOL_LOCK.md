# Pre-Registered Evaluation Protocol Lock (`PROTOCOL_LOCK.md`)

**Date**: 2026-10-07  
**Commit Status**: PRE-REGISTERED & LOCKED PRIOR TO FINAL EVALUATION RUN.  
**Invention Core Under Test**: *Non-additive, history-dependent exposure coupling between physical access constraints, cumulative thermal exposure integrals, subsequent observation fidelity, and downstream packout disposition risk.*

---

## 1. Experimental Split Design

### A. Training & Calibration Set (20 Lots: `TRAIN_01` .. `TRAIN_20`)
- **Purpose**:
  1. Fit linear additive exposure rate $c_{\text{add}}$ (INR/sec) for baseline **FB6** via ordinary least squares regression.
  2. Calibrate prior variance weights and action cost thresholds.
- **Rules**: Calibration data is completely isolated. No evaluation lot data may be used for parameter fitting.

### B. Held-Out Evaluation Set (20 Lots: `EVAL_01` .. `EVAL_20`)
- **Composition**:
  - 10 Potato lots, 10 Onion lots.
  - Regimes: Adversarial (clean top / rotten bottom), Depth-Correlated Spoilage, Hidden-Bottom, and Benign.
- **Rule**: **PARAMETERS LOCKED**. Zero hyper-parameter adjustment or threshold tuning allowed after looking at evaluation results.

---

## 2. Fair Baseline Specifications

All planners operate under the **identical** physical access DAG, action costs, sensor feeds, prior beliefs, budget constraints, and downstream disposition loss matrices:

1. **FB0 (Surface Only)**: Observes $S_0$ once, then commits terminal disposition.
2. **FB1 (Fixed Sampling)**: Takes up to 2 physical sample units from accessible strata, then terminates.
3. **FB2 (Depth-Stratified)**: Rigidly excavates and samples strata $S_0 \to S_1 \to S_2 \to S_3$ up to budget.
4. **FB5 (State-Blind Lookahead)**: Multi-step lookahead planner that models physical unstacking and informational variance reduction, but assumes produce deterioration cost is ₹0.0.
5. **FB6 (Calibrated Additive Baseline)**: Non-strawman additive baseline. Evaluates multi-step lookahead using:
   $$\text{Cost}(a) = \text{physical\_labor\_cost}(a) + c_{\text{add}} \cdot \text{duration}(a)$$
   where $c_{\text{add}}$ is strictly fitted from the 20 training lots.
6. **FB7 (Proposed Exposure-State Planner)**: Uses receding-horizon control with non-additive history ledger tracking cumulative exposure seconds and thermal integrals.
7. **FB7-H (History-Blind Ablation)**: Identical to FB7, but the carried exposure ledger history ($t_{\text{cum}}$, times opened) is cleared at each step ($t_{\text{cum}} = 0$). Tests whether carried history produces any measurable difference.

---

## 3. Pre-Registered Test Matrix

### Test 1: Matched-Exposure Plan-Swap Test (Criterion 8)
- Paired comparison on identical lots where total open exposure duration is strictly matched:
  - **Plan A**: Open $S_1$ (10s) $\to$ Observe $S_1$ (5s) $\to$ Hold open (20s) $\to$ Reclose (5s).
  - **Plan B**: Open $S_1$ (10s) $\to$ Hold open (20s) $\to$ Observe $S_1$ (5s) $\to$ Reclose (5s).
- Total open duration is matched at exactly 35 seconds.
- Metric: End-of-trial condition damage $\Delta D$ and observation fidelity $\eta$.

### Test 2: Additive-Equivalence Kill Test (Criterion 16)
- Evaluates whether FB7's action sequences and final disposition decisions differ from the calibrated additive baseline FB6.
- Metrics: Action agreement %, Disposition agreement %, Loss delta (INR), Win / Tie / Loss counts.

### Test 3: 20-Lot Cross-Baseline Benchmark (Criterion 9, 13, 14)
- Evaluates FB0, FB1, FB2, FB5, FB6, FB7, and FB7-H across the 20 held-out evaluation lots.
- Primary Metric: Expected total disposition loss (INR) and fraction of oracle gap closed.
- Secondary Metrics: False accept rate, inspection cost, cumulative exposure time.

### Test 4: Model Misspecification Grid (Criterion 11, 17)
- Controller assumptions perturbed by $-30\%$, $-15\%$, $0\%$, $+15\%$, $+30\%$ on deterioration decay and sensor noise against fixed ground truth dynamics.

---

## 4. Hardware & Physical Ground-Truth Rules

- **RGB Vision**: Real OpenCV camera (Device Index 0) active for optical frame acquisition.
- **Thermal Probes**: No physical thermocouple probes attached to workstation USB ports. Probes are marked **UNMEASURED** per Criterion 2.
- **Teardown Ground Truth**: Controller is architecturally prevented from reading private ground-truth attributes during inspection. Complete teardown grading executed only after terminal disposition is committed.

---

## 5. Success vs Failure Gate Criteria (Criterion 22)

- **SUCCESS (Proceed to Claude Review)**:
  1. FB7 achieves a statistically significant ($p < 0.05$) reduction in disposition loss over calibrated FB6 on held-out lots.
  2. Plan-swap demonstrates measurable path dependence under matched total exposure.
  3. FB7 outperforms FB7-H (proving history is doing useful work).
  4. Physical sensors are operational and logged.
- **FAILURE (Kill / Abandon Direction)**:
  1. FB7 fails to beat calibrated FB6 (ties or worse).
  2. Plan-swap shows zero divergence in physical state.
  3. External thermal probes remain unmeasured.
