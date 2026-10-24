import logging
import sys
from pathlib import Path

# Ensure project root and backend directory are in sys.path so that
# 'backend.*' absolute imports and local imports work consistently
# whether uvicorn is launched from the workspace root or the backend directory.
_backend_dir = Path(__file__).resolve().parent
_project_root = _backend_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.ml.freshness_model import load_freshness_model
    from backend.ml.produce_classifier import load_produce_classifier
    from backend.routers import scan, haggle, sector, community, locations, ledger
    from backend.database import init_db, seed_database, SessionLocal
except ImportError:
    from ml.freshness_model import load_freshness_model
    from ml.produce_classifier import load_produce_classifier
    from routers import scan, haggle, sector, community, locations, ledger
    from database import init_db, seed_database, SessionLocal

app = FastAPI(title="Sahi Daam API")
logger = logging.getLogger(__name__)


def load_ml_models() -> None:
    logger.info("Loading local ML models")
    classifier_loaded = load_produce_classifier()
    load_freshness_model()
    if classifier_loaded:
        logger.info("Local ML models loaded successfully")
    else:
        logger.warning(
            "Produce classifier is unavailable (network/remote loading failed). "
            "Operating with Gemini as primary vision provider; local produce fallback will be disabled."
        )


@app.on_event("startup")
def startup_events() -> None:
    logger.info("Initializing database...")
    init_db()
    with SessionLocal() as db_session:
        seed_summary = seed_database(db_session)
        logger.info(
            "Database initialized and seeded: %d localities, %d mandis, %d transport configs, %d community observations",
            seed_summary["localities_count"],
            seed_summary["mandis_count"],
            seed_summary["transport_configs_count"],
            seed_summary["community_observations_count"],
        )

    load_ml_models()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https://.*\.ngrok-free\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(scan.router)
app.include_router(haggle.router)
app.include_router(sector.router)
app.include_router(community.router)
app.include_router(locations.router)
app.include_router(ledger.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
