# Proces to create the schema (Bigquery dataset)

My project id is `project-a44b4f29-ed58-4b15-810.ny_taxy_2`

CREATE SCHEMA IF NOT EXISTS `project-a44b4f29-ed58-4b15-810.ny_taxy_2`
OPTIONS (
  location = "US"
);

# Then I needed to create my external table for yellow trip data
With external table BigQuery  does not load the data, so I only have to pay for queries.


CREATE OR REPLACE EXTERNAL TABLE all_trips.external_yellow_tripdata
OPTIONS (
  format = 'PARQUET',
  uris = [
    'gs://taxi-rides-yellow-ny-19-20/yellow_tripdata_2019-*.parquet',
    'gs://taxi-rides-yellow-ny-19-20/yellow_tripdata_2020-*.parquet'
  ]
);

# Next, I needed to copy the data from the external table into bigquery to create a regular (materialized) table
The regular table will be fully managed by BigQuery, that means the data will be in BigQuery, so I will need to pay for storage and queries.

CREATE OR REPLACE TABLE `project-a44b4f29-ed58-4b15-810.all_trips.yellow_tripdata`
AS
SELECT * EXCEPT (airport_fee)
FROM `project-a44b4f29-ed58-4b15-810.all_trips.external_yellow_tripdata`;


# Then I needed to create my external table for Green trip data
With external table BigQuery  does not load the data, so I only have to pay for queries.


CREATE OR REPLACE EXTERNAL TABLE all_trips.external_green_tripdata
OPTIONS (
  format = 'PARQUET',
  uris = [
    'gs://taxi-rides-green-ny-19-20/green_tripdata_2019-*.parquet',
    'gs://taxi-rides-green-ny-19-20/green_tripdata_2020-*.parquet'
  ]
);

# Next, I needed to copy the data from the external table into bigquery to create a regular (materialized) green table
The regular table will be fully managed by BigQuery, that means the data will be in BigQuery, so I will need to pay for storage and queries.

CREATE OR REPLACE TABLE `project-a44b4f29-ed58-4b15-810.all_trips.green_tripdata`
AS
SELECT * EXCEPT (airport_fee)
FROM `project-a44b4f29-ed58-4b15-810.all_trips.external_green_tripdata`;

# What is count of records for the 2024 Yellow Taxi Data?

65,623
840,402
**20,332,093
85,431,289

Query to the external table:

SELECT COUNT(*)
FROM `project-a44b4f29-ed58-4b15-810.nytaxi.external_yellow_tripdata`;

Query result:  20332093

Query to the BigQuery table:

SELECT COUNT(*)
FROM `project-a44b4f29-ed58-4b15-810.nytaxi.yellow_tripdata`;

Query result:  20332093


# Question 2. Data read estimation
Write a query to count the distinct number of PULocationIDs for the entire dataset on both the tables.

What is the estimated amount of data that will be read when this query is executed on the External Table and the Table?

18.82 MB for the External Table and 47.60 MB for the Materialized Table
**0 MB for the External Table and 155.12 MB for the Materialized Table
2.14 GB for the External Table and 0MB for the Materialized Table
0 MB for the External Table and 0MB for the Materialized Table

External table:
SELECT COUNT(DISTINCT PULocationID)
FROM `project-a44b4f29-ed58-4b15-810.nytaxi.external_yellow_tripdata`;

Not running, shows This query will process 0B when run.
After running, the real data (Bytes Processed) was 155.12MB 


BigQuery table:
SELECT COUNT(DISTINCT PULocationID)
FROM `project-a44b4f29-ed58-4b15-810.nytaxi.yellow_tripdata`;

Not running, shows This query will process 155.12 MB when run.
After running, the real data (Bytes Processed) was 155.12MB 

Query results: 262


# Question 3. Understanding columnar storage
Write a query to retrieve the PULocationID from the table (not the external table) in BigQuery. Now write a query to retrieve the PULocationID and DOLocationID on the same table.


Why are the estimated number of Bytes different?

**BigQuery is a columnar database, and it only scans the specific columns requested in the query. Querying two columns (PULocationID, DOLocationID) requires reading more data than querying one column (PULocationID), leading to a higher estimated number of bytes processed.

BigQuery duplicates data across multiple storage partitions, so selecting two columns instead of one requires scanning the table twice, doubling the estimated bytes processed.

BigQuery automatically caches the first queried column, so adding a second column increases processing time but does not affect the estimated bytes scanned.

When selecting multiple columns, BigQuery performs an implicit join operation between them, increasing the estimated bytes processed

First query:
SELECT PULocationID
FROM `project-a44b4f29-ed58-4b15-810.nytaxi.yellow_tripdata`;
Shows 155.12MB when run

Second query:
SELECT PULocationID, DOLocationID
FROM `project-a44b4f29-ed58-4b15-810.nytaxi.yellow_tripdata`;

It shows the query will process 310.24MB when run.


# Question 4. Counting zero fare trips
How many records have a fare_amount of 0?

128,210
546,578
20,188,016
**8,333

SELECT COUNT(*) AS zero_fare_trips
FROM `project-a44b4f29-ed58-4b15-810.nytaxi.yellow_tripdata` WHERE fare_amount = 0;

This query processed 155.12 MB when run.

# Question 5. Partitioning and clustering
What is the best strategy to make an optimized table in Big Query if your query will always filter based on tpep_dropoff_datetime and order the results by VendorID (Create a new table with this strategy)

**Partition by tpep_dropoff_datetime and Cluster on VendorID
Cluster on by tpep_dropoff_datetime and Cluster on VendorID
Cluster on tpep_dropoff_datetime Partition by VendorID
Partition by tpep_dropoff_datetime and Partition by VendorID

BigQuery query:

CREATE OR REPLACE TABLE nytaxi.optimized_trips
PARTITION BY DATE(tpep_dropoff_datetime)
CLUSTER BY VendorID AS
SELECT *
FROM `project-a44b4f29-ed58-4b15-810.nytaxi.yellow_tripdata`;

This query will process 2.72 GB when run.


# Question 6. Partition benefits
Write a query to retrieve the distinct VendorIDs between tpep_dropoff_datetime 2024-03-01 and 2024-03-15 (inclusive)

Use the materialized table you created earlier in your from clause and note the estimated bytes. Now change the table in the from clause to the partitioned table you created for question 5 and note the estimated bytes processed. What are these values?

Choose the answer which most closely matches.

12.47 MB for non-partitioned table and 326.42 MB for the partitioned table
**310.24 MB for non-partitioned table and 26.84 MB for the partitioned table
5.87 MB for non-partitioned table and 0 MB for the partitioned table
310.31 MB for non-partitioned table and 285.64 MB for the partitioned table

Query in materialized nytaxi.yellow_tripdata:

SELECT DISTINCT VendorID
FROM `project-a44b4f29-ed58-4b15-810.nytaxi.yellow_tripdata`
WHERE tpep_dropoff_datetime BETWEEN '2024-03-01' AND '2024-03-15';

This query will process 310.24 MB when run.


Query in nytaxi.optimized_trips

SELECT DISTINCT VendorID
FROM nytaxi.optimized_trips
WHERE tpep_dropoff_datetime BETWEEN '2024-03-01' AND '2024-03-15';

This query will process 26.84 MB when run.


# Question 7. External table storage
Where is the data stored in the External Table you created?

Big Query
Container Registry
** GCP Bucket
Big Table

# Question 8. Clustering best practices
It is best practice in Big Query to always cluster your data:

True
**False

# Question 9. Understanding table scans
No Points: Write a SELECT count(*) query FROM the materialized table you created. How many bytes does it estimate will be read? Why?

SELECT count(*)
FROM `project-a44b4f29-ed58-4b15-810.nytaxi.yellow_tripdata`

0B
Because BigQuery must scan all the columns in the dataset. It does not mantain a metadata with the information of the size of table. 