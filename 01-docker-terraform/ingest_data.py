#!/usr/bin/env python
# coding: utf-8

from sqlalchemy import create_engine
import pandas as pd
import time


engine = create_engine('postgresql://postgres:postgres@localhost:5433/ny_taxi')


# --- Yellow Taxi Data (short file) ---

# Read a sample of the data
df = pd.read_csv('./taxi_zone_lookup.csv')


# Display first rows csv
df.head()

# Check data types
df.dtypes

# Check data shape
df.shape


df.to_sql(name='yellow_taxi', con=engine, if_exists='replace', index=False, chunksize=1000)


# # --- Green Taxi Data (Large file, using chunks) ---


# Read and Ingest
df_green = pd.read_parquet('green_tripdata_2025-11.parquet')


# Display first rows csv
df_green.head()


# Check data types
df_green.dtypes

# Check data shape
df_green.shape

# We use lpep_pickup_datetime to ensure the schema is correct in Postgres
df_green.lpep_pickup_datetime = pd.to_datetime(df_green.lpep_pickup_datetime)
df_green.lpep_dropoff_datetime = pd.to_datetime(df_green.lpep_dropoff_datetime)


print(f"Ingesting taxi data ({len(df_green)} rows) in chunks...")

start_time = time.time()

# if_exists='replace' for the first chunk to create the table
# chunksize=100000 tells pandas how many rows to send at once
df_green.to_sql(name='green_taxi', con=engine, if_exists='replace', index=False, chunksize=10000)

end_time = time.time()
print(f"Finished! Ingestion took {end_time - start_time:.2f} seconds.")

