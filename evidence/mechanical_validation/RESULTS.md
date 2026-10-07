# Empirical Results: Mechanical State-Altering Inspection

**Total Evaluation Episodes:** 10,000 lots  
**Date of Execution:** October 2026

---

## 1. Primary Success Metrics (FB6 vs FB7)

| Metric | FB6 Calibrated Additive | FB7 State-Aware | Paired Delta (FB6 - FB7) |
|---|---|---|---|
| **Mean Terminal Loss (INR)** | ₹51.33 | ₹50.51 | ₹0.82 |
| **Median Terminal Loss (INR)** | ₹5.00 | ₹5.00 | ₹0.00 |
| **Standard Deviation (INR)** | ₹74.64 | ₹74.37 | - |
| **Bootstrap 95% CI** | - | - | [₹0.62, ₹1.03] |
| **Win / Tie / Loss Counts** | - | - | **196 wins / 9758 ties / 46 losses** |
| **Action Sequence Agreement** | - | - | **97.6%** |
| **Disposition Agreement** | - | - | **99.4%** |
| **Oracle Gap Closed** | - | - | **1.60%** |

---

## 2. Benchmark Against All Planners

| Planner | Mean Loss (INR) | Median Loss (INR) | Std Dev (INR) | Description |
|---|---|---|---|---|
| **FB0** | ₹44.63 | ₹5.00 | ₹71.18 | Surface-only inspection |
| **FB1** | ₹62.66 | - | - | Fixed random sampling |
| **FB2** | ₹107.74 | - | - | Depth-stratified excavation |
| **FB3** | ₹25.92 | - | - | Myopic greedy information gain |
| **FB4** | ₹25.92 | - | - | Generic VOI without mechanics |
| **FB5** | ₹51.36 | ₹5.00 | ₹74.67 | State-blind lookahead |
| **FB6** | ₹51.33 | ₹5.00 | ₹74.64 | Calibrated additive baseline |
| **FB7** | ₹50.51 | ₹5.00 | ₹74.37 | Mechanical state-aware controller |
| **ORACLE** | ₹0.00 | ₹0.00 | ₹0.00 | Ground truth omniscient lower bound |

---

## 3. Results by Physical Regime

| Regime | FB6 Mean Loss (INR) | FB7 Mean Loss (INR) | FB7 Advantage (INR) | Action Agreement |
|---|---|---|---|---|
| REGIME 1: Null Regime (Zero Coupling) | ₹51.88 | ₹51.91 | ₹-0.04 | 99.3% |
| REGIME 2: Low Mechanical Memory | ₹52.10 | ₹52.13 | ₹-0.04 | 99.3% |
| REGIME 3: Medium Mechanical Memory | ₹52.23 | ₹52.26 | ₹-0.02 | 99.5% |
| REGIME 4: High Mechanical Memory | ₹51.64 | ₹51.71 | ₹-0.07 | 98.6% |
| REGIME 5: Memory + Obs Coupling | ₹51.76 | ₹51.78 | ₹-0.02 | 99.7% |
| REGIME 6: Memory + Condition Coupling | ₹51.12 | ₹51.16 | ₹-0.04 | 99.2% |
| REGIME 7: Full Multi-Modal Coupling | ₹50.48 | ₹50.48 | ₹-0.01 | 99.9% |
| REGIME 8: High Sensor Noise | ₹51.51 | ₹45.05 | ₹6.46 | 88.8% |
| REGIME 9: Sensor Frame Dropout (10%) | ₹50.24 | ₹48.27 | ₹1.96 | 91.6% |
| REGIME 10: Model Mismatch (+/-25%) | ₹50.37 | ₹50.38 | ₹-0.01 | 99.9% |

---

## 4. Ablation Study Results
- **FB7 Full:** ₹1.81
- **No Mechanical Memory:** ₹4.34
- **No Obs Coupling:** ₹5.00
- **No Condition Coupling:** ₹1.81
- **No State Uncertainty:** ₹1.81
