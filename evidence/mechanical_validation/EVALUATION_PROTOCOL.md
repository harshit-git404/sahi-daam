# Evaluation Protocol: 10-Regime Evaluation Matrix

**Objective:** Rigorously compare FB7 against FB6 across 10,000 held-out evaluation lots across 10 distinct physical regimes.

---

## 1. Experimental Matrix

| Regime ID | Regime Name | Memory ($\gamma$) | Obs Coupling | Cond Coupling | Load Noise | Dropout | Model Mismatch |
|---|---|---|---|---|---|---|---|
| 1 | Null Regime | 0.0 | 0.0 | 0.0 | 0.5 N | 0% | 0% |
| 2 | Low Memory | 0.2 | 0.0 | 0.0 | 0.5 N | 0% | 0% |
| 3 | Medium Memory | 0.5 | 0.0 | 0.0 | 0.5 N | 0% | 0% |
| 4 | High Memory | 1.0 | 0.0 | 0.0 | 0.5 N | 0% | 0% |
| 5 | Memory + Obs | 0.5 | 0.35 | 0.0 | 0.5 N | 0% | 0% |
| 6 | Memory + Cond | 0.5 | 0.0 | 0.25 | 0.5 N | 0% | 0% |
| 7 | Full Multi-Modal | 0.5 | 0.35 | 0.25 | 0.5 N | 0% | 0% |
| 8 | High Sensor Noise | 0.5 | 0.35 | 0.25 | 5.0 N | 0% | 0% |
| 9 | Sensor Dropout | 0.5 | 0.35 | 0.25 | 0.5 N | 10% | 0% |
| 10 | Model Mismatch | 0.5 | 0.35 | 0.25 | 0.5 N | 0% | $\pm 25\%$ |

---

## 2. Statistical Procedures
- 1,000 held-out lots per regime = 10,000 total episodes.
- Seed base: 200,000 (disjoint from training).
- Non-parametric paired difference test and 1,000-sample bootstrap 95% confidence intervals.
