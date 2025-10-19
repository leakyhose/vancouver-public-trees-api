import os
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/health/db")
async def health_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")