# Sahi Daam

Sahi Daam is a fair-price companion app for buying fruits and vegetables that empowers consumers by combining computer-vision freshness detection with real wholesale market data to calculate an objective fair retail price and help them negotiate confidently. 

## Architecture

```text
+----------------+        +-------------------+
|                |        |                   |
|  Frontend (UI) +-------->   Backend API     |
|                |        |                   |
+----------------+        +----+---------+----+
                               |         |
                     +---------v-+     +-v-----------+
                     |           |     |             |
                     |  Pricing  |     | ML / Vision |
                     |  Engine   |     |             |
                     +-----+-----+     +-------------+
                           |
                     +-----v-----+
                     |           |
                     |   Data    |
                     |           |
                     +-----------+
```

## Team Ownership

| Team Member | Area | README Link |
|-------------|------|-------------|
| Person 1 | Backend Data & Loaders | [backend/data/README.md](backend/data/README.md) |
| Person 2 | ML Models | [backend/ml/README.md](backend/ml/README.md) |
| Person 3 | Pricing Engine | [backend/pricing/README.md](backend/pricing/README.md) |

**Rule**: Do NOT change API response field names or shapes. Only replace the logic that generates the values!

## Running Locally

### Backend
1. Navigate to the `backend` directory: `cd backend`
2. Create and activate a virtual environment: `python -m venv venv` and `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux).
3. Install dependencies: `pip install -r requirements.txt`
4. Run the server: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
5. The API will be available at `http://127.0.0.1:8000`.

### Frontend
1. Navigate to the `frontend` directory: `cd frontend`
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev -- --host`
4. The application will be available at `http://localhost:5173`.
5. Note: The frontend uses a Vite proxy (`/api`) to automatically route backend calls to `http://127.0.0.1:8000`.

### Testing on a Phone (via ngrok)
Since the frontend proxies API requests to the backend, you only need one ngrok tunnel for the frontend:
1. Run both the backend and frontend servers as described above.
2. Expose the frontend port via ngrok: `ngrok http 5173` (or use your static domain: `ngrok http 5173 --domain=your-domain.ngrok-free.app`).
3. Access the ngrok URL on your phone.

## Documentation
- [API Contract](docs/API_CONTRACT.md)
- [Data Schema](docs/DATA_SCHEMA.md)
