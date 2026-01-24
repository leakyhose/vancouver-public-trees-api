from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from .db import engine
from redis_client import r


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
    
@router.get("/redis")
async def health_redis():
    try:
        pong = r.ping()
        if pong:
            return {"status": "ok", "redis": "connected"}
        else:
            raise HTTPException(status_code=503, detail="Redis unavailable")
    except Exception:
        raise HTTPException(status_code=503, detail="Redis unavailable")
