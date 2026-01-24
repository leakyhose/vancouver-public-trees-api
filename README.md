<img align="right" src="images/logo.png" alt="Vancouver Public Trees API Logo" width="200">

# Vancouver Public Trees API

A REST API for the City of Vancouver's public tree dataset, providing fast geospatial queries via PostGIS.

## Overview

This API exposes Vancouver's street tree inventory (~180,000 trees) through a clean REST interface. It supports standard filtering, pagination, and three types of spatial queries using PostGIS: bounding box, radius search, and nearest neighbor.

<br clear="right">

## Setup

```bash
pip install -r requirements.txt
```

Set `DATABASE_URL` in `.env` pointing to a PostgreSQL database with PostGIS enabled.

Run the data ingestion script to populate the database:
```bash
python ingenstion.py
```

Start the server:
```bash
uvicorn main:app --reload
```

## API Reference

Base URL: `/api/v1`

### Health

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness check |
| `GET /health/db` | Database connectivity check |

### Trees

#### List Trees
```
GET /trees
```

Query parameters:
- `limit` (int, default 50, max 100)
- `offset` (int, default 0)
- `species` - filter by species name
- `genus` - filter by genus name
- `common_name` - filter by common name
- `neighborhood` - filter by neighbourhood
- `min_height` / `max_height` - filter by height range ID
- `planted_after` / `planted_before` - filter by planting date (YYYY-MM-DD)

Response:
```json
{
  "metadata": { "limit": 50, "offset": 0, "total": 181000 },
  "data": [
    {
      "id": 123,
      "genus_name": "ACER",
      "species_name": "RUBRUM",
      "common_name": "RED MAPLE",
      "height_range_id": 2,
      "geometry": { "type": "Point", "coordinates": [-123.1, 49.2] }
    }
  ]
}
```

#### Get Single Tree
```
GET /trees/{tree_id}
```

Returns full tree details including civic address, diameter, and planting date.

#### Tree Count
```
GET /trees/count
```

Returns total number of trees in the database.

### Spatial Search

```
GET /trees/search
```

Three mutually exclusive modes:

**Bounding Box**
```
?bbox=minLon,minLat,maxLon,maxLat
```

**Radius Search**
```
?coordinates=lat,lon&radius=500
```
Radius in meters.

**Nearest Neighbor**
```
?nearest=lat,lon&count=10
```
Returns N closest trees (max 100).

All modes support `limit` parameter (default 50, max 100).

### Species

```
GET /species
```

Returns list of all distinct species in the dataset.

## Project Structure

```
main.py              # FastAPI app entry point
api/
  db.py              # Database connection
  health.py          # Health check endpoints
  trees.py           # Tree CRUD endpoints
  search.py          # Geospatial search endpoint
  species.py         # Species list endpoint
ingenstion.py        # Data ingestion script
```

## Data Source

Tree data sourced from [Vancouver Open Data Portal](https://opendata.vancouver.ca/explore/dataset/public-trees/).

## Tech Stack

- FastAPI
- PostgreSQL + PostGIS
- SQLAlchemy
