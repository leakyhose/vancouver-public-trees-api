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
        INSERT INTO trees (tree_id, civic_number, std_street, genus_name, species_name, 
                          cultivar_name, common_name, on_street_block, on_street, 
                          neighbourhood_name, street_side_name, height_range_id, 
                          height_range, diameter, date_planted, geom)
        SELECT tree_id, civic_number, std_street, genus_name, species_name, 
               cultivar_name, common_name, on_street_block, on_street, 
               neighbourhood_name, street_side_name, height_range_id, 
               height_range, diameter, date_planted::DATE, 
               ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) as geom
        FROM trees_temp;
    """))
    
    print("Creating GiST index on geometry column")
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS trees_geom_gist
        ON trees
        USING GIST (geom);
    """))
    
    conn.execute(text("DROP TABLE trees_temp;"))
    
    result = conn.execute(text("SELECT COUNT(*) FROM trees;"))
    count = result.fetchone()[0]
    print(f"Successfully uploaded {count} records to trees table")
    


print("Data ingestion complete!")
