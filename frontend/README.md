# Sahi Daam Frontend — Adaptive Valuation UI

The Sahi Daam client interface visualizes the closed-loop **Uncertainty-Driven Adaptive Valuation System**, displaying multi-source evidence, compound uncertainty indicators, targeted active observation prompts, before/after range comparisons, and explainable decision traces.

---

## Key Features

1. **Confidence Status Badge**: Displays `HIGH CONFIDENCE`, `MEDIUM CONFIDENCE`, or `LOW CONFIDENCE` dynamically based on propagated valuation variance.
2. **Uncertainty Breakdown Card**: Displays separate uncertainty gauges for Visual Quality ($U_q$), Market Evidence ($U_m$), and Compound Valuation ($U_{\text{val}}$).
3. **Active Observation Request Prompt**: When the controller determines that Expected Value of Information exceeds observation cost ($\text{EVI} > \text{Cost}$), prompts the user with targeted instructions (e.g., *"Capture another angle or opposite side of produce to inspect hidden surfaces"*).
4. **Before/After Range Comparison**: When a secondary viewpoint is fused, highlights the reduction in fair price interval width and drop in compound uncertainty.
5. **Explainable Decision Trace**: Expandable diagnostic section exposing each algorithmic stage, intermediate values, and rationale.
6. **Validation & Demonstration Mode**: Click the **Beaker / Science** button in the top header to run any of the 8 deterministic patent benchmark scenarios directly.

---

## How to Run

```bash
# Install dependencies
npm install

# Start Vite development server
npm run dev

# Run production build
npm run build
```
The frontend automatically proxies `/api` calls to the local FastAPI backend on port 8000.
