import json

from kafka import KafkaConsumer


TOPIC_NAME = "green-trips"


def main() -> None:
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=["localhost:9092"],
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=5000,
        value_deserializer=lambda message: json.loads(message.decode("utf-8")),
    )

    trips_over_5km = 0
    total_messages = 0

    for message in consumer:
        total_messages += 1
        if float(message.value["trip_distance"]) > 5.0:
            trips_over_5km += 1

    consumer.close()

    print(f"Total messages read: {total_messages}")
    print(f"Trips with trip_distance > 5.0: {trips_over_5km}")


if __name__ == "__main__":
    main()
