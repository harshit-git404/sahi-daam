# Training Protocol and Baseline Calibration

**Objective:** Fit high-fidelity additive per-action costs for FB6 on 10,000 training lots to strictly avoid strawman baseline comparisons.

---

## 1. Training Dataset Generation
- **Sample Size:** 10,000 independent simulated lots.
- **RNG Seed Base:** 10001 (isolated from evaluation seeds).
- **Physical Distributions:** Balanced sampling across all 7 defect patterns (Uniform, Depth-Correlated, Hidden-Bottom, Clustered, Surface-Biased, Benign, Adversarial).
- **Mechanical Memory:** Randomly uniformly sampled $\gamma \in [0.1, 0.8]$.

---

## 2. Additive Cost Estimation
For each physical action $a \in \{OBSERVE, REMOVE, HOLD, RECONFIGURE\}$, the empirical marginal mechanical damage was measured:
$$c_{add}(a) = \mathbb{E}_{training}[\text{DamageLoss}_{economic}(a)]$$

### Frozen Calibrated Weights
```json
{
  "OBSERVE": 0.25,
  "REMOVE": 0.04514999447610149,
  "HOLD": 0.05643250860606586,
  "RECONFIGURE": 1.25
}
```

**Zero Data Leakage Assertion:**
Parameters were frozen and written to `calibrated_fb6_weights.json` before any evaluation episode was initialized.
