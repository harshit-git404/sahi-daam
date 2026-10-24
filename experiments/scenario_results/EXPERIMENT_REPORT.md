# Sahi Daam — Controlled Pricing Experiment Lab Report
## Empirical Simulation Evidence, Mathematical Traces, and Integrity Verification

**Generated:** 2026-10-24 11:00:58 UTC  
**Algorithm Version:** `v2.0-locality-reconciled`  
**Fixture Version:** `1.0.0`  
**Total Executed Runs:** 26  

> **Technical Disclosure & Demonstration Notice:**  
> All scenarios documented in this report were executed using deterministic mock fixtures in an isolated environment. 
> These calculations demonstrate the reproducible behavior of the Sahi Daam cost-basis calculation, safe transport fallback, 
> anti-Sybil duplicate filtering, and bounded community reconciliation. Main database records and live market observations remain unaffected.

---

## 1. Executive Summary Table

| Scenario ID | Category | Transport | Sample ($N$) | Alpha ($lpha$) | Baseline Range | Reconciled Range | Status | Assertions |
|---|---|---|---|---|---|---|---|---|
| `transport_available` | Core Transport | available | 3 | 0.00 | ₹28.6–₹31.9 | ₹28.6–₹31.9 | `TRANSPORT_AWARE_BASELINE` | **PASS** |
| `transport_unavailable` | Core Transport | unavailable | 2 | 0.00 | ₹26.0–₹29.0 | ₹26.0–₹29.0 | `PROVISIONAL_WHOLESALE_BASELINE` | **PASS** |
| `community_low` | Community Reconciliation | available | 10 | 0.20 | ₹28.6–₹31.9 | ₹27.15–₹30.45 | `TRANSPORT_AWARE_RECONCILED` | **PASS** |
| `community_high` | Community Reconciliation | available | 10 | 0.20 | ₹28.6–₹31.9 | ₹29.55–₹32.85 | `TRANSPORT_AWARE_RECONCILED` | **PASS** |
| `insufficient_community` | Community Reconciliation | available | 9 | 0.00 | ₹28.6–₹31.9 | ₹28.6–₹31.9 | `TRANSPORT_AWARE_BASELINE` | **PASS** |
| `duplicate_reports` | Quality Controls | available | 8 | 0.00 | ₹28.6–₹31.9 | ₹28.6–₹31.9 | `TRANSPORT_AWARE_BASELINE` | **PASS** |
| `freshness_adjustment` | Produce Quality | available | 2 | 0.00 | ₹26.6–₹29.9 | ₹26.6–₹29.9 | `TRANSPORT_AWARE_BASELINE` | **PASS** |
| `combined_transport_community_low` | Combined Scenarios | available | 10 | 0.20 | ₹28.6–₹31.9 | ₹26.95–₹30.25 | `TRANSPORT_AWARE_RECONCILED` | **PASS** |
| `combined_transport_community_high` | Combined Scenarios | available | 10 | 0.20 | ₹28.6–₹31.9 | ₹29.75–₹33.05 | `TRANSPORT_AWARE_RECONCILED` | **PASS** |
| `combined_transport_unavail_community_sufficient` | Combined Scenarios | unavailable | 10 | 0.20 | ₹26.0–₹29.0 | ₹25.3–₹28.3 | `PROVISIONAL_WHOLESALE_RECONCILED` | **PASS** |
| `combined_high_community_with_duplicates` | Combined Scenarios | available | 8 | 0.00 | ₹28.6–₹31.9 | ₹28.6–₹31.9 | `TRANSPORT_AWARE_BASELINE` | **PASS** |
| `combined_missing_wholesale` | Safety Fallbacks | unavailable | 0 | 0.00 | Unavailable | — | `UNAVAILABLE` | **FAIL** |
| `combined_invalid_unit` | Quality Controls | available | 0 | 0.00 | ₹28.6–₹31.9 | ₹28.6–₹31.9 | `TRANSPORT_AWARE_BASELINE` | **PASS** |
| `transport_available` | Core Transport | available | 3 | 0.00 | ₹28.6–₹31.9 | ₹28.6–₹31.9 | `TRANSPORT_AWARE_BASELINE` | **PASS** |
| `transport_unavailable` | Core Transport | unavailable | 2 | 0.00 | ₹26.0–₹29.0 | ₹26.0–₹29.0 | `PROVISIONAL_WHOLESALE_BASELINE` | **PASS** |
| `community_low` | Community Reconciliation | available | 10 | 0.20 | ₹28.6–₹31.9 | ₹27.15–₹30.45 | `TRANSPORT_AWARE_RECONCILED` | **PASS** |
| `community_high` | Community Reconciliation | available | 10 | 0.20 | ₹28.6–₹31.9 | ₹29.55–₹32.85 | `TRANSPORT_AWARE_RECONCILED` | **PASS** |
| `insufficient_community` | Community Reconciliation | available | 9 | 0.00 | ₹28.6–₹31.9 | ₹28.6–₹31.9 | `TRANSPORT_AWARE_BASELINE` | **PASS** |
| `duplicate_reports` | Quality Controls | available | 8 | 0.00 | ₹28.6–₹31.9 | ₹28.6–₹31.9 | `TRANSPORT_AWARE_BASELINE` | **PASS** |
| `freshness_adjustment` | Produce Quality | available | 2 | 0.00 | ₹26.6–₹29.9 | ₹26.6–₹29.9 | `TRANSPORT_AWARE_BASELINE` | **PASS** |
| `combined_transport_community_low` | Combined Scenarios | available | 10 | 0.20 | ₹28.6–₹31.9 | ₹26.95–₹30.25 | `TRANSPORT_AWARE_RECONCILED` | **PASS** |
| `combined_transport_community_high` | Combined Scenarios | available | 10 | 0.20 | ₹28.6–₹31.9 | ₹29.75–₹33.05 | `TRANSPORT_AWARE_RECONCILED` | **PASS** |
| `combined_transport_unavail_community_sufficient` | Combined Scenarios | unavailable | 10 | 0.20 | ₹26.0–₹29.0 | ₹25.3–₹28.3 | `PROVISIONAL_WHOLESALE_RECONCILED` | **PASS** |
| `combined_high_community_with_duplicates` | Combined Scenarios | available | 8 | 0.00 | ₹28.6–₹31.9 | ₹28.6–₹31.9 | `TRANSPORT_AWARE_BASELINE` | **PASS** |
| `combined_missing_wholesale` | Safety Fallbacks | unavailable | 0 | 0.00 | Unavailable | — | `UNAVAILABLE` | **PASS** |
| `combined_invalid_unit` | Quality Controls | available | 0 | 0.00 | ₹28.6–₹31.9 | ₹28.6–₹31.9 | `TRANSPORT_AWARE_BASELINE` | **PASS** |

---

## 2. Detailed Scenario Evidence & Mathematical Traces

### Scenario A — Transport Available
- **Run ID:** `run_transport_available_7d8b057021`
- **JSON Evidence File:** [`transport_available/run_transport_available_7d8b057021.json`](transport_available/run_transport_available_7d8b057021.json)
- **SHA-256 Digest:** `b5934114e3ce5fb723c2853a11804fc3d292a3ea7ee4457c7f514f7abea37b78`
- **Description:** Demonstrates complete transport-aware cost calculation (wholesale ₹20 + transport ₹2 = cost basis ₹22/kg). Insufficient community data preserves baseline range.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction (Good Quality)) | ₹/kg | Quality Grading Model |
| Raw Submissions | 3 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 3 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹29.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction (Good Quality)).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction (Good Quality)).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=3, Duplicates=0, Eligible=3 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.00 (Weight Inactive)**
- *Explanation:* Sample requirement not satisfied (3 < 10 independent reports). Community weight α = 0.0; empirical median does not influence final price.

**Step 5: Preserve Baseline Reference (Reconciliation Inactive)**
- *Formula:* `Final Range = Baseline Range (α = 0.0)`
- *Substitution:* `Final Range = Baseline Range`
- *Result:* **Final Output Range = ₹28.60–₹31.90/kg**
- *Explanation:* Because α = 0.0, the pure cost-basis baseline range is preserved in full without distortion.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_BASELINE`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹28.6–₹31.9/kg (Midpoint: ₹30.25)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 3 eligible reports (sufficient=False) | 3 eligible reports (sufficient=False) | **PASS** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_BASELINE | TRANSPORT_AWARE_BASELINE | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Scenario B — Transport Unavailable (Provisional Fallback)
- **Run ID:** `run_transport_unavailable_76a3c8e7e1`
- **JSON Evidence File:** [`transport_unavailable/run_transport_unavailable_76a3c8e7e1.json`](transport_unavailable/run_transport_unavailable_76a3c8e7e1.json)
- **SHA-256 Digest:** `9d643e72a61fc67b9add90b3363ee129c9dd68201301f37103cb8cd308b02fc8`
- **Description:** Demonstrates safe provisional fallback when transport information is unconfigured or unavailable. Missing transport is never treated as zero.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹Unavailable | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 2 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 2 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹27.5 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Evaluate Transport & Determine Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price (Transport Unavailable)`
- *Substitution:* `₹20.00 + [Transport Unconfigured]`
- *Result:* **Provisional Cost Basis = ₹20.00/kg**
- *Explanation:* Transport cost is unavailable. Calculating provisional wholesale-based baseline (not a delivered-cost estimate).

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹20.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹26.00/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹20.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹29.00/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=2, Duplicates=0, Eligible=2 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.00 (Weight Inactive)**
- *Explanation:* Sample requirement not satisfied (2 < 10 independent reports). Community weight α = 0.0; empirical median does not influence final price.

**Step 5: Preserve Baseline Reference (Reconciliation Inactive)**
- *Formula:* `Final Range = Baseline Range (α = 0.0)`
- *Substitution:* `Final Range = Baseline Range`
- *Result:* **Final Output Range = ₹26.00–₹29.00/kg**
- *Explanation:* Because α = 0.0, the pure cost-basis baseline range is preserved in full without distortion.

#### Actual Computed Output
- **Calculation Status:** `PROVISIONAL_WHOLESALE_BASELINE`
- **Baseline Fair Range:** ₹26.0–₹29.0/kg
- **Reconciled Fair Range:** ₹26.0–₹29.0/kg (Midpoint: ₹27.5)
- **Transport Status:** `unavailable`
- **Provisional Indicator:** `True`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | unavailable | unavailable | **PASS** |
| Sample Sufficiency | 2 eligible reports (sufficient=False) | 2 eligible reports (sufficient=False) | **PASS** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | PROVISIONAL_WHOLESALE_BASELINE | PROVISIONAL_WHOLESALE_BASELINE | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=26.0, max=29.0 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Scenario C — Community Prices Lower Than Baseline
- **Run ID:** `run_community_low_aa21bfe853`
- **JSON Evidence File:** [`community_low/run_community_low_aa21bfe853.json`](community_low/run_community_low_aa21bfe853.json)
- **SHA-256 Digest:** `1244a55406b5c6b9bfdb4cc65d3e1fd6f1ec4ac73cf7999242f90147e0f35550`
- **Description:** Demonstrates reconciliation when at least 10 valid independent reports indicate lower retail prices (median ₹23/kg vs baseline midpoint ~₹30.25).

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 10 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 10 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹23.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.20 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=10, Duplicates=0, Eligible=10 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.20 (Weight Active)**
- *Explanation:* Sample requirement satisfied (10 >= 10 independent reports). Community median is ₹23.00/kg.

**Step 5: Apply Adaptive Range Reconciliation**
- *Formula:* `Reconciled Reference = (1 - α) × Baseline Reference + α × Community Median`
- *Substitution:* `(1 - 0.20) × ₹30.25 + 0.20 × ₹23.00`
- *Result:* **Reconciled Reference = ₹28.80/kg (Range: ₹27.15–₹30.45)**
- *Explanation:* Cost-basis baseline midpoint (₹30.25) reconciled with crowd reports (₹23.00) using α=0.20.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_RECONCILED`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹27.15–₹30.45/kg (Midpoint: ₹28.8)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 10 eligible reports (sufficient=True) | 10 eligible reports (sufficient=True) | **PASS** |
| Reconciliation Weight (α) | α between 0.20 and 0.20 | α = 0.20 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_RECONCILED | TRANSPORT_AWARE_RECONCILED | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Scenario D — Community Prices Higher Than Baseline
- **Run ID:** `run_community_high_580773540d`
- **JSON Evidence File:** [`community_high/run_community_high_580773540d.json`](community_high/run_community_high_580773540d.json)
- **SHA-256 Digest:** `296083a65f1ac50304d44cdc88e3f5e853b4c79b05ed8df66e9f746c3815a87e`
- **Description:** Demonstrates reconciliation when community reports indicate market premiums (median ₹35/kg). Reconciled reference moves toward community estimate while preserving baseline.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 10 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 10 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹35.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.20 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=10, Duplicates=0, Eligible=10 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.20 (Weight Active)**
- *Explanation:* Sample requirement satisfied (10 >= 10 independent reports). Community median is ₹35.00/kg.

**Step 5: Apply Adaptive Range Reconciliation**
- *Formula:* `Reconciled Reference = (1 - α) × Baseline Reference + α × Community Median`
- *Substitution:* `(1 - 0.20) × ₹30.25 + 0.20 × ₹35.00`
- *Result:* **Reconciled Reference = ₹31.20/kg (Range: ₹29.55–₹32.85)**
- *Explanation:* Cost-basis baseline midpoint (₹30.25) reconciled with crowd reports (₹35.00) using α=0.20.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_RECONCILED`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹29.55–₹32.85/kg (Midpoint: ₹31.2)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 10 eligible reports (sufficient=True) | 10 eligible reports (sufficient=True) | **PASS** |
| Reconciliation Weight (α) | α between 0.20 and 0.20 | α = 0.20 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_RECONCILED | TRANSPORT_AWARE_RECONCILED | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Scenario E — Insufficient Community Sample (Threshold Gate)
- **Run ID:** `run_insufficient_community_9b5d93faa1`
- **JSON Evidence File:** [`insufficient_community/run_insufficient_community_9b5d93faa1.json`](insufficient_community/run_insufficient_community_9b5d93faa1.json)
- **SHA-256 Digest:** `897c231909714df647749ef742fdc92f2d0fed1b88a833c63ae8bfefbd6f8519`
- **Description:** Demonstrates that a small community sample (9 reports) cannot override the baseline. Weight alpha = 0.0, baseline range is preserved in full.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 9 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 9 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹24.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=9, Duplicates=0, Eligible=9 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.00 (Weight Inactive)**
- *Explanation:* Sample requirement not satisfied (9 < 10 independent reports). Community weight α = 0.0; empirical median does not influence final price.

**Step 5: Preserve Baseline Reference (Reconciliation Inactive)**
- *Formula:* `Final Range = Baseline Range (α = 0.0)`
- *Substitution:* `Final Range = Baseline Range`
- *Result:* **Final Output Range = ₹28.60–₹31.90/kg**
- *Explanation:* Because α = 0.0, the pure cost-basis baseline range is preserved in full without distortion.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_BASELINE`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹28.6–₹31.9/kg (Midpoint: ₹30.25)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 9 eligible reports (sufficient=False) | 9 eligible reports (sufficient=False) | **PASS** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_BASELINE | TRANSPORT_AWARE_BASELINE | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Scenario F — Duplicate Community Reports (Anti-Sybil Filtering)
- **Run ID:** `run_duplicate_reports_f43e8c6678`
- **JSON Evidence File:** [`duplicate_reports/run_duplicate_reports_f43e8c6678.json`](duplicate_reports/run_duplicate_reports_f43e8c6678.json)
- **SHA-256 Digest:** `a36957ca4de3a458a0aa9ecd8ba5123afbfec214b142e9be359de96261f5e72e`
- **Description:** Demonstrates that flagged duplicate submissions are excluded from the independent sample count. 13 raw submissions yield only 8 independent reports, keeping alpha = 0.0.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 13 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 8 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹25.5 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=13, Duplicates=5, Eligible=8 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.00 (Weight Inactive)**
- *Explanation:* Sample requirement not satisfied (8 < 10 independent reports). Community weight α = 0.0; empirical median does not influence final price.

**Step 5: Preserve Baseline Reference (Reconciliation Inactive)**
- *Formula:* `Final Range = Baseline Range (α = 0.0)`
- *Substitution:* `Final Range = Baseline Range`
- *Result:* **Final Output Range = ₹28.60–₹31.90/kg**
- *Explanation:* Because α = 0.0, the pure cost-basis baseline range is preserved in full without distortion.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_BASELINE`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹28.6–₹31.9/kg (Midpoint: ₹30.25)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 8 eligible reports (sufficient=False) | 8 eligible reports (sufficient=False) | **PASS** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_BASELINE | TRANSPORT_AWARE_BASELINE | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Scenario G — Freshness Adjustment (Fair Quality Deduction)
- **Run ID:** `run_freshness_adjustment_e6204b5a8b`
- **JSON Evidence File:** [`freshness_adjustment/run_freshness_adjustment_e6204b5a8b.json`](freshness_adjustment/run_freshness_adjustment_e6204b5a8b.json)
- **SHA-256 Digest:** `6fed4962816c3c1042d84b737bc5f4367e598e6e4c55e14f8497d5b22f70fd88`
- **Description:** Demonstrates the effect of produce quality on retail range. Sub-run G1 evaluates fresh produce (₹0 deduction), while G2 applies a ₹-2.00/kg freshness deduction.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | -2 (Fair freshness deduction of ₹-2.00/kg) | ₹/kg | Quality Grading Model |
| Raw Submissions | 2 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 2 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹28.5 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (-2)`
- *Result:* **Baseline Minimum = ₹26.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (Fair freshness deduction of ₹-2.00/kg).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (-2)`
- *Result:* **Baseline Maximum = ₹29.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (Fair freshness deduction of ₹-2.00/kg).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=2, Duplicates=0, Eligible=2 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.00 (Weight Inactive)**
- *Explanation:* Sample requirement not satisfied (2 < 10 independent reports). Community weight α = 0.0; empirical median does not influence final price.

**Step 5: Preserve Baseline Reference (Reconciliation Inactive)**
- *Formula:* `Final Range = Baseline Range (α = 0.0)`
- *Substitution:* `Final Range = Baseline Range`
- *Result:* **Final Output Range = ₹26.60–₹29.90/kg**
- *Explanation:* Because α = 0.0, the pure cost-basis baseline range is preserved in full without distortion.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_BASELINE`
- **Baseline Fair Range:** ₹26.6–₹29.9/kg
- **Reconciled Fair Range:** ₹26.6–₹29.9/kg (Midpoint: ₹28.25)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 2 eligible reports (sufficient=False) | 2 eligible reports (sufficient=False) | **PASS** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_BASELINE | TRANSPORT_AWARE_BASELINE | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=26.6, max=29.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

#### Sub-Run Comparison Matrix
| Sub-Run | Quality Condition | Deduction | Baseline Range | Difference from Fresh |
|---|---|---|---|---|
| G1: Fresh / Good Quality (0 deduction) | No freshness deduction | +0 ₹/kg | ₹28.6–₹31.9/kg | +0.00 ₹/kg |
| G2: Lower / Fair Freshness (-₹2/kg deduction) | ₹-2.00/kg freshness deduction | -2 ₹/kg | ₹26.6–₹29.9/kg | -2.00 ₹/kg |

---

### Combined 1 — Transport Available + Low Community Median
- **Run ID:** `run_combined_transport_community_low_3928ee5c76`
- **JSON Evidence File:** [`combined_transport_community_low/run_combined_transport_community_low_3928ee5c76.json`](combined_transport_community_low/run_combined_transport_community_low_3928ee5c76.json)
- **SHA-256 Digest:** `866fd22486906fd57797d093c39c9c63b5e34a115e9b60ab22cfae33daa73e0b`
- **Description:** Complete transport cost (₹2/kg) combined with 10 eligible community reports having a low median of ₹22/kg.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 10 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 10 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹22.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.20 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=10, Duplicates=0, Eligible=10 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.20 (Weight Active)**
- *Explanation:* Sample requirement satisfied (10 >= 10 independent reports). Community median is ₹22.00/kg.

**Step 5: Apply Adaptive Range Reconciliation**
- *Formula:* `Reconciled Reference = (1 - α) × Baseline Reference + α × Community Median`
- *Substitution:* `(1 - 0.20) × ₹30.25 + 0.20 × ₹22.00`
- *Result:* **Reconciled Reference = ₹28.60/kg (Range: ₹26.95–₹30.25)**
- *Explanation:* Cost-basis baseline midpoint (₹30.25) reconciled with crowd reports (₹22.00) using α=0.20.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_RECONCILED`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹26.95–₹30.25/kg (Midpoint: ₹28.6)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 10 eligible reports (sufficient=True) | 10 eligible reports (sufficient=True) | **PASS** |
| Reconciliation Weight (α) | α between 0.20 and 0.20 | α = 0.20 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_RECONCILED | TRANSPORT_AWARE_RECONCILED | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Combined 2 — Transport Available + High Community Median
- **Run ID:** `run_combined_transport_community_high_7cbefe1d48`
- **JSON Evidence File:** [`combined_transport_community_high/run_combined_transport_community_high_7cbefe1d48.json`](combined_transport_community_high/run_combined_transport_community_high_7cbefe1d48.json)
- **SHA-256 Digest:** `909e6a09f6dc1f37ec1978dcc26d560f80deebeea752c9d09be95fd4665da355`
- **Description:** Transport cost (₹2/kg) combined with 10 community reports showing high retail prices (median ₹36/kg).

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 10 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 10 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹36.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.20 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=10, Duplicates=0, Eligible=10 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.20 (Weight Active)**
- *Explanation:* Sample requirement satisfied (10 >= 10 independent reports). Community median is ₹36.00/kg.

**Step 5: Apply Adaptive Range Reconciliation**
- *Formula:* `Reconciled Reference = (1 - α) × Baseline Reference + α × Community Median`
- *Substitution:* `(1 - 0.20) × ₹30.25 + 0.20 × ₹36.00`
- *Result:* **Reconciled Reference = ₹31.40/kg (Range: ₹29.75–₹33.05)**
- *Explanation:* Cost-basis baseline midpoint (₹30.25) reconciled with crowd reports (₹36.00) using α=0.20.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_RECONCILED`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹29.75–₹33.05/kg (Midpoint: ₹31.4)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 10 eligible reports (sufficient=True) | 10 eligible reports (sufficient=True) | **PASS** |
| Reconciliation Weight (α) | α between 0.20 and 0.20 | α = 0.20 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_RECONCILED | TRANSPORT_AWARE_RECONCILED | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Combined 3 — Transport Unavailable + Sufficient Community Reports
- **Run ID:** `run_combined_transport_unavail_community_sufficient_719fd10678`
- **JSON Evidence File:** [`combined_transport_unavail_community_sufficient/run_combined_transport_unavail_community_sufficient_719fd10678.json`](combined_transport_unavail_community_sufficient/run_combined_transport_unavail_community_sufficient_719fd10678.json)
- **SHA-256 Digest:** `5b768b10b25ab9bd7bceeb55127830d13a24583fcc1b594f2708a4dcd999f39c`
- **Description:** Demonstrates that community reconciliation can still adjust a provisional wholesale baseline when transport is missing.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹Unavailable | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 10 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 10 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹24.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.20 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Evaluate Transport & Determine Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price (Transport Unavailable)`
- *Substitution:* `₹20.00 + [Transport Unconfigured]`
- *Result:* **Provisional Cost Basis = ₹20.00/kg**
- *Explanation:* Transport cost is unavailable. Calculating provisional wholesale-based baseline (not a delivered-cost estimate).

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹20.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹26.00/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹20.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹29.00/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=10, Duplicates=0, Eligible=10 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.20 (Weight Active)**
- *Explanation:* Sample requirement satisfied (10 >= 10 independent reports). Community median is ₹24.00/kg.

**Step 5: Apply Adaptive Range Reconciliation**
- *Formula:* `Reconciled Reference = (1 - α) × Baseline Reference + α × Community Median`
- *Substitution:* `(1 - 0.20) × ₹27.50 + 0.20 × ₹24.00`
- *Result:* **Reconciled Reference = ₹26.80/kg (Range: ₹25.30–₹28.30)**
- *Explanation:* Cost-basis baseline midpoint (₹27.50) reconciled with crowd reports (₹24.00) using α=0.20.

#### Actual Computed Output
- **Calculation Status:** `PROVISIONAL_WHOLESALE_RECONCILED`
- **Baseline Fair Range:** ₹26.0–₹29.0/kg
- **Reconciled Fair Range:** ₹25.3–₹28.3/kg (Midpoint: ₹26.8)
- **Transport Status:** `unavailable`
- **Provisional Indicator:** `True`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | unavailable | unavailable | **PASS** |
| Sample Sufficiency | 10 eligible reports (sufficient=True) | 10 eligible reports (sufficient=True) | **PASS** |
| Reconciliation Weight (α) | α between 0.20 and 0.20 | α = 0.20 | **PASS** |
| Calculation Status | PROVISIONAL_WHOLESALE_RECONCILED | PROVISIONAL_WHOLESALE_RECONCILED | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=26.0, max=29.0 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Combined 4 — High Community Prices with Flagged Duplicates
- **Run ID:** `run_combined_high_community_with_duplicates_e82ce62c45`
- **JSON Evidence File:** [`combined_high_community_with_duplicates/run_combined_high_community_with_duplicates_e82ce62c45.json`](combined_high_community_with_duplicates/run_combined_high_community_with_duplicates_e82ce62c45.json)
- **SHA-256 Digest:** `1287ad0d75a8f6099d68bd9af2eb01d550b0857e67c0c5652e288c5fc4257c7f`
- **Description:** 14 high-price reports (median ₹36), but 6 flagged as duplicates -> only 8 independent reports remain, correctly preventing weight activation.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 14 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 8 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹37.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=14, Duplicates=6, Eligible=8 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.00 (Weight Inactive)**
- *Explanation:* Sample requirement not satisfied (8 < 10 independent reports). Community weight α = 0.0; empirical median does not influence final price.

**Step 5: Preserve Baseline Reference (Reconciliation Inactive)**
- *Formula:* `Final Range = Baseline Range (α = 0.0)`
- *Substitution:* `Final Range = Baseline Range`
- *Result:* **Final Output Range = ₹28.60–₹31.90/kg**
- *Explanation:* Because α = 0.0, the pure cost-basis baseline range is preserved in full without distortion.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_BASELINE`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹28.6–₹31.9/kg (Midpoint: ₹30.25)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 8 eligible reports (sufficient=False) | 8 eligible reports (sufficient=False) | **PASS** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_BASELINE | TRANSPORT_AWARE_BASELINE | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Combined 5 — Missing Wholesale Price (No Fabrication)
- **Run ID:** `run_combined_missing_wholesale_b5d474005a`
- **JSON Evidence File:** [`combined_missing_wholesale/run_combined_missing_wholesale_b5d474005a.json`](combined_missing_wholesale/run_combined_missing_wholesale_b5d474005a.json)
- **SHA-256 Digest:** `7ad7c6ac45deea212f3f48c8cf0b74021f91a3258c9c0017f8b07eab2064caaf`
- **Description:** Wholesale market price is missing or null. The system must refuse to fabricate a fair price and report status UNAVAILABLE.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹Unavailable | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 1 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 0 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹Unavailable | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Evaluate Wholesale Input**
- *Formula:* `Cost Basis = Wholesale Price (Wholesale Required)`
- *Substitution:* `Wholesale Price = Unavailable`
- *Result:* **Cost Basis = Unavailable**
- *Explanation:* No valid wholesale observation exists. Pricing engine refuses to fabricate a price.

#### Actual Computed Output
- **Calculation Status:** `UNAVAILABLE`
- **Baseline Fair Range:** Unavailable
- **Reconciled Fair Range:** None
- **Transport Status:** `unavailable`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | unavailable | **FAIL** |
| Sample Sufficiency | 1 eligible reports (sufficient=False) | 0 eligible reports (sufficient=False) | **FAIL** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | UNAVAILABLE | UNAVAILABLE | **PASS** |
| Baseline Ordering & Validity | Unavailable (missing wholesale) | None | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Combined 6 — Unsupported Unit (Non-Weight Units Filtered)
- **Run ID:** `run_combined_invalid_unit_84a31cb718`
- **JSON Evidence File:** [`combined_invalid_unit/run_combined_invalid_unit_84a31cb718.json`](combined_invalid_unit/run_combined_invalid_unit_84a31cb718.json)
- **SHA-256 Digest:** `ccfd19aeb5ca16cfb8efa607099afa564f09fca968664b7bb67f37198401d4f6`
- **Description:** Community submissions quoted per 'bunch' or 'piece' without weight conversion data are excluded from ₹/kg normalization.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 3 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 0 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹Unavailable | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=3, Duplicates=0, Eligible=0 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.00 (Weight Inactive)**
- *Explanation:* Sample requirement not satisfied (0 < 10 independent reports). Community weight α = 0.0; empirical median does not influence final price.

**Step 5: Preserve Baseline Reference (Reconciliation Inactive)**
- *Formula:* `Final Range = Baseline Range (α = 0.0)`
- *Substitution:* `Final Range = Baseline Range`
- *Result:* **Final Output Range = ₹28.60–₹31.90/kg**
- *Explanation:* Because α = 0.0, the pure cost-basis baseline range is preserved in full without distortion.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_BASELINE`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹28.6–₹31.9/kg (Midpoint: ₹30.25)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 0 eligible reports (sufficient=False) | 0 eligible reports (sufficient=False) | **PASS** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_BASELINE | TRANSPORT_AWARE_BASELINE | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Scenario A — Transport Available
- **Run ID:** `run_transport_available_9da8849ebe`
- **JSON Evidence File:** [`transport_available/run_transport_available_9da8849ebe.json`](transport_available/run_transport_available_9da8849ebe.json)
- **SHA-256 Digest:** `334b46b16f8a24ebea5645355151ee9d58d7b40fb1105b3a6d05bc94ca58f73e`
- **Description:** Demonstrates complete transport-aware cost calculation (wholesale ₹20 + transport ₹2 = cost basis ₹22/kg). Insufficient community data preserves baseline range.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction (Good Quality)) | ₹/kg | Quality Grading Model |
| Raw Submissions | 3 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 3 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹29.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction (Good Quality)).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction (Good Quality)).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=3, Duplicates=0, Eligible=3 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.00 (Weight Inactive)**
- *Explanation:* Sample requirement not satisfied (3 < 10 independent reports). Community weight α = 0.0; empirical median does not influence final price.

**Step 5: Preserve Baseline Reference (Reconciliation Inactive)**
- *Formula:* `Final Range = Baseline Range (α = 0.0)`
- *Substitution:* `Final Range = Baseline Range`
- *Result:* **Final Output Range = ₹28.60–₹31.90/kg**
- *Explanation:* Because α = 0.0, the pure cost-basis baseline range is preserved in full without distortion.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_BASELINE`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹28.6–₹31.9/kg (Midpoint: ₹30.25)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 3 eligible reports (sufficient=False) | 3 eligible reports (sufficient=False) | **PASS** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_BASELINE | TRANSPORT_AWARE_BASELINE | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Scenario B — Transport Unavailable (Provisional Fallback)
- **Run ID:** `run_transport_unavailable_380853861f`
- **JSON Evidence File:** [`transport_unavailable/run_transport_unavailable_380853861f.json`](transport_unavailable/run_transport_unavailable_380853861f.json)
- **SHA-256 Digest:** `1c9fc7d8e92bf3f16e498401f09b0d79021b545beda18930baf7fb3d700fd23e`
- **Description:** Demonstrates safe provisional fallback when transport information is unconfigured or unavailable. Missing transport is never treated as zero.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹Unavailable | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 2 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 2 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹27.5 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Evaluate Transport & Determine Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price (Transport Unavailable)`
- *Substitution:* `₹20.00 + [Transport Unconfigured]`
- *Result:* **Provisional Cost Basis = ₹20.00/kg**
- *Explanation:* Transport cost is unavailable. Calculating provisional wholesale-based baseline (not a delivered-cost estimate).

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹20.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹26.00/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹20.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹29.00/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=2, Duplicates=0, Eligible=2 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.00 (Weight Inactive)**
- *Explanation:* Sample requirement not satisfied (2 < 10 independent reports). Community weight α = 0.0; empirical median does not influence final price.

**Step 5: Preserve Baseline Reference (Reconciliation Inactive)**
- *Formula:* `Final Range = Baseline Range (α = 0.0)`
- *Substitution:* `Final Range = Baseline Range`
- *Result:* **Final Output Range = ₹26.00–₹29.00/kg**
- *Explanation:* Because α = 0.0, the pure cost-basis baseline range is preserved in full without distortion.

#### Actual Computed Output
- **Calculation Status:** `PROVISIONAL_WHOLESALE_BASELINE`
- **Baseline Fair Range:** ₹26.0–₹29.0/kg
- **Reconciled Fair Range:** ₹26.0–₹29.0/kg (Midpoint: ₹27.5)
- **Transport Status:** `unavailable`
- **Provisional Indicator:** `True`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | unavailable | unavailable | **PASS** |
| Sample Sufficiency | 2 eligible reports (sufficient=False) | 2 eligible reports (sufficient=False) | **PASS** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | PROVISIONAL_WHOLESALE_BASELINE | PROVISIONAL_WHOLESALE_BASELINE | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=26.0, max=29.0 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Scenario C — Community Prices Lower Than Baseline
- **Run ID:** `run_community_low_da4f27541a`
- **JSON Evidence File:** [`community_low/run_community_low_da4f27541a.json`](community_low/run_community_low_da4f27541a.json)
- **SHA-256 Digest:** `136725004ca9dc9be7a5ae9f607f8e4611dccf5bb7158c1344adc56cdea63d29`
- **Description:** Demonstrates reconciliation when at least 10 valid independent reports indicate lower retail prices (median ₹23/kg vs baseline midpoint ~₹30.25).

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 10 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 10 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹23.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.20 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=10, Duplicates=0, Eligible=10 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.20 (Weight Active)**
- *Explanation:* Sample requirement satisfied (10 >= 10 independent reports). Community median is ₹23.00/kg.

**Step 5: Apply Adaptive Range Reconciliation**
- *Formula:* `Reconciled Reference = (1 - α) × Baseline Reference + α × Community Median`
- *Substitution:* `(1 - 0.20) × ₹30.25 + 0.20 × ₹23.00`
- *Result:* **Reconciled Reference = ₹28.80/kg (Range: ₹27.15–₹30.45)**
- *Explanation:* Cost-basis baseline midpoint (₹30.25) reconciled with crowd reports (₹23.00) using α=0.20.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_RECONCILED`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹27.15–₹30.45/kg (Midpoint: ₹28.8)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 10 eligible reports (sufficient=True) | 10 eligible reports (sufficient=True) | **PASS** |
| Reconciliation Weight (α) | α between 0.20 and 0.20 | α = 0.20 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_RECONCILED | TRANSPORT_AWARE_RECONCILED | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Scenario D — Community Prices Higher Than Baseline
- **Run ID:** `run_community_high_b2cd05f725`
- **JSON Evidence File:** [`community_high/run_community_high_b2cd05f725.json`](community_high/run_community_high_b2cd05f725.json)
- **SHA-256 Digest:** `9859595868a5b009b4b1764a3720a5006bed78c372d6bbe3361fb6feaffd4635`
- **Description:** Demonstrates reconciliation when community reports indicate market premiums (median ₹35/kg). Reconciled reference moves toward community estimate while preserving baseline.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 10 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 10 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹35.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.20 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=10, Duplicates=0, Eligible=10 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.20 (Weight Active)**
- *Explanation:* Sample requirement satisfied (10 >= 10 independent reports). Community median is ₹35.00/kg.

**Step 5: Apply Adaptive Range Reconciliation**
- *Formula:* `Reconciled Reference = (1 - α) × Baseline Reference + α × Community Median`
- *Substitution:* `(1 - 0.20) × ₹30.25 + 0.20 × ₹35.00`
- *Result:* **Reconciled Reference = ₹31.20/kg (Range: ₹29.55–₹32.85)**
- *Explanation:* Cost-basis baseline midpoint (₹30.25) reconciled with crowd reports (₹35.00) using α=0.20.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_RECONCILED`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹29.55–₹32.85/kg (Midpoint: ₹31.2)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 10 eligible reports (sufficient=True) | 10 eligible reports (sufficient=True) | **PASS** |
| Reconciliation Weight (α) | α between 0.20 and 0.20 | α = 0.20 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_RECONCILED | TRANSPORT_AWARE_RECONCILED | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Scenario E — Insufficient Community Sample (Threshold Gate)
- **Run ID:** `run_insufficient_community_1560c560d7`
- **JSON Evidence File:** [`insufficient_community/run_insufficient_community_1560c560d7.json`](insufficient_community/run_insufficient_community_1560c560d7.json)
- **SHA-256 Digest:** `ea61aab564158f57da1484c742d4e6ef03e718973a4cc4dfee4509f80846bcf1`
- **Description:** Demonstrates that a small community sample (9 reports) cannot override the baseline. Weight alpha = 0.0, baseline range is preserved in full.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 9 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 9 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹24.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=9, Duplicates=0, Eligible=9 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.00 (Weight Inactive)**
- *Explanation:* Sample requirement not satisfied (9 < 10 independent reports). Community weight α = 0.0; empirical median does not influence final price.

**Step 5: Preserve Baseline Reference (Reconciliation Inactive)**
- *Formula:* `Final Range = Baseline Range (α = 0.0)`
- *Substitution:* `Final Range = Baseline Range`
- *Result:* **Final Output Range = ₹28.60–₹31.90/kg**
- *Explanation:* Because α = 0.0, the pure cost-basis baseline range is preserved in full without distortion.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_BASELINE`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹28.6–₹31.9/kg (Midpoint: ₹30.25)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 9 eligible reports (sufficient=False) | 9 eligible reports (sufficient=False) | **PASS** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_BASELINE | TRANSPORT_AWARE_BASELINE | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Scenario F — Duplicate Community Reports (Anti-Sybil Filtering)
- **Run ID:** `run_duplicate_reports_1f46fba2ff`
- **JSON Evidence File:** [`duplicate_reports/run_duplicate_reports_1f46fba2ff.json`](duplicate_reports/run_duplicate_reports_1f46fba2ff.json)
- **SHA-256 Digest:** `7b4e4bc617da7bf217b341c51eca86cda0489c107d8acb382b6f2056dd78c2b7`
- **Description:** Demonstrates that flagged duplicate submissions are excluded from the independent sample count. 13 raw submissions yield only 8 independent reports, keeping alpha = 0.0.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 13 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 8 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹25.5 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=13, Duplicates=5, Eligible=8 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.00 (Weight Inactive)**
- *Explanation:* Sample requirement not satisfied (8 < 10 independent reports). Community weight α = 0.0; empirical median does not influence final price.

**Step 5: Preserve Baseline Reference (Reconciliation Inactive)**
- *Formula:* `Final Range = Baseline Range (α = 0.0)`
- *Substitution:* `Final Range = Baseline Range`
- *Result:* **Final Output Range = ₹28.60–₹31.90/kg**
- *Explanation:* Because α = 0.0, the pure cost-basis baseline range is preserved in full without distortion.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_BASELINE`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹28.6–₹31.9/kg (Midpoint: ₹30.25)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 8 eligible reports (sufficient=False) | 8 eligible reports (sufficient=False) | **PASS** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_BASELINE | TRANSPORT_AWARE_BASELINE | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Scenario G — Freshness Adjustment (Fair Quality Deduction)
- **Run ID:** `run_freshness_adjustment_e07b351463`
- **JSON Evidence File:** [`freshness_adjustment/run_freshness_adjustment_e07b351463.json`](freshness_adjustment/run_freshness_adjustment_e07b351463.json)
- **SHA-256 Digest:** `7ac0f37e354f236f0ba27240e7d87d7e65e60b05882643e838c52509266b7f72`
- **Description:** Demonstrates the effect of produce quality on retail range. Sub-run G1 evaluates fresh produce (₹0 deduction), while G2 applies a ₹-2.00/kg freshness deduction.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | -2 (Fair freshness deduction of ₹-2.00/kg) | ₹/kg | Quality Grading Model |
| Raw Submissions | 2 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 2 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹28.5 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (-2)`
- *Result:* **Baseline Minimum = ₹26.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (Fair freshness deduction of ₹-2.00/kg).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (-2)`
- *Result:* **Baseline Maximum = ₹29.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (Fair freshness deduction of ₹-2.00/kg).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=2, Duplicates=0, Eligible=2 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.00 (Weight Inactive)**
- *Explanation:* Sample requirement not satisfied (2 < 10 independent reports). Community weight α = 0.0; empirical median does not influence final price.

**Step 5: Preserve Baseline Reference (Reconciliation Inactive)**
- *Formula:* `Final Range = Baseline Range (α = 0.0)`
- *Substitution:* `Final Range = Baseline Range`
- *Result:* **Final Output Range = ₹26.60–₹29.90/kg**
- *Explanation:* Because α = 0.0, the pure cost-basis baseline range is preserved in full without distortion.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_BASELINE`
- **Baseline Fair Range:** ₹26.6–₹29.9/kg
- **Reconciled Fair Range:** ₹26.6–₹29.9/kg (Midpoint: ₹28.25)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 2 eligible reports (sufficient=False) | 2 eligible reports (sufficient=False) | **PASS** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_BASELINE | TRANSPORT_AWARE_BASELINE | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=26.6, max=29.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

#### Sub-Run Comparison Matrix
| Sub-Run | Quality Condition | Deduction | Baseline Range | Difference from Fresh |
|---|---|---|---|---|
| G1: Fresh / Good Quality (0 deduction) | No freshness deduction | +0 ₹/kg | ₹28.6–₹31.9/kg | +0.00 ₹/kg |
| G2: Lower / Fair Freshness (-₹2/kg deduction) | ₹-2.00/kg freshness deduction | -2 ₹/kg | ₹26.6–₹29.9/kg | -2.00 ₹/kg |

---

### Combined 1 — Transport Available + Low Community Median
- **Run ID:** `run_combined_transport_community_low_d1c374f6bf`
- **JSON Evidence File:** [`combined_transport_community_low/run_combined_transport_community_low_d1c374f6bf.json`](combined_transport_community_low/run_combined_transport_community_low_d1c374f6bf.json)
- **SHA-256 Digest:** `8cb3a1f9494bb35a62326c4a89160f3306f7b597285a35244d474085e29f7a9a`
- **Description:** Complete transport cost (₹2/kg) combined with 10 eligible community reports having a low median of ₹22/kg.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 10 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 10 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹22.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.20 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=10, Duplicates=0, Eligible=10 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.20 (Weight Active)**
- *Explanation:* Sample requirement satisfied (10 >= 10 independent reports). Community median is ₹22.00/kg.

**Step 5: Apply Adaptive Range Reconciliation**
- *Formula:* `Reconciled Reference = (1 - α) × Baseline Reference + α × Community Median`
- *Substitution:* `(1 - 0.20) × ₹30.25 + 0.20 × ₹22.00`
- *Result:* **Reconciled Reference = ₹28.60/kg (Range: ₹26.95–₹30.25)**
- *Explanation:* Cost-basis baseline midpoint (₹30.25) reconciled with crowd reports (₹22.00) using α=0.20.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_RECONCILED`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹26.95–₹30.25/kg (Midpoint: ₹28.6)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 10 eligible reports (sufficient=True) | 10 eligible reports (sufficient=True) | **PASS** |
| Reconciliation Weight (α) | α between 0.20 and 0.20 | α = 0.20 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_RECONCILED | TRANSPORT_AWARE_RECONCILED | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Combined 2 — Transport Available + High Community Median
- **Run ID:** `run_combined_transport_community_high_b35d37d1a7`
- **JSON Evidence File:** [`combined_transport_community_high/run_combined_transport_community_high_b35d37d1a7.json`](combined_transport_community_high/run_combined_transport_community_high_b35d37d1a7.json)
- **SHA-256 Digest:** `1f75ccbaa57303a1b0b70b33d496a51404bf1160d172aff697afb6e7bef200be`
- **Description:** Transport cost (₹2/kg) combined with 10 community reports showing high retail prices (median ₹36/kg).

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 10 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 10 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹36.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.20 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=10, Duplicates=0, Eligible=10 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.20 (Weight Active)**
- *Explanation:* Sample requirement satisfied (10 >= 10 independent reports). Community median is ₹36.00/kg.

**Step 5: Apply Adaptive Range Reconciliation**
- *Formula:* `Reconciled Reference = (1 - α) × Baseline Reference + α × Community Median`
- *Substitution:* `(1 - 0.20) × ₹30.25 + 0.20 × ₹36.00`
- *Result:* **Reconciled Reference = ₹31.40/kg (Range: ₹29.75–₹33.05)**
- *Explanation:* Cost-basis baseline midpoint (₹30.25) reconciled with crowd reports (₹36.00) using α=0.20.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_RECONCILED`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹29.75–₹33.05/kg (Midpoint: ₹31.4)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 10 eligible reports (sufficient=True) | 10 eligible reports (sufficient=True) | **PASS** |
| Reconciliation Weight (α) | α between 0.20 and 0.20 | α = 0.20 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_RECONCILED | TRANSPORT_AWARE_RECONCILED | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Combined 3 — Transport Unavailable + Sufficient Community Reports
- **Run ID:** `run_combined_transport_unavail_community_sufficient_c015ab4c86`
- **JSON Evidence File:** [`combined_transport_unavail_community_sufficient/run_combined_transport_unavail_community_sufficient_c015ab4c86.json`](combined_transport_unavail_community_sufficient/run_combined_transport_unavail_community_sufficient_c015ab4c86.json)
- **SHA-256 Digest:** `d3212dffc400ada48d0cdaa61971a9b923a0b0d64ace493e8036f279a08b8910`
- **Description:** Demonstrates that community reconciliation can still adjust a provisional wholesale baseline when transport is missing.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹Unavailable | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 10 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 10 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹24.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.20 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Evaluate Transport & Determine Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price (Transport Unavailable)`
- *Substitution:* `₹20.00 + [Transport Unconfigured]`
- *Result:* **Provisional Cost Basis = ₹20.00/kg**
- *Explanation:* Transport cost is unavailable. Calculating provisional wholesale-based baseline (not a delivered-cost estimate).

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹20.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹26.00/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹20.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹29.00/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=10, Duplicates=0, Eligible=10 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.20 (Weight Active)**
- *Explanation:* Sample requirement satisfied (10 >= 10 independent reports). Community median is ₹24.00/kg.

**Step 5: Apply Adaptive Range Reconciliation**
- *Formula:* `Reconciled Reference = (1 - α) × Baseline Reference + α × Community Median`
- *Substitution:* `(1 - 0.20) × ₹27.50 + 0.20 × ₹24.00`
- *Result:* **Reconciled Reference = ₹26.80/kg (Range: ₹25.30–₹28.30)**
- *Explanation:* Cost-basis baseline midpoint (₹27.50) reconciled with crowd reports (₹24.00) using α=0.20.

#### Actual Computed Output
- **Calculation Status:** `PROVISIONAL_WHOLESALE_RECONCILED`
- **Baseline Fair Range:** ₹26.0–₹29.0/kg
- **Reconciled Fair Range:** ₹25.3–₹28.3/kg (Midpoint: ₹26.8)
- **Transport Status:** `unavailable`
- **Provisional Indicator:** `True`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | unavailable | unavailable | **PASS** |
| Sample Sufficiency | 10 eligible reports (sufficient=True) | 10 eligible reports (sufficient=True) | **PASS** |
| Reconciliation Weight (α) | α between 0.20 and 0.20 | α = 0.20 | **PASS** |
| Calculation Status | PROVISIONAL_WHOLESALE_RECONCILED | PROVISIONAL_WHOLESALE_RECONCILED | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=26.0, max=29.0 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Combined 4 — High Community Prices with Flagged Duplicates
- **Run ID:** `run_combined_high_community_with_duplicates_135199cde2`
- **JSON Evidence File:** [`combined_high_community_with_duplicates/run_combined_high_community_with_duplicates_135199cde2.json`](combined_high_community_with_duplicates/run_combined_high_community_with_duplicates_135199cde2.json)
- **SHA-256 Digest:** `169bb22e2ddaf63273f4eca3e09f3e41de09ec2d5191b80af4f568a361414295`
- **Description:** 14 high-price reports (median ₹36), but 6 flagged as duplicates -> only 8 independent reports remain, correctly preventing weight activation.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 14 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 8 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹37.0 | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=14, Duplicates=6, Eligible=8 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.00 (Weight Inactive)**
- *Explanation:* Sample requirement not satisfied (8 < 10 independent reports). Community weight α = 0.0; empirical median does not influence final price.

**Step 5: Preserve Baseline Reference (Reconciliation Inactive)**
- *Formula:* `Final Range = Baseline Range (α = 0.0)`
- *Substitution:* `Final Range = Baseline Range`
- *Result:* **Final Output Range = ₹28.60–₹31.90/kg**
- *Explanation:* Because α = 0.0, the pure cost-basis baseline range is preserved in full without distortion.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_BASELINE`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹28.6–₹31.9/kg (Midpoint: ₹30.25)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 8 eligible reports (sufficient=False) | 8 eligible reports (sufficient=False) | **PASS** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_BASELINE | TRANSPORT_AWARE_BASELINE | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Combined 5 — Missing Wholesale Price (No Fabrication)
- **Run ID:** `run_combined_missing_wholesale_30ae4aefe6`
- **JSON Evidence File:** [`combined_missing_wholesale/run_combined_missing_wholesale_30ae4aefe6.json`](combined_missing_wholesale/run_combined_missing_wholesale_30ae4aefe6.json)
- **SHA-256 Digest:** `0fdcf6b862f0a0016874aec1f66a684d178ad24ddb3ecc5204566ae1fa2c31e4`
- **Description:** Wholesale market price is missing or null. The system must refuse to fabricate a fair price and report status UNAVAILABLE.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹Unavailable | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 1 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 0 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹Unavailable | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Evaluate Wholesale Input**
- *Formula:* `Cost Basis = Wholesale Price (Wholesale Required)`
- *Substitution:* `Wholesale Price = Unavailable`
- *Result:* **Cost Basis = Unavailable**
- *Explanation:* No valid wholesale observation exists. Pricing engine refuses to fabricate a price.

#### Actual Computed Output
- **Calculation Status:** `UNAVAILABLE`
- **Baseline Fair Range:** Unavailable
- **Reconciled Fair Range:** None
- **Transport Status:** `unavailable`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | unavailable | unavailable | **PASS** |
| Sample Sufficiency | 0 eligible reports (sufficient=False) | 0 eligible reports (sufficient=False) | **PASS** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | UNAVAILABLE | UNAVAILABLE | **PASS** |
| Baseline Ordering & Validity | Unavailable (missing wholesale) | None | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

### Combined 6 — Unsupported Unit (Non-Weight Units Filtered)
- **Run ID:** `run_combined_invalid_unit_f61774e406`
- **JSON Evidence File:** [`combined_invalid_unit/run_combined_invalid_unit_f61774e406.json`](combined_invalid_unit/run_combined_invalid_unit_f61774e406.json)
- **SHA-256 Digest:** `85e859cb789487dfb1c09cf19f315b057bd4e7aa0d36b00de7bbc316eacf6008`
- **Description:** Community submissions quoted per 'bunch' or 'piece' without weight conversion data are excluded from ₹/kg normalization.

#### Input Parameters
| Parameter | Input Value | Unit | Source |
|---|---|---|---|
| Commodity | Tomato | — | Deterministic Fixture |
| Wholesale Price | ₹20.0 | ₹/kg | Mock Observation |
| Transport Cost | ₹2.0 | ₹/kg | Vehicle Rate Profile |
| Retail Markup Range | +30% to +45% | % | Standard Policy |
| Freshness Deduction | +0 (No freshness deduction) | ₹/kg | Quality Grading Model |
| Raw Submissions | 3 reports | Count | Crowd-sourced Fixture |
| Eligible Independent Reports | 0 reports | Count | Excludes Duplicates & Stale |
| Community Median | ₹Unavailable | ₹/kg | Eligible Median |
| Adaptive Weight (α) | 0.00 | 0.0–0.40 | Sample Gate Policy |

#### Step-by-Step Mathematical Calculation (Computed from Actual Output)

**Step 1: Determine Delivered Cost Basis**
- *Formula:* `Cost Basis = Wholesale Price + Transport Cost per kg`
- *Substitution:* `₹20.00 + ₹2.00`
- *Result:* **Delivered Cost Basis = ₹22.00/kg**
- *Explanation:* Delivered cost includes freight (distance_vehicle_model) to retail locality.

**Step 2: Calculate Minimum Baseline Boundary**
- *Formula:* `Baseline Min = Cost Basis × (1 + Minimum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.30) + (+0)`
- *Result:* **Baseline Minimum = ₹28.60/kg**
- *Explanation:* Applies minimum retailer margin (+30%) and quality adjustment (No freshness deduction).

**Step 3: Calculate Maximum Baseline Boundary**
- *Formula:* `Baseline Max = Cost Basis × (1 + Maximum Markup %) + Freshness Adjustment`
- *Substitution:* `₹22.00 × (1 + 0.45) + (+0)`
- *Result:* **Baseline Maximum = ₹31.90/kg**
- *Explanation:* Applies maximum retailer margin (+45%) and quality adjustment (No freshness deduction).

**Step 4: Evaluate Community Evidence & Sample Sufficiency**
- *Formula:* `Adaptive Weight α = 0.0 if Eligible Reports < 10, else min(0.40, 0.20 + 0.02 × (N - 10))`
- *Substitution:* `Total=3, Duplicates=0, Eligible=0 vs Threshold=10`
- *Result:* **Reconciliation Weight (α) = α = 0.00 (Weight Inactive)**
- *Explanation:* Sample requirement not satisfied (0 < 10 independent reports). Community weight α = 0.0; empirical median does not influence final price.

**Step 5: Preserve Baseline Reference (Reconciliation Inactive)**
- *Formula:* `Final Range = Baseline Range (α = 0.0)`
- *Substitution:* `Final Range = Baseline Range`
- *Result:* **Final Output Range = ₹28.60–₹31.90/kg**
- *Explanation:* Because α = 0.0, the pure cost-basis baseline range is preserved in full without distortion.

#### Actual Computed Output
- **Calculation Status:** `TRANSPORT_AWARE_BASELINE`
- **Baseline Fair Range:** ₹28.6–₹31.9/kg
- **Reconciled Fair Range:** ₹28.6–₹31.9/kg (Midpoint: ₹30.25)
- **Transport Status:** `available`
- **Provisional Indicator:** `False`

#### Expected vs. Actual Assertions
| Check | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Transport Availability | available | available | **PASS** |
| Sample Sufficiency | 0 eligible reports (sufficient=False) | 0 eligible reports (sufficient=False) | **PASS** |
| Reconciliation Weight (α) | α between 0.00 and 0.00 | α = 0.00 | **PASS** |
| Calculation Status | TRANSPORT_AWARE_BASELINE | TRANSPORT_AWARE_BASELINE | **PASS** |
| Baseline Ordering & Validity | 0 <= min <= max (finite positive numbers) | min=28.6, max=31.9 | **PASS** |
| Atomic Evidence Persistence | Saved to scenario directory with manifest entry | Successfully Saved | **PASS** |

---

## 3. Methodological & Integrity Notes
1. **Isolation Guarantee:** All calculations run via `PricingReconciliationService.reconcile` in transient memory without inserting experimental mock submissions into `backend/sahi_daam.db`.
2. **Bit-for-Bit Determinism:** Every numeric value is serialized with sorted keys and compact separators under IEEE 754 non-finite rejection.
3. **Anti-Sybil duplicate gating:** Flagged duplicates are strictly deducted prior to sample threshold evaluation.
4. **Provisional Transparency:** When transport is unavailable, output is explicitly flagged as `PROVISIONAL_WHOLESALE_BASELINE` rather than falsely assuming ₹0 freight.

## 4. How to Verify Evidence
To re-run and verify all scenarios:
```bash
python -m unittest backend/tests/test_experiment_service.py -v
```
