import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from .ml.freshness_model import load_freshness_model
    from .ml.produce_classifier import load_produce_classifier
    from .routers import scan, haggle, sector
except ImportError:
    from ml.freshness_model import load_freshness_model
    from ml.produce_classifier import load_produce_classifier
    from routers import scan, haggle, sector

app = FastAPI(title="Sahi Daam API")
logger = logging.getLogger(__name__)


@app.on_event("startup")
def load_ml_models() -> None:
    logger.info("Loading local ML models")
    load_produce_classifier()
    load_freshness_model()
    logger.info("Local ML models loaded successfully")

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

@app.get("/health")
def health_check():
    return {"status": "ok"}
