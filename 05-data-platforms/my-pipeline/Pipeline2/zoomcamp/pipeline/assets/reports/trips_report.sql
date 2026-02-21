/* @bruin

name: reports.trips_report

type: duckdb.sql

depends:
  - staging.trips

materialization:
  type: table
  strategy: time_interval
  incremental_key: pickup_date
  time_granularity: date

columns:
  - name: pickup_date
    type: date
    description: Date of the trip pickup
    primary_key: true
    checks:
      - name: not_null
  - name: taxi_type
    type: string
    description: Type of taxi (yellow, green)
    primary_key: true
    checks:
      - name: not_null
  - name: payment_type_name
    type: string
    description: Payment type
    primary_key: true
    checks:
      - name: not_null
  - name: total_trips
    type: bigint
    description: Number of trips
    checks:
      - name: not_null
  - name: total_distance
    type: float
    description: Total distance in miles
  - name: total_fare
    type: float
    description: Total fare amount in USD
  - name: total_tips
    type: float
    description: Total tips in USD
  - name: total_tolls
    type: float
    description: Total tolls in USD
  - name: average_trip_distance
    type: float
    description: Average trip distance
  - name: average_fare
    type: float
    description: Average fare per trip
  - name: average_tip
    type: float
    description: Average tip per trip

custom_checks:
  - name: trip_count_positive
    description: Must have at least one trip per record
    query: |
      SELECT COUNT(*) FROM reports.trips_report
      WHERE total_trips <= 0
    value: 0
    blocking: false

@bruin */

SELECT
  CAST(CAST(t.pickup_datetime AS DATE) AS DATE) AS pickup_date,
  t.taxi_type,
  t.payment_type_name,
  COUNT(*) AS total_trips,
  SUM(t.trip_distance) AS total_distance,
  SUM(t.fare_amount) AS total_fare,
  SUM(t.tip_amount) AS total_tips,
  SUM(t.tolls_amount) AS total_tolls,
  AVG(t.trip_distance) AS average_trip_distance,
  AVG(t.fare_amount) AS average_fare,
  AVG(t.tip_amount) AS average_tip
FROM staging.trips t
WHERE CAST(CAST(t.pickup_datetime AS DATE) AS DATE) >= '{{ start_datetime }}'::DATE
  AND CAST(CAST(t.pickup_datetime AS DATE) AS DATE) < '{{ end_datetime }}'::DATE
GROUP BY
  CAST(CAST(t.pickup_datetime AS DATE) AS DATE),
  t.taxi_type,
  t.payment_type_name
ORDER BY
  pickup_date DESC,
  taxi_type,
  payment_type_name

