import pandas as pd
import os
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

df = pd.read_csv('https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/public-trees/exports/csv', on_bad_lines='skip', sep=';')
df[["latitude", "longitude"]] = df["geo_point_2d"].str.split(",", expand=True).astype(float)
df = df.replace(r'^\s*$', np.nan, regex=True)

df = df.drop(columns=["geo_point_2d", "geom"])

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

with engine.begin() as conn:
    print("Wiping old data")
    conn.execute(text("TRUNCATE TABLE trees;"))
    
    print("Uploading new data")
    df.to_sql('trees_temp', conn, if_exists='replace', index=False, method='multi')
    
    print("Creating PostGIS geometries")
    conn.execute(text("""
        INSERT INTO trees 
        SELECT *, ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) as geom
        FROM trees_temp;
    """))
    


print("Data ingestion complete!")
