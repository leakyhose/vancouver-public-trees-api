from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from .db import engine

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("")
async def health():
    return {"status": "ok"}


@router.get("/db")
async def health_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")
