import json
import dataclasses
from dataclasses import dataclass
import pandas as pd



@dataclass
class Ride:
    PULocationID: int
    DOLocationID: int
    trip_distance: float
    total_amount: float
    lpep_pickup_datetime: str  # Using string for simplicity in serialization/deserialization. Format: 'yyyy-MM-dd HH:mm:ss'
    lpep_dropoff_datetime: str  #
    passenger_count: int
    tip_amount: float


def ride_from_row(row):
    passenger_count = row['passenger_count']
    if pd.isna(passenger_count):
        passenger_count = 0

    return Ride(
        PULocationID=int(row['PULocationID']),
        DOLocationID=int(row['DOLocationID']),
        trip_distance=float(row['trip_distance']),
        total_amount=float(row['total_amount']),
        lpep_pickup_datetime=row['lpep_pickup_datetime'].strftime('%Y-%m-%d %H:%M:%S'),
        lpep_dropoff_datetime=row['lpep_dropoff_datetime'].strftime('%Y-%m-%d %H:%M:%S'),
        passenger_count=int(passenger_count),
        tip_amount=float(row['tip_amount']),
    )


def ride_serializer(ride):
    ride_dict = dataclasses.asdict(ride)
    ride_json = json.dumps(ride_dict).encode('utf-8')
    return ride_json

def ride_deserializer(data):
    json_str = data.decode('utf-8')
    ride_dict = json.loads(json_str)
    return Ride(**ride_dict)