import os
from fastapi import FastAPI
from sqlalchemy import create_engine
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