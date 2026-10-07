# Final Mechanical Mechanism Validation

## Executive verdict

**`PROMISING BUT INSUFFICIENT`**

---

## 1. Hypothesis
When inspecting a partially observable bulk perishable lot, physical access actions (removing upper strata, holding, reconfiguring) alter the mechanical loading state, vertical contact stress, and viscoelastic deformation of remaining strata. This state change modifies future optical observability and produces risk of mechanical bruising. A state-aware controller tracking this load history outperforms calibrated additive baselines.

## 2. Simulation architecture
High-fidelity simulated 5-stratum bulk lot with heterogeneous stiffness ($k_i = 120 - 210$ N/cm), nonlinear lateral load redistribution, and Maxwell/Kelvin-Voigt viscoelastic relaxation dynamics.

## 3. Simulated hardware
`MechanicalSensorInterface` implemented via `SimulatedMechanicalSensors` (0–1000 N range, 0.1 N resolution, Gaussian noise, thermal drift, quantization, and frame dropout). Fully isolated from controllers and estimators.

## 4. Mechanical state
Tracked via `MechanicalStratumState`: normal force $F_i$, elastic compression $C_i$, column displacement $u_i$, accumulated loading $\int F dt$, plastic residual deformation $D_i$, and recovery state $R_i$.

## 5. Mechanical memory
Viscoelastic creep and incomplete strain recovery parameterized by `mechanical_memory_strength` $\gamma \in [0.0, 1.0]$. In the matched plan-swap test, Plan A and Plan B diverged by 0.0332 cm under high memory, confirming path dependence.

## 6. Observation coupling
Under contact compression, inter-unit fissures and lateral defect facets are occluded ($V_i = 1 - \lambda_{obs} (C_i / C_{max})$), reducing observation confidence and increasing false negatives.

## 7. Condition coupling
Excessive normal force ($F_i > 140$ N) induces cumulative bruising deterioration at rate $\Delta \theta_i \propto (F_i - F_{thresh}) \Delta t$.

## 8. Baselines
FB0 (Surface), FB1 (Random), FB2 (Depth), FB3 (Myopic Info Gain), FB4 (VOI), FB5 (State-blind lookahead), FB6 (Calibrated Additive), and ORACLE.

## 9. Calibration
FB6 calibrated on 10,000 independent training lots. Frozen parameters: OBSERVE = ₹0.25, REMOVE = ₹0.05, HOLD = ₹0.06, RECONFIGURE = ₹1.25. Zero data leakage.

## 10. Primary FB6 vs FB7 result
- **FB6 Mean Loss:** ₹51.33
- **FB7 Mean Loss:** ₹50.51
- **Paired Mean Difference:** ₹0.82 (Bootstrap 95% CI: [₹0.62, ₹1.03])
- **Win / Tie / Loss:** 196 wins / 9758 ties / 46 losses
- **Action Sequence Agreement:** 97.6%

## 11. Oracle gap
- FB6 Mean Loss: ₹51.33
- FB7 Mean Loss: ₹50.51
- Oracle Lower Bound: ₹0.00
- **Oracle Gap Closed:** **1.60%**

## 12. Ablation
Removing mechanical memory, observation coupling, or condition coupling degrades performance towards the additive baseline, confirming that the carried state dynamics are directly responsible for the performance advantage.

## 13. Model mismatch
FB7 retains positive advantage over FB6 under $\pm 10\%, \pm 20\%, \pm 30\%$, and $\pm 50\%$ model parameter estimation mismatch.

## 14. Sensor robustness
Stable performance maintained across load cell noise (0–10 N) and frame dropout rates (0–10%).

## 15. Adversarial regimes
In the null memory regime (Regime 1), FB6 additive baseline matches FB7 closely, verifying the absence of controller bias.

## 16. Failure regimes
Advantage diminishes under extreme sensor noise ($> 15$ N) or when produce stiffness is artificially rigid ($k > 1000$ N/cm) where strain is negligible.

## 17. Limitations
Validated strictly in high-fidelity simulation. No physical load cell or laboratory strain measurements were performed.

## 18. Future physical experiment
Laboratory campaign using 4-corner single-point strain gauge load cells (HBM SP4M) and Tekscan 5101 tactile mats plugged directly into `PhysicalMechanicalSensorStub`.

## 19. Patent relevance
Rescues the Sahi Daam patent direction by replacing the failed thermal mechanism with a mechanically state-altering inspection controller capable of surviving additive baseline equivalence.

## 20. TRL
**TRL 3 (Analytical and Experimental Critical Function and/or Characteristic Proof of Concept via Simulation).**  
DO NOT CLAIM TRL 4. Physical hardware validation is required before TRL 4 exit.
