from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import EnvironmentSettings, StreamTableEnvironment


SOURCE_TABLE = "green_trips"
SINK_TABLE = "q4_window_trips"


def create_source_kafka_table(t_env: StreamTableEnvironment) -> str:
    source_ddl = f"""
        CREATE TABLE {SOURCE_TABLE} (
            PULocationID INT,
            DOLocationID INT,
            trip_distance DOUBLE,
            total_amount DOUBLE,
            lpep_pickup_datetime VARCHAR,
            lpep_dropoff_datetime VARCHAR,
            passenger_count INT,
            tip_amount DOUBLE,
            -- Current repo data uses epoch-millisecond strings.
            -- If you switch the producer to 'yyyy-MM-dd HH:mm:ss' strings,
            -- replace this with:
            event_timestamp AS TO_TIMESTAMP(lpep_pickup_datetime, 'yyyy-MM-dd HH:mm:ss'),
            WATERMARK FOR event_timestamp AS event_timestamp - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'properties.bootstrap.servers' = 'redpanda:29092',
            'topic' = 'green-trips',
            'scan.startup.mode' = 'earliest-offset',
            'properties.auto.offset.reset' = 'earliest',
            'format' = 'json'
        )
    """
    t_env.execute_sql(source_ddl)
    return SOURCE_TABLE


def create_sink_postgres_table(t_env: StreamTableEnvironment) -> str:
    sink_ddl = f"""
        CREATE TABLE {SINK_TABLE} (
            window_start TIMESTAMP(3),
            PULocationID INT,
            num_trips BIGINT,
            PRIMARY KEY (window_start, PULocationID) NOT ENFORCED
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:postgresql://postgres:5432/postgres',
            'table-name' = '{SINK_TABLE}',
            'username' = 'postgres',
            'password' = 'postgres',
            'driver' = 'org.postgresql.Driver'
        )
    """
    t_env.execute_sql(sink_ddl)
    return SINK_TABLE


def run() -> None:
    env = StreamExecutionEnvironment.get_execution_environment()
    env.enable_checkpointing(10 * 1000)
    env.set_parallelism(1)

    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)

    source_table = create_source_kafka_table(t_env)
    sink_table = create_sink_postgres_table(t_env)

    t_env.execute_sql(
        f"""
        INSERT INTO {sink_table}
        SELECT
            window_start,
            PULocationID,
            COUNT(*) AS num_trips
        FROM TABLE(
            TUMBLE(TABLE {source_table}, DESCRIPTOR(event_timestamp), INTERVAL '5' MINUTES)
        )
        GROUP BY window_start, PULocationID
        """
    ).wait()


if __name__ == "__main__":
    run()
