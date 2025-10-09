import requests
import pandas as pd
from dotenv import load_dotenv

df = pd.read_csv('https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/public-trees/exports/csv', on_bad_lines='skip', sep=';')
print(df.head())