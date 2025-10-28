import os
from fastapi import FastAPI, HTTPException, Query
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


@app.get("/api/v1/trees")
async def list_trees(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    species: str = Query(default=None),
    genus: str = Query(default=None),
    common_name: str = Query(default=None),
    neighborhood: str = Query(default=None),
    min_height: int = Query(default=None),
    max_height: int = Query(default=None),
    planted_after: str = Query(default=None),
    planted_before: str = Query(default=None)
):
    filters = []
    params = {"limit": limit, "offset": offset}

    if species:
        filters.append("species_name = :species")
        params["species"] = species
    if genus:
        filters.append("genus_name = :genus")
        params["genus"] = genus
    if common_name:
        filters.append("common_name = :common_name")
        params["common_name"] = common_name
    if neighborhood:
        filters.append("neighbourhood_name = :neighborhood")
        params["neighborhood"] = neighborhood
    if min_height is not None:
        filters.append("height_range_id >= :min_height")
        params["min_height"] = min_height
    if max_height is not None:
        filters.append("height_range_id <= :max_height")
        params["max_height"] = max_height
    if planted_after:
        filters.append("date_planted >= :planted_after")
        params["planted_after"] = planted_after
    if planted_before:
        filters.append("date_planted <= :planted_before")
        params["planted_before"] = planted_before

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    with engine.connect() as conn:
        count_result = conn.execute(
            text(f"SELECT COUNT(*) FROM trees {where_clause}"), params
        )
        total = count_result.scalar()

        result = conn.execute(text(f"""
            SELECT tree_id, genus_name, species_name, common_name, height_range_id,
                   ST_X(geom) as longitude, ST_Y(geom) as latitude
            FROM trees
            {where_clause}
            ORDER BY tree_id
            LIMIT :limit OFFSET :offset
        """), params)
        rows = result.fetchall()

    data = [{
        "id": row.tree_id,
        "genus_name": row.genus_name,
        "species_name": row.species_name,
        "common_name": row.common_name,
        "height_range_id": row.height_range_id,
        "geometry": {
            "type": "Point",
            "coordinates": [row.longitude, row.latitude]
        }
    } for row in rows]

    return {
        "metadata": {"limit": limit, "offset": offset, "total": total},
        "data": data
    }


@app.get("/api/v1/trees/count")
async def trees_count():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM trees"))
        count = result.scalar()
    return {"count": count}


@app.get("/api/v1/trees/search")
async def search_trees(
    bbox: str = Query(default=None),
    coordinates: str = Query(default=None),
    radius: float = Query(default=None),
    limit: int = Query(default=50, le=100)
):
    # radius search
    if coordinates and radius:
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

    # bbox search
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
        raise HTTPException(status_code=400, detail="Provide bbox or coordinates+radius")

    return {"data": [{
        "id": row.tree_id,
        "genus_name": row.genus_name,
        "species_name": row.species_name,
        "common_name": row.common_name,
        "geometry": {"type": "Point", "coordinates": [row.longitude, row.latitude]}
    } for row in rows]}


@app.get("/api/v1/trees/{tree_id}")
async def get_tree(tree_id: int):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT tree_id, civic_number, std_street, genus_name, species_name,
                   cultivar_name, common_name, on_street_block, on_street,
                   neighbourhood_name, street_side_name, height_range_id,
                   height_range, diameter, date_planted,
                   ST_X(geom) as longitude, ST_Y(geom) as latitude
            FROM trees WHERE tree_id = :id
        """), {"id": tree_id})
        row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Tree not found")

    return {
        "id": row.tree_id,
        "civic_number": row.civic_number,
        "std_street": row.std_street,
        "genus_name": row.genus_name,
        "species_name": row.species_name,
        "cultivar_name": row.cultivar_name,
        "common_name": row.common_name,
        "on_street_block": row.on_street_block,
        "on_street": row.on_street,
        "neighbourhood_name": row.neighbourhood_name,
        "street_side_name": row.street_side_name,
        "height_range_id": row.height_range_id,
        "height_range": row.height_range,
        "diameter": row.diameter,
        "date_planted": str(row.date_planted) if row.date_planted else None,
        "geometry": {
            "type": "Point",
            "coordinates": [row.longitude, row.latitude]
        }
    }


@app.get("/api/v1/species")
async def list_species():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT species_name FROM trees
            WHERE species_name IS NOT NULL
            ORDER BY species_name
        """))
        rows = result.fetchall()
    return {"species": [row.species_name for row in rows]}