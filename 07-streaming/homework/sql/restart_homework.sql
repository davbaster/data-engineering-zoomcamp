DROP TABLE IF EXISTS q4_window_trips;
DROP TABLE IF EXISTS q5_session_trips_sink;
DROP TABLE IF EXISTS q6_hourly_tips_sink;

CREATE TABLE q4_window_trips (
    window_start TIMESTAMP,
    pulocationid INTEGER,
    num_trips BIGINT,
    PRIMARY KEY (window_start, pulocationid)
);

CREATE TABLE q5_session_trips_sink (
    session_start TIMESTAMP,
    session_end TIMESTAMP,
    pulocationid INTEGER,
    num_trips BIGINT,
    PRIMARY KEY (session_start, session_end, pulocationid)
);

CREATE TABLE q6_hourly_tips_sink (
    window_start TIMESTAMP,
    total_tip_amount DOUBLE PRECISION,
    PRIMARY KEY (window_start)
);
