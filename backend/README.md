# Sahi Daam Backend — Uncertainty-Driven Adaptive Valuation Pipeline

The Sahi Daam backend implements the core algorithmic patent architecture: **Uncertainty-Driven Adaptive Valuation System for Quality-Aware Commodity Pricing Using Active Observation and Multi-Source Market Evidence**.

---

## Directory Architecture

```
backend/
├── config.py                       # Centralized thresholds (EVI, observation cost, uncertainty limits)
├── main.py                         # FastAPI gateway & middleware configuration
├── simulation_harness.py           # Standalone verification runner for patent benchmark scenarios
│
├── core/
│   └── schemas.py                  # Pydantic schemas: Observation, QualityEstimate, ValuationResult, etc.
│
├── uncertainty/
│   └── estimator.py                # Epistemic visual uncertainty metric (confidence, blur, margin, disagreement)
│
├── quality/
│   └── estimator.py                # Model-agnostic IQualityEstimator (Hybrid, Gemini, Local, Simulated)
│
├── market/
│   ├── evidence.py                 # Multi-source market evidence ingestion (Agmarknet, Nearby, Cache)
│   ├── reliability.py              # Multi-factor reliability scorer (recency decay, geo, authority, consistency)
│   └── estimator.py                # Reliability-weighted wholesale estimator & sample dispersion variance
│
├── valuation/
│   ├── adjustment.py               # Dynamic perishability-aware quality-to-price adjustment model
│   └── engine.py                   # Compound variance propagation (σ_fair²) & interval expansion
│
├── controller/
│   └── observation_controller.py   # Adaptive observation controller (Expected Value of Information vs. Cost)
│
├── observation/
│   └── fusion.py                   # Multi-observation fusion engine (defect preservation & variance reduction)
│
├── session/
│   └── manager.py                  # In-memory & persistent session state manager with decision traces
│
├── pricing/
│   ├── anomaly.py                  # Confidence-gated deal anomaly classifier (INSUFFICIENT_CONFIDENCE guard)
│   ├── engine.py                   # Legacy pricing interface
│   └── phrasebook.py               # Multilingual negotiation phrasebook
│
├── routers/
│   ├── valuation.py                # REST endpoints: /valuation/session, /observe, /decision, /simulate
│   ├── scan.py                     # Backward-compatible scan endpoint with session initialization
│   └── haggle.py                   # Confidence-aware bargaining endpoint
│
└── tests/
    └── test_adaptive_valuation.py  # Comprehensive automated pytest suite
```

---

## Key Algorithms & Mathematical Formulations

1. **Quality Uncertainty ($U_{\text{quality}}$)**:
   $$U_{\text{quality}} = \min\left(1.0, w_c (1 - C) + w_d D + w_i P_{\text{image}} + w_v P_{\text{coverage}} + w_a P_{\text{ambiguity}}\right)$$
2. **Market Source Reliability ($R_i$)**:
   $$R_i = w_t S_{\text{recency}} + w_g S_{\text{geo}} + w_s S_{\text{source}} + w_c S_{\text{consistency}}$$
3. **Reliability-Weighted Market Benchmark ($P_{\text{market}}$)**:
   $$P_{\text{market}} = \frac{\sum w_i P_i}{\sum w_i}, \quad \sigma_{\text{market}}^2 = \sum w_i (P_i - P_{\text{market}})^2$$
4. **Compound Valuation Variance Propagation ($\sigma_{\text{fair}}^2$)**:
   $$\sigma_{\text{fair}}^2 = \sigma_{\text{market}}^2 + \sigma_{\text{adj}}^2 + \sigma_{\text{model}}^2$$
   $$\Delta = Z \cdot \sigma_{\text{fair}} \cdot (1 + \lambda \cdot U_{\text{valuation}})$$
5. **Adaptive Value of Information ($\text{EVI}$)**:
   $$\text{EVI} = U_{\text{current}} \cdot \gamma_{\text{gain}} - \text{Cost}_{\text{observation}}$$

---

## Running Backend & Tests

```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Run automated tests
pytest

# Run deterministic benchmark simulation harness
python simulation_harness.py

# Start live FastAPI dev server
uvicorn main:app --reload --port 8000
```
