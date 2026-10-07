# Sahi Daam — Uncertainty-Driven Adaptive Valuation System

> **Patent Title**: *Uncertainty-Driven Adaptive Valuation System for Quality-Aware Commodity Pricing Using Active Observation and Multi-Source Market Evidence*

Sahi Daam is an intelligent, closed-loop commodity appraisal platform. Unlike traditional static price calculators, Sahi Daam dynamically models epistemic and aleatoric uncertainty across visual quality assessment and multi-source mandi data, optimizing the **Expected Value of Information (EVI)** to guide active multi-view observation and compute confidence-calibrated fair retail intervals.

---

## The Core Invention: Closed-Loop Active Observation

```
INITIAL OBSERVATION (Image k=1)
        ↓
QUALITY / DEFECT ESTIMATION
        ↓
EPISTEMIC UNCERTAINTY QUANTIFICATION (U_quality)
        ↓
MULTI-SOURCE MARKET EVIDENCE INGESTION (Agmarknet, Nearby Mandis, Cache)
        ↓
MARKET SOURCE MULTI-FACTOR RELIABILITY SCORING (Recency, Geo, Authority, Consistency)
        ↓
DYNAMIC QUALITY-TO-PRICE ADJUSTMENT
        ↓
COMPOUND VALUATION UNCERTAINTY PROPAGATION (σ_fair²)
        ↓
ADAPTIVE OBSERVATION CONTROLLER
 ┌─────────────────────────────────────────────────────────┐
 │ Is Expected Value of Information (EVI) > Observation Cost? │
 └─────────────────────────────────────────────────────────┘
           ↓ YES                                    ↓ NO
  TARGETED OBSERVATION REQUEST                FINALIZE VALUATION
  ("Capture opposite side to inspect defects")      ↓
           ↓                                  CONFIDENCE-GATED ANOMALY CHECK
  USER SUPPLIES OBSERVATION k=2                     ↓
           ↓                                  CONFIDENCE-AWARE NEGOTIATION
  MULTI-OBSERVATION FUSION ENGINE
  (Defect Preservation & Variance Reduction)
           ↓
  RECOMPUTE & RE-EVALUATE
```

---

## Architectural Highlights

1. **Epistemic Uncertainty Engine (`backend/uncertainty/estimator.py`)**: Quantifies confidence, model disagreement, blur, visual coverage, and class margin deterministically.
2. **Model-Agnostic Quality Estimators (`backend/quality/estimator.py`)**: Decoupled `IQualityEstimator` interface supporting multimodal VLMs (Gemini), local CNN/ViT architectures, or synthetic validation estimators.
3. **Multi-Source Market Reliability Scorer (`backend/market/reliability.py`)**: Computes composite evidence weights across temporal freshness (decay), spatial distance, authority, and inter-mandi consistency.
4. **Weighted Market Dispersion Estimator (`backend/market/estimator.py`)**: Replaces rigid single fallbacks with reliability-weighted wholesale prices and explicit variance quantification.
5. **Quality-Price Dynamic Adjustment (`backend/valuation/adjustment.py`)**: Replaces fixed flat deductions with perishability-indexed, market-relative value functions.
6. **Compound Valuation Variance Propagation (`backend/valuation/engine.py`)**: Propagates compound variance $\sigma_{\text{fair}}^2 = \sigma_{\text{market}}^2 + \sigma_{\text{adj}}^2 + \sigma_{\text{model}}^2$, dynamically widening or narrowing fair price intervals based on certainty.
7. **Adaptive Observation Controller (`backend/controller/observation_controller.py`)**: Decides whether to acquire additional viewpoints based on Expected Value of Information (EVI) vs. observation cost.
8. **Multi-Observation Fusion (`backend/observation/fusion.py`)**: Asymmetrically preserves localized defects and shrinks visual coverage uncertainty when independent views agree.
9. **Confidence-Gated Negotiation Guardrails (`backend/pricing/anomaly.py`)**: Suppresses false overpricing accusations when valuation uncertainty is high (`INSUFFICIENT_CONFIDENCE`).
10. **Explainable Decision Trace**: Emits step-by-step diagnostic reasoning for every valuation and controller decision.

---

## Running Locally

### Backend
1. `cd backend`
2. Activate virtual environment: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
3. Install dependencies: `pip install -r requirements.txt`
4. Run server: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
5. API documentation available at: `http://127.0.0.1:8000/docs`

### Frontend
1. `cd frontend`
2. Install dependencies: `npm install`
3. Run dev server: `npm run dev`
4. Access client at: `http://localhost:5173`

---

## Verification & Patent Validation Suite

### 1. Automated Test Suite (Pytest)
```powershell
cd backend
.\venv\Scripts\python.exe -m pytest
```
*77 tests covering mathematical uncertainty, market fusion, variance propagation, controller EVI thresholds, multi-observation defect preservation, and negotiation safety.*

### 2. Benchmark Simulation Harness
```powershell
cd backend
.\venv\Scripts\python.exe simulation_harness.py
```
*Executes all 8 deterministic patent scenarios and produces `docs/simulation_results.json`.*

### 3. Interactive Demonstration Mode
Inside the frontend, click the **Beaker / Science icon** in the top navigation bar to open the **Validation & Demonstration Mode** dialog and simulate any benchmark scenario on demand.

---

## Detailed Documentation & Technical Traceability

- [System Architecture](docs/ARCHITECTURE.md)
- [Patent Technical Mapping](docs/PATENT_TECHNICAL_MAPPING.md)
- [Experimental Validation Plan](docs/VALIDATION_PLAN.md)
- [Implementation Status & Audit](docs/IMPLEMENTATION_STATUS.md)
- [Architecture & Workflow Diagrams](docs/diagrams/)
- [API Contract](docs/API_CONTRACT.md)
- [Benchmark Results](docs/simulation_results.json)
