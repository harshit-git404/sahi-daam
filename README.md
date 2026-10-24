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
1. Use the project virtual environment: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux).
2. Setup environment variables: Verify `.env` contains your Gemini or Agmarknet configuration (if using live external providers; fallback works offline with local models and seeded data).
3. The database is initialized and seeded idempotently on startup. To manually verify or re-seed:
   `python -c "from backend.database import init_db, seed_database, SessionLocal; init_db(); s=SessionLocal(); seed_database(s); s.close()"`
4. Run the server: `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
5. The API will be available at `http://127.0.0.1:8000` (docs at `http://127.0.0.1:8000/docs`).

### Frontend
1. Navigate to the `frontend` directory: `cd frontend`
2. Install dependencies: `npm install`
3. Build & Typecheck: `npm run build`
4. Run the development server: `npm run dev -- --host`
5. The application will be available at `http://localhost:5173`.
6. Note: The frontend uses a Vite proxy (`/api`) to automatically route backend calls to `http://127.0.0.1:8000`.

### Cryptographic Ledger Verification
To independently verify the global SHA-256 hash chain and ledger integrity:
```bash
python -m backend.scripts.verify_ledger
```
Optional flags:
- `--db-url sqlite:///backend/sahi_daam.db`: Custom database path.
- `--checkpoint checkpoint.json`: Verify against a trusted checkpoint file.
- `--create-checkpoint out.json`: Export current chain state as a trusted checkpoint.

### Running Tests
- **Backend Test Suite (124+ automated tests)**:
  ```bash
  python -m unittest discover -s backend/tests -v
  ```
- **Frontend Build & Linter**:
  ```bash
  cd frontend
  npm run build
  npm run lint
  ```

## Documentation
- [API Contract](docs/API_CONTRACT.md)
- [Data Schema](docs/DATA_SCHEMA.md)
