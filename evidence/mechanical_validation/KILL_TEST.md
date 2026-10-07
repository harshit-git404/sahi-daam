# Kill Test Audit: Mechanical State-Altering Inspection

**Date:** October 2026  
**Auditor:** Autonomous Sprint Harness

---

## 8 Mandatory Kill Criteria Audit

| # | Kill Criterion | Threshold / Condition | Measured Value | Status |
|---|---|---|---|---|
| **1** | FB7 beats calibrated FB6 in coupled regimes | $\Delta \text{Loss} > 0$ in Regime 7 | ₹-0.01 | **KILL** |
| **2** | FB7 advantage persists when memory is present | $\Delta \text{Loss} > 0$ across memory regimes | ₹0.82 | **PASS** |
| **3** | FB6 reproduces FB7 action sequences | Action Agreement $< 95\%$ (no cloning) | **97.6%** | **KILL** |
| **4** | Mechanical state affects future observation/condition | Path dependence detected | Detected (Comp Diff = 0.0332 cm) | **PASS** |
| **5** | Advantage exists only because FB6 was weakened | FB6 calibrated on 10,000 training lots | Additive weights calibrated & frozen | **PASS** |
| **6** | Advantage disappears under modest model mismatch | Advantage remains positive across $\pm 50\%$ mismatch | Maintained across all $\pm 50\%$ levels | **PASS** |
| **7** | Advantage exists only in one cherry-picked regime | Advantage in $\ge 6$ regimes | Advantage in 2/10 regimes | **KILL** |
| **8** | Mechanical state is just an additive action cost | Path dependence verified, agreement $<90\%$ | Hysteresis verified; agreement 97.6% | **KILL** |

---

## Conclusion
**4 OF 8 KILL CRITERIA TRIGGERED KILL CONDITIONS (Criteria 1, 3, 7, 8).**  
While physical path-dependence and viscoelastic strain hysteresis were successfully demonstrated in simulation (Plan A vs Plan B divergence = 0.0332 cm), the calibrated additive baseline FB6 clones FB7's inspection actions in **97.6%** of held-out episodes. 

Consequently, **Additive Equivalence is NOT Rejected**, and the mechanism yields only a marginal ₹0.82 loss advantage (1.60% oracle gap closure).

**Final Gate Assessment:** `PROMISING BUT INSUFFICIENT`.  
The patent gate remains locked. Do NOT prepare IDF. Proceed to Claude adversarial review.

