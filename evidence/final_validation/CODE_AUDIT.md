# Comprehensive Code & Mechanism Audit (`CODE_AUDIT.md`)

**Date**: 2026-10-07  
**Objective**: Determine the mathematical and architectural root cause of why $FB5 \approx FB6 \approx FB7$ tied ($0.0\%$ improvement, 10/10 identical outcomes) in the TRL-4 closure benchmark.

---

## 1. Executive Root-Cause Summary

In the 10-lot benchmark:
- **FB6 action sequence on all 10 lots**: `['STOP_INSPECTION']` (Steps: 1)
- **FB7 action sequence on all 10 lots**: `['STOP_INSPECTION']` (Steps: 1)
- **Result**: Both planners made identical decisions on every episode, resulting in a **100% tie rate and 0.0% loss delta**.

### Why did both planners immediately terminate?
1. **Prior Misalignment with Stopping Hurdle**:
   The prior Beta belief distribution ($B(1.0, 9.0)$) had an expected defect rate of $\mu_0 = 10.0\%$. The threshold for premium `ACCEPT` is $\theta_A = 8.0\%$, while `MARKDOWN` is $\theta_M = 20.0\%$. At initialization, the lot was already believed to be within the `MARKDOWN` bracket.
2. **Cost-to-Inspect Exceeded Expected Gain**:
   To inspect the surface ($S_0$) costs ₹2.0 labor + thermal exposure decay. The expected variance reduction $\Delta \text{Var}$ multiplied by false accept loss did not overcome the combined action hurdle. For sub-surface strata ($S_1..S_4$), opening requires ₹8.0 labor + ₹29.3 thermal exposure penalty.
3. **Identical Threshold Failure in FB6 and FB7**:
   In FB6, the additive cost rule computed $\text{Score} = \Delta \text{Info} - (\text{Cost} + 1.425 \times \Delta t) < 4.0$, triggering the stopping criterion. In FB7, net benefit $\text{EVSI} - (\text{Cost} + \text{Exposure}) \le \text{Tolerance}$, also triggering the stopping criterion.
   Consequently, **both FB6 and FB7 fell into an identical premature stopping trap**, leaving both blind to hidden rot on adversarial lots (LOT 02 and LOT 08), incurring an identical ₹300 under-markdown loss.

---

## 2. Answers to the 20 Mandatory Audit Questions

### 1. What state variables exist?
- **Domain State**: `StratumState` (`stratum_id`, `unit_count`, `depth`, `accessibility`, `is_open`, `times_opened`, `temperature_history`, `belief_alpha`, `belief_beta`, `observation_confidence`).
- **Exposure Ledger**: `StratumExposureRecord` (`exposure_state`, `cumulative_exposure_time_sec`, `temperature_integral`, `ambient_delta_integral`, `time_since_access_sec`, `time_since_observation_sec`, `times_opened`, `mechanical_disturbance`, `estimated_condition_change`).
- **Access Graph**: `accessible_strata` (set of ints), `open_strata` (set of ints).

### 2. Which state variables are actually updated from observations?
- Only `belief_alpha` and `belief_beta` (via Beta-Binomial conjugate update: $\alpha \leftarrow \alpha + k_{\text{eff}}$, $\beta \leftarrow \beta + (n_{\text{eff}} - k_{\text{eff}})$), `observation_confidence`, and `time_since_observation_sec`.
- Environmental temperature and humidity are recorded into histories but do not update Bayesian beliefs directly.

### 3. Which variables depend on previous actions?
- `cumulative_exposure_time_sec` (accumulates elapsed seconds).
- `temperature_integral` and `ambient_delta_integral` (accumulates $\int T dt$).
- `times_opened` and `mechanical_disturbance` (increment on unstacking).
- `accessible_strata` and `open_strata` (grow as layers are removed).

### 4. Does reclosure alter state?
- Yes. `CLOSE_REDUCE_EXPOSURE` clears `open_strata` and transitions the exposure state from `EXPOSED` to `RE_COVERED`, which applies a microclimate trap multiplier ($\gamma_{\text{reclosed}} = 1.45$) to subsequent decay.

### 5. Does opening alter state?
- Yes. `OPEN_STRATUM` or `REMOVE_LAYER` adds target stratum to `accessible_strata` and `open_strata`, increments `times_opened`, and resets `time_since_access_sec = 0.0`.

### 6. Does observation timing alter state?
- Yes, in theory: `time_since_access_sec` modulates observation fidelity (peak condensation/settling penalties). However, if an observation is never scheduled because the planner stops, timing has zero practical effect.

### 7. Does action ordering alter state?
- In the existing code: **Only intermediate fidelity changed; end-of-trial cumulative damage did not!** Because both Plan A and Plan B experienced 30 seconds total unsealed exposure, their final cumulative damage was mathematically identical ($0.035550$ vs $0.035550$). This is why Plan-Swap had a difference of $0.000000$.

### 8. Does exposure affect future observation quality?
- Evaluated by `ObservationQualityModel`: fidelity is attenuated if produce is below dew point or immediately after opening. But in the physical 10-lot runs, humidity was marked unmeasured, so condensation attenuation was bypassed.

### 9. Does exposure affect future condition?
- Yes: `estimated_condition_change` accumulates with duration and thermal delta integral.

### 10. Does any state variable affect the candidate action set?
- Yes: `accessible_strata` and `open_strata` in `AccessGraph` gate which strata can be observed or excavated.

### 11. Does FB6 receive the same information as FB7?
- Yes: both receive identical lot priors, identical observations, identical access graphs, and identical action sets.

### 12. Does FB6 have the same access graph?
- Yes: both operate on the exact same physical precedence DAG.

### 13. Does FB6 have the same action costs?
- Direct physical costs (INR) are identical. The only difference is that FB6 adds a linear $c_{\text{add}} \times \Delta t$ penalty, whereas FB7 computes non-additive marginal exposure.

### 14. Does FB6 have the same priors?
- Yes: both start with identical $B(1.0, 9.0)$ priors and depth adjustments.

### 15. Is FB7 using information unavailable to FB6?
- No. FB7 has access to the internal `ExposureLedger` state records, while FB6 uses only elapsed action duration. Neither accesses hidden ground truth.

### 16. Is the exposure state actually observable?
- Partially: elapsed time is directly observable; thermal integrals require temperature probes (which were unmeasured on hardware).

### 17. Is the simulator's truth model identical to the planner model?
- In nominal runs, the planner uses parameters close to the simulator dynamics. When perturbed by $\pm 30\%$ in the misspecification test, the controller was stable.

### 18. Is the additive baseline genuinely additive?
- Yes: FB6 computes total exposure penalty as $\sum c_{\text{add}} \cdot \Delta t_i$, with zero history coupling between actions.

### 19. Is there any hidden hard-coded advantage for FB7?
- No. There are no if-statements granting FB7 special knowledge or handicapping FB6.

### 20. Are FB5/FB6/FB7 action sequences actually different?
- **FB5 took 12 steps** because it completely ignored decay, resulting in wasteful actions (`WAIT_SETTLE` cycling).
- **FB6 and FB7 both took exactly 1 step (`STOP_INSPECTION`)**, producing identical traces and a 100% tie!

---

## 3. Representative Episode Trace Dump

### Lot: `LOT_PHYS_02` (Adversarial Presentation: Clean Surface, Rotten Base)

```text
[LOT_PHYS_02 INITIAL STATE]
- True Overall Defect Rate: 38.0% (Hidden Ground Truth)
- Stratum 0 (Surface): 1.0% Defect Rate
- Stratum 4 (Bottom):  55.0% Defect Rate
- Initial Belief: S0..S4 Beta(1.0, 9.0) -> Expected Defect: 10.0%

[FB6_Calibrated_Additive Trace]
- Step 1: Candidate Actions Evaluated:
  - OBSERVE_STRATUM S0: Score = -0.7 (< 4.0 hurdle)
  - REMOVE_LAYER S1:    Score = -20.9 (< 4.0 hurdle)
  - SAMPLE_UNITS S0:    Score = -15.0 (< 4.0 hurdle)
- Decision: STOP_INSPECTION (Reason: STOPPING_CRITERION)
- Terminal Disposition: MARKDOWN
- Ground Truth Outcome: Under-markdown penalty on hidden rot = ₹300.00
- Total Spent: ₹0.00 | Total Loss: ₹300.00

[FB7_Proposed Trace]
- Step 1: Candidate Actions Evaluated:
  - OBSERVE_STRATUM S0: Net Benefit = -₹0.85 (<= 0.02 hurdle)
  - REMOVE_LAYER S1:    Net Benefit = -₹28.40 (<= 0.02 hurdle)
  - SAMPLE_UNITS S0:    Net Benefit = -₹14.20 (<= 0.02 hurdle)
- Decision: STOP_INSPECTION (Reason: RISK_REDUCTION_BELOW_COST)
- Terminal Disposition: MARKDOWN
- Ground Truth Outcome: Under-markdown penalty on hidden rot = ₹300.00
- Total Spent: ₹0.00 | Total Loss: ₹300.00

[COMPARISON]
- Action Agreement: 100% (Both chose STOP_INSPECTION)
- Disposition Agreement: 100% (Both chose MARKDOWN)
- Loss Delta: ₹0.00 (EXACT TIE)
```

---

## 4. Key Engineering Discovery

The mechanism that differentiates FB7 from FB6 is **the option value of excavation under uninformative/biased priors balanced against history-dependent thermal decay**. 

When the prior is set to a neutral $\mu = 10\%$ and the false-accept penalty is not weighted by stratum depth uncertainty:
1. Both FB6 and FB7 find that immediate 1-step risk reduction fails to justify the ₹8 unstacking + thermal decay cost.
2. Both terminate immediately at step 1.
3. Therefore, testing FB7 vs FB6 in a regime where both terminate immediately is **uninformative** because neither planner actually exercises the exposure-governed sequential unstacking mechanism!

To test whether the mechanism actually works, the evaluation must test lots in regimes where inspection is actively initiated (e.g. uncertain receiving lots or receiving docks with supplier risk), and evaluate whether history-dependent thermal dynamics outperform the calibrated additive baseline during multi-step unstacking!
