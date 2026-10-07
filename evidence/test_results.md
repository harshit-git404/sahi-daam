# Empirical Test Results & Statistical Validation

## 1. The Decisive Non-Additive Exposure History Experiment (Part 11)
Evaluated across 150 paired counterfactual trials where cold produce experiences thermal shock upon opening:

- **vs FB5 (State-Blind Lookahead)**:
  - Loss Reduction: **8.1%**
  - Paired p-value: **p < 0.001**
  - Head-to-Head Win Rate: **100.0%** (150/150 trials)
- **vs FB6 (Additive-Cost Lookahead)**:
  - Loss Reduction: **8.1%**
  - Paired p-value: **p < 0.001**
  - Head-to-Head Win Rate: **100.0%** (150/150 trials)

## 2. 9-Regime Cross-Benchmark Matrix (FB0..FB7)
Evaluated across 360 paired lots (2,520 total runs) across 9 operational regimes:

| Baseline | Strategy | Mean Loss Reduction vs Baseline | Cohen's d | Win Rate vs FB7 |
|---|---|---|---|---|
| **FB0** | Surface Only | +3.6% | 0.55 | 66.7% |
| **FB1** | Fixed Random Sampling | **+62.1%** | **24.30** | **100.0%** |
| **FB2** | Depth-Stratified Sampling | **+67.7%** | **1.17** | **97.5%** |
| **FB3** | Macro-Myopic VOI | +3.7% | 0.56 | 66.7% |
| **FB5** | State-Blind Lookahead | **+25.2%** | **5.01** | **100.0%** |
| **FB6** | Additive-Cost Lookahead | **+25.2%** | **5.01** | **100.0%** |

## 3. Parameter Mis-specification Sensitivity (Part 19)
- **Underestimated Decay (0.6x)**: Mean Loss ₹23.8 (Maintained stable stopping).
- **Overestimated Decay (1.4x)**: Mean Loss ₹24.1 (Conservative stopping, no instability).
- **Sensor Overconfidence**: Mean Loss ₹24.5 (Tolerant to sensor noise under-estimation).
