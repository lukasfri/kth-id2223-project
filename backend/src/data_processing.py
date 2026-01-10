import pandas as pd

from __generated__ import gtfs_realtime_pb2
from static import StaticData

def feed_entity_to_dict(feed_message: gtfs_realtime_pb2.FeedMessage, entity: gtfs_realtime_pb2.FeedEntity) -> dict:
    return {
        "id": entity.id,
        "trip_id": entity.trip_update.trip.trip_id,
        "start_date": entity.trip_update.trip.start_date,
        "schedule_relationship": entity.trip_update.trip.schedule_relationship,
        "vehicle_id": entity.trip_update.vehicle.id,
        "stop_time_updates": [
            {
                "stop_sequence": stu.stop_sequence,
                "stop_id": stu.stop_id,
                "arrival_time": stu.arrival.time if stu.HasField("arrival") else None,
                "departure_time": stu.departure.time if stu.HasField("departure") else None,
                "schedule_relationship": stu.schedule_relationship,
            }
            for stu in entity.trip_update.stop_time_update
        ],
        "timestamp": feed_message.header.timestamp,
    }

def feed_message_to_dataframe(feed_message: gtfs_realtime_pb2.FeedMessage) -> pd.DataFrame:
    df = pd.DataFrame([feed_entity_to_dict(feed_message, e) for e in feed_message.entity])

    df["id"] = df["id"].astype(pd.Int64Dtype())
    df["trip_id"] = df["trip_id"].replace("", pd.NA).astype(pd.StringDtype())
    df["vehicle_id"] = df["vehicle_id"].replace("", pd.NA).astype(pd.Int64Dtype())

    return df

def join_static_data_on_rt(static_data: StaticData, gtfs_feed_df: pd.DataFrame) -> pd.DataFrame:
    gtfs_feed_df = gtfs_feed_df.join(static_data.trips, on="trip_id", how="left", rsuffix="_trip")
    gtfs_feed_df = gtfs_feed_df.join(static_data.routes, on="route_id", how="left", rsuffix="_route")
  
    return gtfs_feed_df

def explode_to_stops_with_join_static(static_data: StaticData, gtfs_feed_df: pd.DataFrame) -> pd.DataFrame:
    # Flatten with stop time updates exploded into separate rows
    df_exploded = gtfs_feed_df.explode("stop_time_updates").reset_index(drop=True)

    # Extract stop time update details into separate columns
    df_exploded["stop_sequence"] = df_exploded["stop_time_updates"].apply(lambda x: x["stop_sequence"])
    df_exploded["stop_id"] = df_exploded["stop_time_updates"].apply(lambda x: x["stop_id"])
    df_exploded["arrival_time"] = df_exploded["stop_time_updates"].apply(lambda x: x["arrival_time"]).astype("Int64")
    df_exploded["arrival_time"] = pd.to_datetime(df_exploded["arrival_time"], unit='s')
    df_exploded["departure_time"] = df_exploded["stop_time_updates"].apply(lambda x: x["departure_time"]).astype("Int64")
    df_exploded["departure_time"] = pd.to_datetime(df_exploded["departure_time"], unit='s', cache=False)
    df_exploded["stop_time_schedule_relationship"] = df_exploded["stop_time_updates"].apply(lambda x: x["schedule_relationship"])
    df_exploded = df_exploded.drop(columns=["stop_time_updates"])

    df_exploded["stop_id"] = df_exploded["stop_id"].map(lambda x: pd.NA if x == "" else x).astype(pd.StringDtype())

    df_exploded = df_exploded.set_index(["trip_id", "stop_sequence"])

    df_exploded_with_stop_times = df_exploded.join(static_data.stop_times, on=["trip_id", "stop_sequence"], how="left", rsuffix="_planned")
  
    df_exploded_with_stop_times["arrival_time_late"] = (df_exploded_with_stop_times["arrival_time"] - df_exploded_with_stop_times["arrival_time_planned"])
    df_exploded_with_stop_times["departure_time_late"] = (df_exploded_with_stop_times["departure_time"] - df_exploded_with_stop_times["departure_time_planned"])

    return df_exploded_with_stop_times

