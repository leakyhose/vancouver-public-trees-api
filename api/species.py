from fastapi import APIRouter
from sqlalchemy import text
from .db import engine
from redis_cache import redis_cache

router = APIRouter(prefix="/api/v1/species", tags=["species"])

@redis_cache(expire_seconds=3600)
@router.get("")
async def list_species():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT species_name FROM trees
            WHERE species_name IS NOT NULL
            ORDER BY species_name
        """))
        rows = result.fetchall()
    return {"species": [row.species_name for row in rows]}
