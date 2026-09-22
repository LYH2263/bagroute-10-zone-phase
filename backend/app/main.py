from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.seed import seed_if_empty


# 轻量幂等建列：项目用 create_all 建表、无迁移工具，
# 旧库缺少后加的 segment 列时在此补齐。
_ENSURE_COLUMNS = [
    "ALTER TABLE subscriber_stops ADD COLUMN IF NOT EXISTS segment VARCHAR(8) DEFAULT 'front'",
    "ALTER TABLE pack_bags ADD COLUMN IF NOT EXISTS segment VARCHAR(8) DEFAULT 'front'",
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        for ddl in _ENSURE_COLUMNS:
            conn.execute(text(ddl))
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
