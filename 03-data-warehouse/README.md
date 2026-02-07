# Proces to create the schema (Bigquery dataset)

My project id is `project-a44b4f29-ed58-4b15-810.nytaxi`

CREATE SCHEMA IF NOT EXISTS `project-a44b4f29-ed58-4b15-810.nytaxi`
OPTIONS (
  location = "US"
);

# Then I needed to create my external table
With external table BigQuery  does not load the data, so I only have to pay for queries.

CREATE OR REPLACE EXTERNAL TABLE `project-a44b4f29-ed58-4b15-810.nytaxi.external_yellow_tripdata`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://taxi-rides-ny-2024/*.parquet']
);

# Next, I needed to copy the data from the external table into bigquery to create a regular (materialized) table
The regular table will be fully managed by BigQuery, that means the data will be in BigQuery, so I will need to pay for storage and queries.

CREATE OR REPLACE TABLE `project-a44b4f29-ed58-4b15-810.nytaxi.yellow_tripdata`
AS
SELECT *
FROM `project-a44b4f29-ed58-4b15-810.nytaxi.external_yellow_tripdata`;s

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


#Question 3. Understanding columnar storage
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


#