# Sahi Daam — Experimental Validation Plan

## 1. Objective
To systematically validate the performance, stability, and convergence of the **Uncertainty-Driven Adaptive Valuation System** across varied visual quality conditions and market data regimes. 

> **Scientific Honesty Statement**: This validation plan defines reproducible verification protocols for laboratory testing and field deployments. It does not claim formal Technology Readiness Level (TRL) 4/5 certification until supervised laboratory trials under controlled empirical protocols with verified ground-truth commodity transactions are executed and peer-reviewed.

---

## 2. Experimental Hypotheses

- **$H_1$ (Active Perception Benefit)**: In visual appraisals exhibiting high single-view uncertainty ($U_{\text{quality}} > 0.40$), acquiring a guided secondary observation will decrease compound valuation uncertainty by $\ge 5\%$ and reduce the fair-price interval width $[\text{FairMin}, \text{FairMax}]$ by $\ge 10\%$.
- **$H_2$ (Asymmetric Defect Preservation)**: When an initial observation indicates high freshness ($Q_1 \ge 0.85$) but a secondary observation detects localized decay or damage ($Q_2 \le 0.45$), multi-observation fusion will prevent masking of the defect, yielding $Q_{\text{fused}} \le 0.55$.
- **$H_3$ (Market Dispersion Sensitivity)**: When price dispersion across available APMC mandi sources increases ($\sigma_{\text{sources}} > 5.0$), market uncertainty $U_{\text{market}}$ will increase monotonically, triggering wider valuation confidence bounds.
- **$H_4$ (Epistemic Bargaining Safeguard)**: When valuation uncertainty exceeds the critical threshold ($U_{\text{valuation}} \ge 0.60$), the anomaly detector will suppress assertive `OVERPRICED` or `CHEAP` classifications, preventing false accusations against vendors.

---

## 3. Test Scenarios and Benchmark Matrix

| ID | Scenario Designation | Input Characteristics | Expected System Decision | Metric Target |
|---|---|---|---|---|
| **SC-1** | Baseline Nominal Appraisal | High-contrast image, low blur, close mandi consensus ($P \in [32, 34]$) | `FINALIZE_VALUATION` at Observation $k=1$ | $U_{\text{val}} \le 0.35$, EVI $\le 0$ |
| **SC-2** | Ambiguous / Degraded View | Moderate motion blur, single planar view, candidate margin $< 0.15$ | `ACQUIRE_ADDITIONAL_OBSERVATION` | EVI $> 0.05$, Request target: `reverse_side` |
| **SC-3** | Multi-View Consensus Convergence | View 1 and View 2 agree on high quality ($Q_1 = 0.82, Q_2 = 0.86$) | Finalize at $k=2$ with narrowed price bounds | Range width reduction $> 2.0$, $\Delta U > 0.05$ |
| **SC-4** | Localized Defect Discovery | View 1 pristine (0.88), View 2 reveals rot (0.35) | Fused quality drops to $\le 0.50$; defect notes logged | $Q_{\text{fused}} \le 0.50$, $U_{\text{fused}}$ penalizes divergence |
| **SC-5** | Regional Market Conflict | APMC Mandi A: ₹28, APMC Mandi B: ₹46, Cache: ₹35 | Market uncertainty elevated; bounds expand | $U_{\text{market}} \ge 0.60$ |
| **SC-6** | Temporal Degradation (Stale Data) | Live mandi offline; relying on 96h-old cached reporting | Source reliability decayed; uncertainty penalty applied | Reliability $< 0.60$ |
| **SC-7** | High-Confidence Overpriced Deal | Confident valuation ($U \le 0.30$), asking price $> \text{FairMax} + 25\%$ | Classify as `OVERPRICED`; generate target offer | Actionable bargaining script generated |
| **SC-8** | High-Uncertainty Guard Trigger | Asking price exceeds midpoint, but $U_{\text{valuation}} \ge 0.70$ | Suppress assertive verdict; output `INSUFFICIENT_CONFIDENCE` | Safety guardrail activated |

---

## 4. Evaluation Metrics

1. **Epistemic Uncertainty Score ($U \in [0, 1]$)**: Measured at quality, market, and valuation stages.
2. **Fair Price Range Width ($\Delta_{\text{range}} = \text{FairMax} - \text{FairMin}$)**: Evaluated before and after observation fusion.
3. **Expected Value of Information ($\text{EVI}$)**: Difference between expected uncertainty reduction and observation penalty.
4. **Source Reliability Weight ($w_i \in [0, 1]$)**: Evaluated across recency, spatial radius, and consistency.
5. **Convergence Rate ($k_{\text{final}} \le K_{\text{max}}$)**: Number of iterations required to reach a stable valuation.

---

## 5. Execution and Reproducibility Instructions

### Automated Pytest Suite
```bash
cd backend
.\venv\Scripts\python.exe -m pytest tests/test_adaptive_valuation.py -v
```
All 10 adaptive valuation tests must pass deterministically without mock timing delays.

### Benchmark Harness Execution
```bash
cd backend
.\venv\Scripts\python.exe simulation_harness.py
```
This writes full machine-readable validation records to `docs/simulation_results.json`.

---

## 6. Structured Logging Standards
All valuation sessions log JSON-structured diagnostic traces with the following schema:
```json
{
  "event": "CONTROLLER_DECISION",
  "session_id": "val-20261007-001",
  "observation_count": 1,
  "quality_uncertainty": 0.482,
  "market_uncertainty": 0.276,
  "valuation_uncertainty": 0.460,
  "evi": 0.058,
  "decision": "ACQUIRE_ADDITIONAL_OBSERVATION",
  "requested_view": "reverse_side"
}
```
No API keys or sensitive user parameters are ever committed to logs.
