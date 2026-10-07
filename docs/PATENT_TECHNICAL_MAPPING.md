# Patent Technical Mapping Specification

This document establishes the 1-to-1 traceability between the legal invention concepts of the patent application and the concrete software implementation in Sahi Daam.

---

## Traceability Matrix

| # | Patent Invention Concept | Software Module & File | API Endpoint | Primary Data Structure | Core Algorithm / Formula | Automated Validation Test |
|---|---|---|---|---|---|---|
| **1** | **Model-Agnostic Quality Estimation** | `backend/quality/estimator.py` | `POST /scan-produce`<br/>`POST /valuation/session` | `QualityEstimate`<br/>`IQualityEstimator` | Multi-model inference + divergence scoring: $D = \|S_{\text{vlm}} - S_{\text{cnn}}\|$ | `test_quality_estimation_with_uncertainty` |
| **2** | **Epistemic Quality Uncertainty Quantification** | `backend/uncertainty/estimator.py` | `POST /valuation/session`<br/>`POST /valuation/observe` | `UncertaintyBreakdown`<br/>`QualityEstimate.uncertainty` | Multi-factor penalty formulation:<br/>$U_q = \sum w_i P_i$ over confidence, disagreement, blur, coverage, ambiguity | `test_uncertainty_estimator_bounded` |
| **3** | **Multi-Source Market Evidence Ingestion** | `backend/market/evidence.py` | `POST /valuation/session` | `MarketEvidenceRecord` | Heterogeneous provider synthesis across APMC Mandis, spatial radius, temporal buffers, and cache | `test_market_evidence_fusion_increases_confidence` |
| **4** | **Market Source Multi-Factor Reliability Scoring** | `backend/market/reliability.py` | Internal Engine | `MarketEvidenceRecord.source_reliability` | Linear composite reliability:<br/>$R = w_t S_{\text{recency}} + w_g S_{\text{geo}} + w_s S_{\text{source}} + w_c S_{\text{consistency}}$ | `test_stale_market_data_decays_reliability` |
| **5** | **Reliability-Weighted Market Price Estimation** | `backend/market/estimator.py` | `POST /valuation/session` | `WeightedMarketPriceEstimate` | Weighted mean & sample dispersion variance:<br/>$P = \frac{\sum w_i P_i}{\sum w_i}$, $\sigma_m^2 = \sum w_i (P_i - P)^2$ | `test_market_disagreement_elevates_uncertainty` |
| **6** | **Commodity-Specific Quality-to-Price Adjustment** | `backend/valuation/adjustment.py` | Internal Engine | `QualityAdjustmentResult` | Dynamic relative adjustment:<br/>$\Delta P = P_{\text{market}} \cdot \beta_{\text{perishability}} \cdot (Q - Q_0)$ | `test_quality_price_adjustment_model` |
| **7** | **Compound Valuation Uncertainty Propagation** | `backend/valuation/engine.py` | `POST /valuation/session`<br/>`POST /valuation/observe` | `ValuationResult`<br/>`ValuationComponents` | Compound variance & dynamic interval expansion:<br/>$\sigma_{\text{fair}}^2 = \sigma_{\text{market}}^2 + \sigma_{\text{adj}}^2 + \sigma_{\text{model}}^2$,<br/>$\Delta = Z \sigma_{\text{fair}} (1 + \lambda U)$ | `test_valuation_uncertainty_widens_interval` |
| **8** | **Adaptive Observation Controller (Active Perception)** | `backend/controller/observation_controller.py` | `POST /valuation/decision`<br/>`POST /valuation/session` | `ControllerDecision`<br/>`ObservationRequest` | Expected Value of Information (EVI) optimization:<br/>$\text{EVI} = U_{\text{current}} \cdot \gamma_{\text{gain}} - \text{Cost}_{\text{obs}}$ | `test_controller_requests_observation`<br/>`test_controller_finalizes_on_low_uncertainty` |
| **9** | **Sequential Multi-Observation Fusion** | `backend/observation/fusion.py` | `POST /valuation/observe` | `ValuationSession.observations`<br/>`QualityEstimate` | Asymmetric defect preservation & variance shrinkage:<br/>$Q_{\text{fused}} = \min(Q_i) \cdot w_{\text{defect}} + Q_{\text{mean}} \cdot (1 - w_{\text{defect}})$ | `test_multi_observation_fusion_reduces_uncertainty`<br/>`test_conflicting_views_preserve_defect` |
| **10** | **Uncertainty-Gated Price-Quality Anomaly Detection** | `backend/pricing/anomaly.py` | `POST /haggle-check` | `AnomalyAnalysisResult` | Epistemic guardrail thresholding:<br/>If $U_{\text{val}} > 0.60 \implies \text{INSUFFICIENT\_CONFIDENCE}$ | `test_deal_classification_confidence_guard` |
| **11** | **Confidence-Aware Tactical Negotiation Engine** | `backend/routers/haggle.py`<br/>`backend/pricing/phrasebook.py` | `POST /haggle-check` | `HaggleCheckResponse` | Dynamic bargaining anchor computation:<br/>$\text{Offer}_{\text{start}} = f(\text{FairMin}, \text{Confidence})$ | `test_haggle_check_respects_uncertainty` |
| **12** | **Session State Persistence & Step-by-Step Decision Trace** | `backend/session/manager.py` | `GET /valuation/{session_id}`<br/>`POST /valuation/observe` | `ValuationSession`<br/>`DecisionTraceStep` | Append-only sequential session graph with before/after metric deltas | `test_session_manager_persistence` |

---

## Benchmark Scenario Verifications

The simulation harness (`backend/simulation_harness.py`) deterministically exercises the 8 core patent assertions:
- **Scenario 1**: High quality image + high market agreement $\rightarrow$ Controller finalizes on View 1 without requesting View 2.
- **Scenario 2**: Blur/ambiguity $\rightarrow$ Controller calculates positive EVI and requests `reverse_side`.
- **Scenario 3**: Agreeing sequential observations $\rightarrow$ Range width narrows from ₹19.2 to ₹16.6; uncertainty drops by 7.3%.
- **Scenario 4**: View 1 pristine (0.88), View 2 bruised (0.35) $\rightarrow$ Fused score drops to 0.496; defect is preserved.
- **Scenario 5**: High spatial mandi variance $\rightarrow$ Market uncertainty rises by 56.9%.
- **Scenario 6**: 96-hour stale mandi reporting $\rightarrow$ Source reliability decays from 0.871 to 0.575.
- **Scenario 7**: Vendor asks ₹55 with confident fair max of ₹41 $\rightarrow$ Definitive `OVERPRICED` verdict with actionable targets.
- **Scenario 8**: Vendor asks ₹55 with highly uncertain valuation ($U=0.706$) $\rightarrow$ `INSUFFICIENT_CONFIDENCE` safeguard prevents false overpricing claim.
