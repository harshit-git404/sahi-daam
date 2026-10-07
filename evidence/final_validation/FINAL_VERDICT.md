# Final Validation Verdict

## 1. Invention tested
- **Title:** System and Method for Exposure-Governed Access Sequencing in the Inspection of Partially Observable Bulk Perishable Lots
- **Core Claimed Mechanism:** Dynamic exposure-aware planning trading disposition risk reduction against cumulative, path-dependent physical deterioration and observability degradation.

## 2. Physical apparatus
- Tabletop inspection rig with 5-strata container holding bulk produce lots (potatoes and onions).
- Optical observation aperture for multi-layer camera acquisition.

## 3. Sensor configuration
- **Optical Camera:** Index 0 (640x480 UVC webcam), Active (PASS).
- **Thermal Probes:** Contact thermocouple array at Strata S0–S4: UNMEASURED (No physical multi-probe hardware connected to USB/COM).

## 4. Physical protocol
- Pre-registered in `PROTOCOL_LOCK.md`.
- Matched-exposure plan-swap protocol: Fixed total 35s exposure duration comparing immediate vs delayed observation sequences.

## 5. Training/evaluation split
- **Training Lots:** 20 lots used strictly to calibrate additive cost baseline $c_{\text{add}} = ₹1.3855/\text{sec}$.
- **Held-Out Evaluation Lots:** 20 fresh independent lots (10 potato, 10 onion) evaluated under locked parameters.

## 6. Independent ground truth
- Complete post-inspection physical teardown recorded in `evidence/final_validation/ground_truth/`.
- Planners operated strictly under partial observability without oracle leakage.

## 7. Exposure/history experiment
- Matched 35s Exposure Trial (N = 50):
  - Plan A Mean Damage: 0.033498
  - Plan B Mean Damage: 0.033498
  - Mean Damage Difference: 0.000000 (p = 1.0000)
  - Observation Fidelity Difference: 0.0873 (p = 0.0000e+00)
  - **Path-Dependence Finding:** While temporal thermal drift produced an observation fidelity difference (0.0873), the cumulative physical damage difference was exactly 0.000000 under matched total holding intervals. Physical material damage path-dependence was **NOT DEMONSTRATED**.

## 8. Additive-equivalence experiment
- Evaluated whether additive baseline FB6 can reproduce FB7 decisions:
  - Action Sequence Agreement: **100.0%**
  - Disposition Decision Agreement: **100.0%**
  - FB6 Mean Loss: ₹75.00
  - FB7 Mean Loss: ₹75.00
  - Pairwise Record: 0 Wins / 20 Ties / 0 Losses
  - Relative Advantage: 0.00%
  - **Additive Equivalence Finding:** When properly calibrated from training data, the additive baseline FB6 reproduces FB7's action selection and disposition decisions. The additive model was **NOT REJECTED**.

## 9. Baseline results
Summary across 20 held-out evaluation lots:
- **FB0 (Surface-Only):** Mean Loss = ₹77.20
- **FB1 (Fixed Random):** Mean Loss = ₹107.00
- **FB2 (Depth-Stratified):** Mean Loss = ₹96.40
- **FB5 (State-Blind Lookahead):** Mean Loss = ₹85.80
- **FB6 (Calibrated Additive):** Mean Loss = ₹75.00
- **FB7 (Proposed Exposure-Aware):** Mean Loss = ₹75.00
- **FB7-H (History-Blind Ablation):** Mean Loss = ₹75.00

## 10. FB6 vs FB7
- Paired difference: ₹0.00 (0.00% improvement, 20/20 ties).
- FB7 fails to demonstrate a statistically significant or practical economic advantage over calibrated additive baseline FB6.

## 11. Model misspecification
- Perturbations of $\pm 30\%$ in false-accept costs demonstrated numerical stability of the controller, but did not resolve the fundamental equivalence to additive cost representations.

## 12. Physical reproducibility
- The optical capture loop is reproducible and logged.
- The absence of physical thermocouple hardware precludes thermal reproducibility.

## 13. Limitations
1. Physical temperature probes were absent (UNMEASURED).
2. Produce decay kinetics over inspection timescales (30–90 seconds) are dominated by opening overhead rather than path-dependent non-linear interaction terms.
3. Separable additive cost modeling adequately captures the inspection cost trade-off.

## 14. TRL assessment
- **Current Status:** Advanced TRL 3.
- **TRL 4 Status:** **NOT ACHIEVED** (Fails Gates A, E, F, G).

## 15. Patent relevance
- The hypothesis that bulk perishable inspection requires path-dependent exposure-state tracking is not supported by empirical evidence over standard inspection horizons.
- An additive action-cost model is simpler, more robust, and performs identically.
- Filing an IDF based on non-additive exposure state tracking would fail patent novelty and utility requirements under adversarial prior-art examination.

## 16. Final verdict

```
FAILS — CURRENT INVENTION MECHANISM SHOULD BE ABANDONED
```
