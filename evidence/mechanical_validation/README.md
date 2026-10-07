# Mechanical State-Altering Inspection Validation Evidence

**Working Title:** Load-History-Aware Adaptive Inspection of Partially Observable Bulk Perishable Lots  
**Status:** PROMISING BUT INSUFFICIENT  
**Evidence Type:** High-Fidelity Hardware-Equivalent Simulation (TRL 3)  
**Hardware Notice:** SIMULATED HARDWARE & SIMULATED PHYSICAL ENVIRONMENT. No physical load cells were connected.

---

## Overview

This repository contains the complete empirical evidence evaluating whether replacing the failed thermal/exposure-history mechanism with a **mechanically state-altering inspection mechanism** provides an authentic, non-additive inventive advantage.

### Key Results Summary
- **Evaluation Episodes:** 10,000 held-out lots across 10 distinct physical regimes.
- **FB6 Calibrated Additive Mean Loss:** ₹51.33
- **FB7 Mechanical State-Aware Mean Loss:** ₹50.51
- **Paired Mean Difference:** ₹0.82 [95% CI: ₹0.62, ₹1.03]
- **Win / Tie / Loss:** 196 wins / 9758 ties / 46 losses
- **Action Sequence Agreement:** 97.6% (Additive equivalence rejected)
- **Oracle Gap Closed:** 1.60%
- **Executive Verdict:** `PROMISING BUT INSUFFICIENT`

---

## Directory Index
- `CODE_AUDIT.md`: Inventory of reused, modified, and newly created software modules.
- `ASSUMPTIONS.md`: Documented simulation assumptions and parameter definitions.
- `FUTURE_HARDWARE.md`: Engineering design specification for future TRL 4 instrumentation.
- `SIMULATION_PROTOCOL.md`: Physical equations, load redistribution, and sensor fusion dynamics.
- `TRAINING_PROTOCOL.md`: Protocol for training and freezing the FB6 additive baseline.
- `EVALUATION_PROTOCOL.md`: 10-regime evaluation matrix and statistical procedures.
- `RESULTS.md`: Detailed tabulated performance metrics.
- `KILL_TEST.md`: Explicit verification against the 8 kill criteria.
- `FINAL_VERDICT.md`: Formal technical verdict and recommendation.
- `CLAUDE_HANDOFF.md`: Comprehensive handoff dossier for Claude adversarial review.
