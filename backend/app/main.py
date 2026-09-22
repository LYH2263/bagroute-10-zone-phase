from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.router import api_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.seed import seed_if_empty


def _ensure_segment_columns() -> None:
    """Backfill segment columns on databases created before they existed."""
    insp = inspect(engine)
    with engine.begin() as conn:
        for table in ("subscriber_stops", "pack_bags"):
            cols = {c["name"] for c in insp.get_columns(table)}
            if "segment" not in cols:
                conn.execute(
                    text(f"ALTER TABLE {table} ADD COLUMN segment VARCHAR(8) NOT NULL DEFAULT 'front'")
                )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _ensure_segment_columns()
    if settings.seed_on_empty:
        db = SessionLocal()
        try:
            seed_if_empty(db)
        finally:
            db.close()
    yield


app = FastAPI(title="BagRoute", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")
