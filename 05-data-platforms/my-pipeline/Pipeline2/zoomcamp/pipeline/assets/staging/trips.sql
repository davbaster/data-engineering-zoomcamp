/* @bruin

name: staging.trips

type: duckdb.sql

depends:
  - ingestion.trips
  - ingestion.payment_lookup

materialization:
  type: table
  strategy: time_interval
  incremental_key: pickup_datetime
  time_granularity: timestamp

columns:
  - name: trip_id
    type: string
    description: Unique trip identifier
    primary_key: true
    nullable: false
    checks:
      - name: not_null
  - name: vendor_id
    type: integer
    description: Vendor identifier
  - name: pickup_datetime
    type: timestamp
    description: Pickup time
    primary_key: true
    nullable: false
    checks:
      - name: not_null
  - name: dropoff_datetime
    type: timestamp
    description: Dropoff time
    nullable: false
    checks:
      - name: not_null
  - name: passenger_count
    type: integer
    description: Number of passengers
    checks:
      - name: not_null
  - name: trip_distance
    type: float
    description: Trip distance in miles
  - name: pickup_location_id
    type: integer
    description: Pickup location ID
  - name: dropoff_location_id
    type: integer
    description: Dropoff location ID
  - name: payment_type_id
    type: integer
    description: Payment type ID
    checks:
      - name: not_null
  - name: payment_type_name
    type: string
    description: Payment type name (from lookup)
  - name: fare_amount
    type: float
    description: Fare amount
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
    description: Congestion surcharge
  - name: airport_fee
    type: float
    description: Airport fee
  - name: taxi_type
    type: string
    description: Type of taxi
    checks:
      - name: not_null

custom_checks:
  - name: no_duplicate_trips
    description: Each composite key should appear only once (after deduplication)
    query: |
      SELECT COUNT(*) FROM (
        SELECT trip_id, pickup_datetime, pickup_location_id, dropoff_location_id, fare_amount
        FROM staging.trips
        GROUP BY 1, 2, 3, 4, 5
        HAVING COUNT(*) > 1
      )
    value: 0
    blocking: false

@bruin */

WITH raw_trips AS (
  SELECT
    trip_id,
    vendor_id,
    pickup_datetime,
    dropoff_datetime,
    passenger_count,
    trip_distance,
    pickup_location_id,
    dropoff_location_id,
    payment_type_id,
    fare_amount,
    mta_tax,
    tip_amount,
    tolls_amount,
    total_amount,
    congestion_surcharge,
    airport_fee,
    taxi_type
  FROM ingestion.trips
  WHERE pickup_datetime >= '{{ start_datetime }}'
    AND pickup_datetime < '{{ end_datetime }}'
),

-- Deduplicate using ROW_NUMBER on composite key
deduped_trips AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY trip_id, pickup_datetime, pickup_location_id, dropoff_location_id, fare_amount
      ORDER BY pickup_datetime DESC
    ) AS rn
  FROM raw_trips
),

-- Join with payment lookup
enriched_trips AS (
  SELECT
    dt.trip_id,
    dt.vendor_id,
    dt.pickup_datetime,
    dt.dropoff_datetime,
    dt.passenger_count,
    dt.trip_distance,
    dt.pickup_location_id,
    dt.dropoff_location_id,
    dt.payment_type_id,
    COALESCE(pl.payment_type_name, 'unknown') AS payment_type_name,
    dt.fare_amount,
    dt.mta_tax,
    dt.tip_amount,
    dt.tolls_amount,
    dt.total_amount,
    dt.congestion_surcharge,
    dt.airport_fee,
    dt.taxi_type
  FROM deduped_trips dt
  LEFT JOIN ingestion.payment_lookup pl
    ON dt.payment_type_id = pl.payment_type_id
  WHERE dt.rn = 1
)

SELECT * FROM enriched_trips

