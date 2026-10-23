import os
from pathlib import Path
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Ensure environment variables are loaded
_BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(_BACKEND_DIR / ".env")

DEFAULT_DB_PATH = _BACKEND_DIR / "data" / "sahi_daam.db"
DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

# Configure SQLite engine with foreign-keys and WAL mode enabled
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine=None) -> None:
    """Initialize database tables using non-destructive checkfirst=True."""
    from . import models  # noqa: F401 - ensure models are registered
    active_engine = target_engine or engine
    Base.metadata.create_all(bind=active_engine, checkfirst=True)

    # Lightweight non-destructive column migration for SQLite
    try:
        from sqlalchemy import text
        with active_engine.connect() as conn:
            cursor = conn.execute(text("PRAGMA table_info(community_price_observations)"))
            existing_cols = {row[1] for row in cursor.fetchall()}
            if existing_cols:
                if "normalized_price_per_kg" not in existing_cols:
                    conn.execute(text("ALTER TABLE community_price_observations ADD COLUMN normalized_price_per_kg FLOAT"))
                if "duplicate_reason" not in existing_cols:
                    conn.execute(text("ALTER TABLE community_price_observations ADD COLUMN duplicate_reason VARCHAR(256)"))
                conn.commit()
    except Exception:
        pass
