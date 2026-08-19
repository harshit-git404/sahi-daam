# Sahi Daam

Sahi Daam is a fair-price companion app for buying fruits and vegetables. It uses machine learning to assess the freshness of produce and provides a fair price range based on wholesale data, helping users negotiate better prices.

## Folder Structure

- `frontend/`: The Vite + React web application with Tailwind CSS.
- `backend/`: The FastAPI backend serving the APIs, ML models, and pricing logic.
  - `backend/main.py`: Entry point for the FastAPI application.
  - `backend/routers/`: API endpoints for scanning and haggling.
  - `backend/ml/`: Machine learning models for freshness detection.
  - `backend/pricing/`: Logic for calculating fair price ranges.
  - `backend/data/`: Static data files like wholesale prices and markup research.

## Running Locally

### Backend
1. Navigate to the `backend` directory: `cd backend`
2. Create and activate a virtual environment: `python -m venv venv` and `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux).
3. Install dependencies: `pip install -r requirements.txt`
4. Run the server: `uvicorn main:app --reload`
5. The API will be available at `http://127.0.0.1:8000`. You can check the health endpoint at `http://127.0.0.1:8000/health`.

### Frontend
1. Navigate to the `frontend` directory: `cd frontend`
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev`
4. The application will be available at the URL provided in the terminal (usually `http://localhost:5173`).

## Team Ownership

| Team Member | Area | Files |
|-------------|------|-------|
| Sai | Backend Data & Loaders | `backend/data/*`, `backend/routers/scan.py` |
| Navneet | ML Models | `backend/ml/freshness_model.py` |
| Abhiram | Pricing Engine | `backend/pricing/engine.py` |

**Rule**: Do NOT change API response field names or shapes. Only replace the logic that generates the values!
