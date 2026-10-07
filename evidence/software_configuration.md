# Software Configuration & Architectural Topology

## 1. Module Architecture (`inspection_control/`)
- `domain/`: Physical lot, strata states, dynamic access graph, non-additive exposure ledger.
- `sensing/`: Hardware drivers (OpenCV `RealOpenCVCameraDriver`, serial thermal probe, fault-tolerant fusion hub).
- `dynamics/`: Non-additive exposure coupling model, produce deterioration model, exposure-dependent observation quality model.
- `estimation/`: OpenCV color/contour defect segmenter, Bayesian Beta-Binomial conjugate posterior updater with analytic CLT tail risk.
- `planning/`: Receding-horizon controller (`FB7_Exposure_Aware_Planner`) and 6 fair baselines (`FB0`..`FB6`).
- `station/`: Hardware abstraction layer (`PhysicalInspectionStation`).
- `evidence/`: Immutable SQLite & CSV audit logger, post-inspection teardown evaluator.
- `api/` & `ui/`: FastAPI real-time station server & interactive operator dashboard.

## 2. Dependencies
- Python 3.13 (`backend/venv`)
- OpenCV (`cv2`) 5.0.0, NumPy 2.5.2, SciPy 1.18.1, Pandas 3.0.6, Matplotlib 3.11.2, FastAPI 0.115.0, Pytest 9.1.1.
