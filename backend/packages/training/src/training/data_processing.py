import pandas as pd

from training.__generated__ import gtfs_realtime_pb2 as gtfs_rt
from training.static_data import StaticData


def feed_entity_to_vehicle_position_dict(
    feed_message: gtfs_rt.FeedMessage, entity: gtfs_rt.FeedEntity) -> dict:
    return {
        "id": entity.id,
        "trip_id": entity.vehicle.trip.trip_id,
        "timestamp": feed_message.header.timestamp,
        "vehicle_latitude": entity.vehicle.position.latitude,
        "vehicle_longitude": entity.vehicle.position.longitude,
        "vehicle_bearing": entity.vehicle.position.bearing,
        "vehicle_odometer": entity.vehicle.position.odometer,
        "vehicle_speed": entity.vehicle.position.speed,
        "vehicle_congestion_level": entity.vehicle.congestion_level,
        "vehicle_occupancy_percentage": entity.vehicle.occupancy_percentage,
        "vehicle_occupancy_status": entity.vehicle.occupancy_status,
        "stop_id": entity.vehicle.stop_id,
        "current_status": entity.vehicle.current_status,
        "current_stop_sequence": entity.vehicle.current_stop_sequence,
    }

def feed_message_to_vehicle_position_dataframe(feed_message: gtfs_rt.FeedMessage) -> pd.DataFrame:
    # VehicleStopStatus = gtfs_rt.VehiclePosition.VehicleStopStatus
    # vehicle_stop_type = pd.CategoricalDtype([
    #     VehicleStopStatus.INCOMING_AT,
    #     VehicleStopStatus.STOPPED_AT,
    #     VehicleStopStatus.IN_TRANSIT_TO,
    # ])
        
    df = pd.DataFrame([feed_entity_to_vehicle_position_dict(feed_message, e) for e in feed_message.entity])

    df["id"] = df["id"].astype(pd.Int64Dtype())
    df["trip_id"] = df["trip_id"].replace("", pd.NA).astype(pd.StringDtype())

    return df

def feed_entity_to_trip_update_dict(feed_message: gtfs_rt.FeedMessage, entity: gtfs_rt.FeedEntity
) -> dict:
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
                "departure_time": stu.departure.time
                if stu.HasField("departure")
                else None,
                "schedule_relationship": stu.schedule_relationship,
            }
            for stu in entity.trip_update.stop_time_update
        ],
        "timestamp": feed_message.header.timestamp,
    }


def feed_message_to_trip_update_dataframe(
    feed_message: gtfs_rt.FeedMessage,
) -> pd.DataFrame:
    df = pd.DataFrame(
        [feed_entity_to_trip_update_dict(feed_message, e) for e in feed_message.entity]
    )

    df["id"] = df["id"].astype(pd.Int64Dtype())
    df["trip_id"] = df["trip_id"].replace("", pd.NA).astype(pd.StringDtype())
    df["vehicle_id"] = df["vehicle_id"].replace("", pd.NA).astype(pd.Int64Dtype())

    return df


def join_static_data_on_rt_vehicle_positions(static_data: StaticData, gtfs_feed_df: pd.DataFrame) -> pd.DataFrame:
    gtfs_feed_df = gtfs_feed_df.join(static_data.trips, on="trip_id", how="left", rsuffix="_trip")
    gtfs_feed_df = gtfs_feed_df.join(static_data.routes, on="route_id", how="left", rsuffix="_route")
  
    return gtfs_feed_df

def join_static_data_on_rt_trip_updates(
    static_data: StaticData, gtfs_feed_df: pd.DataFrame
) -> pd.DataFrame:
    gtfs_feed_df = gtfs_feed_df.join(
        static_data.trips, on="trip_id", how="left", rsuffix="_trip"
    )
    gtfs_feed_df = gtfs_feed_df.join(
        static_data.routes, on="route_id", how="left", rsuffix="_route"
    )

    return gtfs_feed_df


def explode_to_stops_with_join_static(
    static_data: StaticData, gtfs_feed_df: pd.DataFrame
) -> pd.DataFrame:
    # Flatten with stop time updates exploded into separate rows
    df_exploded = gtfs_feed_df.explode("stop_time_updates").reset_index(drop=True)

    # Extract stop time update details into separate columns
    df_exploded["stop_sequence"] = df_exploded["stop_time_updates"].apply(
        lambda x: x["stop_sequence"]
    )
    df_exploded["stop_id"] = df_exploded["stop_time_updates"].apply(
        lambda x: x["stop_id"]
    )

    # Raw GTFS-RT times are Unix epoch seconds or None
    df_exploded["arrival_time"] = (
        df_exploded["stop_time_updates"]
        .apply(lambda x: x["arrival_time"])
        .astype("Int64")
    )
    df_exploded["departure_time"] = (
        df_exploded["stop_time_updates"]
        .apply(lambda x: x["departure_time"])
        .astype("Int64")
    )

    df_exploded["stop_time_schedule_relationship"] = df_exploded[
        "stop_time_updates"
    ].apply(lambda x: x["schedule_relationship"])
    df_exploded = df_exploded.drop(columns=["stop_time_updates"])

    df_exploded["stop_id"] = (
        df_exploded["stop_id"]
        .map(lambda x: pd.NA if x == "" else x)
        .astype(pd.StringDtype())
    )

    # Convert RT times to seconds since service-day midnight
    timezone_offset = pd.Timedelta(hours=-2)
    service_date = pd.to_datetime(
        df_exploded["start_date"], format="%Y%m%d", errors="coerce"
    )
    service_midnight = service_date + timezone_offset

    def to_service_seconds(epoch_series: pd.Series) -> pd.Series:
        # epoch_series is Int64 seconds since Unix epoch; <NA> is allowed
        dt = pd.to_datetime(epoch_series, unit="s", errors="coerce", cache=False)
        seconds = (dt - service_midnight).dt.total_seconds()
        return seconds.round().astype("Int64")

    df_exploded["arrival_time"] = to_service_seconds(df_exploded["arrival_time"])
    df_exploded["departure_time"] = to_service_seconds(df_exploded["departure_time"])

    df_exploded = df_exploded.set_index(["trip_id", "stop_sequence"])

    df_exploded_with_stop_times = df_exploded.join(
        static_data.stop_times,
        on=["trip_id", "stop_sequence"],
        how="left",
        rsuffix="_planned",
    )

    df_exploded_with_stop_times["arrival_time_late"] = (
        df_exploded_with_stop_times["arrival_time"]
        - df_exploded_with_stop_times["arrival_time_planned"]
    ).astype("Int64")
    df_exploded_with_stop_times["departure_time_late"] = (
        df_exploded_with_stop_times["departure_time"]
        - df_exploded_with_stop_times["departure_time_planned"]
    ).astype("Int64")

    return df_exploded_with_stop_times
