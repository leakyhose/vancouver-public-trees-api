from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from .db import engine
from redis_cache import redis_cache

router = APIRouter(prefix="/api/v1/trees/search", tags=["search"])


@redis_cache(3600)
@router.get("")
async def search_trees(
    bbox: str = Query(default=None),
    coordinates: str = Query(default=None),
    radius: float = Query(default=None),
    nearest: str = Query(default=None),
    count: int = Query(default=None, le=100),
    limit: int = Query(default=50, le=100)
):
    # nearest neighbor
    if nearest:
        if bbox or coordinates or radius:
            raise HTTPException(status_code=400, detail="Cannot combine nearest with other params")
        try:
            lat, lon = map(float, nearest.split(","))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid nearest format")
        n = count if count else 10

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tree_id, genus_name, species_name, common_name,
                       ST_X(geom) as longitude, ST_Y(geom) as latitude
                FROM trees
                ORDER BY geom <-> ST_MakePoint(:lon, :lat)::geometry
                LIMIT :n
            """), {"lon": lon, "lat": lat, "n": n})
            rows = result.fetchall()

    # radius
    elif coordinates and radius:
        if bbox:
            raise HTTPException(status_code=400, detail="Cannot use bbox with radius search")
        try:
            lat, lon = map(float, coordinates.split(","))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid coordinates format")
        if radius <= 0:
            raise HTTPException(status_code=400, detail="Radius must be positive")

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tree_id, genus_name, species_name, common_name,
                       ST_X(geom) as longitude, ST_Y(geom) as latitude
                FROM trees
                WHERE ST_DWithin(geom::geography, ST_MakePoint(:lon, :lat)::geography, :radius)
                LIMIT :limit
            """), {"lon": lon, "lat": lat, "radius": radius, "limit": limit})
            rows = result.fetchall()

    # bbox
    elif bbox:
        if coordinates or radius:
            raise HTTPException(status_code=400, detail="Cannot combine bbox with other spatial params")
        coords = bbox.split(",")
        if len(coords) != 4:
            raise HTTPException(status_code=400, detail="bbox must have 4 values")
        try:
            min_lon, min_lat, max_lon, max_lat = map(float, coords)
        except ValueError:
            raise HTTPException(status_code=400, detail="bbox values must be numbers")

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tree_id, genus_name, species_name, common_name,
                       ST_X(geom) as longitude, ST_Y(geom) as latitude
                FROM trees
                WHERE geom && ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
                LIMIT :limit
            """), {
                "min_lon": min_lon, "min_lat": min_lat,
                "max_lon": max_lon, "max_lat": max_lat,
                "limit": limit
            })
            rows = result.fetchall()
    else:
        raise HTTPException(status_code=400, detail="Provide bbox, coordinates+radius, or nearest")

    return {"data": [{
        "id": row.tree_id,
        "genus_name": row.genus_name,
        "species_name": row.species_name,
        "common_name": row.common_name,
        "geometry": {"type": "Point", "coordinates": [row.longitude, row.latitude]}
    } for row in rows]}
