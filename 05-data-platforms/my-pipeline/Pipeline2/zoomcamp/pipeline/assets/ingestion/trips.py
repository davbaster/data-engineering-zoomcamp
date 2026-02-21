"""@bruin

name: ingestion.trips

type: python

image: python:3.11

connection: duckdb-default

materialization:
  type: table
  strategy: append

columns:
  - name: trip_id
    type: string
    description: Unique trip identifier (combination of vendor and trip fields)
    checks:
      - name: not_null
  - name: vendor_id
    type: integer
    description: Vendor ID (1=Yellow Cab, 2=Medallion Limo, etc.)
  - name: pickup_datetime
    type: timestamp
    description: When the trip started
    checks:
      - name: not_null
  - name: dropoff_datetime
    type: timestamp
    description: When the trip ended
    checks:
      - name: not_null
  - name: passenger_count
    type: integer
    description: Number of passengers
    checks:
      - name: not_null
  - name: trip_distance
    type: float
    description: Distance in miles
  - name: pickup_location_id
    type: integer
    description: Location ID for pickup
  - name: dropoff_location_id
    type: integer
    description: Location ID for dropoff
  - name: payment_type_id
    type: integer
    description: Payment method ID
    checks:
      - name: not_null
  - name: fare_amount
    type: float
    description: Base fare amount in USD
  - name: mta_tax
    type: float
    description: MTA tax
  - name: tip_amount
    type: float
    description: Tip amount
  - name: tolls_amount
    type: float
    description: Toll charges
  - name: total_amount
    type: float
    description: Total amount charged
  - name: congestion_surcharge
    type: float
    description: Congestion surcharge (if applicable)
  - name: airport_fee
    type: float
    description: Airport fee (if applicable)
  - name: taxi_type
    type: string
    description: Type of taxi (yellow, green, etc.)
    checks:
      - name: not_null

custom_checks:
  - name: pickup_before_dropoff
    description: Pickup time should be before dropoff time
    query: |
      SELECT COUNT(*) FROM ingestion.trips
      WHERE pickup_datetime > dropoff_datetime
    value: 0
    blocking: false

@bruin"""

import json
import os
from datetime import datetime, timedelta
import pandas as pd
import requests
from dateutil.relativedelta import relativedelta


def materialize() -> list[dict]:
    """Fetch NYC taxi trip data from TLC public endpoint."""
    
    # Parse environment variables for Bruin context
    start_date = os.getenv("BRUIN_START_DATE", "2022-01-01")
    end_date = os.getenv("BRUIN_END_DATE", "2022-02-01")
    
    # Parse taxi_types variable from JSON
    bruin_vars = os.getenv("BRUIN_VARS", "{}")
    variables = json.loads(bruin_vars)
    taxi_types = variables.get("taxi_types", ["yellow", "green"])
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Base URL for NYC TLC taxi data
    base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/"
    
    all_trips = []
    current_date = start
    
    # Iterate through each month in the date range
    while current_date < end:
        year = current_date.year
        month = current_date.month
        
        # Fetch data for each taxi type
        for taxi_type in taxi_types:
            filename = f"{taxi_type}_tripdata_{year:04d}-{month:02d}.parquet"
            url = base_url + filename
            year_month_str = f"{year:04d}{month:02d}"
            
            try:
                print(f"Fetching {url}...")
                # Read parquet file directly from URL
                df = pd.read_parquet(url)
                
                # Add taxi_type column to identify the source
                df["taxi_type"] = taxi_type
                
                # Create a trip_id from available identifiers
                # Use a combination of time and location to create a unique-enough ID
                df["trip_id"] = (
                    df.index.astype(str) + "_" +
                    year_month_str + "_" +
                    taxi_type
                )
                
                all_trips.append(df)
                print(f"  ✓ Loaded {len(df)} records from {filename}")
                
            except Exception as e:
                print(f"  ✗ Failed to fetch {filename}: {e}")
        
        # Move to next month
        current_date += relativedelta(months=1)
    
    if not all_trips:
        print("No data fetched. Check date range and internet connectivity.")
        return []
    
    # Combine all dataframes
    combined_df = pd.concat(all_trips, ignore_index=True)
    
    # Standardize column names to lowercase with underscores
    combined_df.columns = combined_df.columns.str.lower().str.replace(" ", "_")
    
    # Ensure we have the essential columns needed downstream
    # Map common column names from different taxi types
    column_mapping = {
        "tpep_pickup_datetime": "pickup_datetime",
        "tpep_dropoff_datetime": "dropoff_datetime",
        "lpep_pickup_datetime": "pickup_datetime",
        "lpep_dropoff_datetime": "dropoff_datetime",
        "pulocationid": "pickup_location_id",
        "dolocationid": "dropoff_location_id",
        "puLocationID": "pickup_location_id",
        "doLocationID": "dropoff_location_id",
    }
    
    combined_df = combined_df.rename(columns=column_mapping, errors="ignore")
    
    # Convert datetime columns to proper timestamp format
    for col in ["pickup_datetime", "dropoff_datetime"]:
        if col in combined_df.columns:
            combined_df[col] = pd.to_datetime(combined_df[col])
    
    # Ensure numeric columns are properly typed
    numeric_cols = [
        "passenger_count", "trip_distance", "pickup_location_id",
        "dropoff_location_id", "payment_type", "fare_amount",
        "mta_tax", "tip_amount", "tolls_amount", "total_amount",
        "congestion_surcharge", "airport_fee"
    ]
    
    for col in numeric_cols:
        if col in combined_df.columns:
            combined_df[col] = pd.to_numeric(combined_df[col], errors="coerce")
    
    # Rename payment_type to payment_type_id for consistency
    if "payment_type" in combined_df.columns:
        combined_df = combined_df.rename(columns={"payment_type": "payment_type_id"})
    
    # Ensure vendor_id exists
    if "vendorid" in combined_df.columns:
        combined_df = combined_df.rename(columns={"vendorid": "vendor_id"})
    
    print(f"\nTotal records ingested: {len(combined_df)}")
    print(f"Date range: {combined_df['pickup_datetime'].min()} to {combined_df['pickup_datetime'].max()}")
    
    # Return as list of dictionaries for Bruin materialization
    return combined_df.to_dict("records")


