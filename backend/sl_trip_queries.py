from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import gtfs_kit as gk
import pandas as pd
from zoneinfo import ZoneInfo

import build.gen.gtfs_realtime_pb2 as gtfs_realtime_pb2


DEFAULT_TZ = "Europe/Stockholm"


@dataclass
class TripTimepointInfo:
    """Combined planned/actual arrival and vehicle position for one trip.

    All datetimes are timezone-aware in the provided timezone (default
    Europe/Stockholm).
    """

    route_id: str
    trip_id: str
    from_stop_id: str
    to_stop_id: str

    planned_arrival: Optional[datetime]
    actual_arrival: Optional[datetime]

    vehicle_position_time: Optional[datetime]
    vehicle_latitude: Optional[float]
    vehicle_longitude: Optional[float]


def load_static_feed(zip_path: str | Path) -> gk.Feed:
    """Load a static GTFS feed from a .zip file using gtfs_kit.

    Parameters
    ----------
    zip_path:
        Path to a zip file downloaded from the KoDa GTFS-static API,
        e.g. './data/sl_2024-06-15.zip'.

    Returns
    -------
    gk.Feed
        Parsed static feed.
    """
    path = Path(zip_path)
    if not path.is_file():
        raise FileNotFoundError(f"Static GTFS zip not found: {path}")
    # dist_units does not matter for these queries; use a reasonable default.
    return gk.read_feed(str(path), dist_units="km")


def load_gtfs_rt_feed(pb_path: str | Path) -> gtfs_realtime_pb2.FeedMessage:
    """Load a GTFS-RT protobuf file (.pb) into a FeedMessage.

    Parameters
    ----------
    pb_path:
        Path to a protobuf file extracted from KoDa GTFS-RT archives,
        e.g. './data/data-tmp-rt/sl/TripUpdates/...pb'.

    Returns
    -------
    gtfs_realtime_pb2.FeedMessage
    """
    path = Path(pb_path)
    if not path.is_file():
        raise FileNotFoundError(f"GTFS-RT protobuf file not found: {path}")

    with path.open("rb") as f:
        data = f.read()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(data)
    return feed


def gtfs_time_to_datetime(
    service_date: date,
    time_str: str,
    tz: ZoneInfo,
) -> datetime:
    """Convert a GTFS HH:MM:SS string (possibly >= 24h) to a datetime.

    GTFS allows times like '25:10:00' to represent trips after midnight
    on the following calendar day.
    """
    h_str, m_str, s_str = time_str.split(":")
    hours = int(h_str)
    minutes = int(m_str)
    seconds = int(s_str)

    day_offset, hour_in_day = divmod(hours, 24)
    base_dt = datetime.combine(
        service_date,
        time(hour_in_day, minutes, seconds),
        tzinfo=tz,
    )
    return base_dt + timedelta(days=day_offset)


# ---------------------------------------------------------------------------
# Route and stop name / ID helpers
# ---------------------------------------------------------------------------


def route_short_name_to_ids(feed: gk.Feed, route_short_name: str) -> List[str]:
    """Map a route_short_name (e.g. line number) to route_id(s).

    Returns all matching route_ids. Multiple matches are possible if
    the same short name is reused.
    """
    routes = feed.routes
    if "route_short_name" not in routes.columns:
        return []

    mask = routes["route_short_name"] == route_short_name
    matches = routes.loc[mask, "route_id"].dropna().unique()
    return sorted(str(value) for value in matches)


def route_id_to_short_name(feed: gk.Feed, route_id: str) -> Optional[str]:
    """Map a route_id back to route_short_name.

    Returns the first non-null short name if multiple rows match.
    """
    routes = feed.routes
    mask = routes["route_id"] == route_id
    subset = routes.loc[mask]

    if subset.empty or "route_short_name" not in subset.columns:
        return None

    # Take the first non-null value if available.
    values = subset["route_short_name"].dropna()
    if values.empty:
        return None
    return str(values.iloc[0])


def route_long_name_to_ids(feed: gk.Feed, route_long_name: str) -> List[str]:
    """Map a route_long_name to route_id(s).

    Returns all matching route_ids. Multiple matches are possible if
    operators reuse the same long name.
    """
    routes = feed.routes
    if "route_long_name" not in routes.columns:
        return []

    mask = routes["route_long_name"] == route_long_name
    matches = routes.loc[mask, "route_id"].dropna().unique()
    return sorted(str(value) for value in matches)


def route_id_to_long_name(feed: gk.Feed, route_id: str) -> Optional[str]:
    """Map a route_id back to route_long_name.

    Returns the first non-null long name if multiple rows match.
    """
    routes = feed.routes
    mask = routes["route_id"] == route_id
    subset = routes.loc[mask]

    if subset.empty or "route_long_name" not in subset.columns:
        return None

    values = subset["route_long_name"].dropna()
    if values.empty:
        return None
    return str(values.iloc[0])


def route_id_to_description_and_type(
    feed: gk.Feed,
    route_id: str,
) -> Tuple[Optional[str], Optional[int]]:
    """Return (route_desc, route_type) for a route_id.

    If no matching row or columns are missing, returns (None, None).
    """
    routes = feed.routes

    has_desc = "route_desc" in routes.columns
    has_type = "route_type" in routes.columns
    if not has_desc and not has_type:
        return None, None

    mask = routes["route_id"] == route_id
    subset = routes.loc[mask]
    if subset.empty:
        return None, None

    desc: Optional[str] = None
    type_val: Optional[int] = None

    if has_desc:
        desc_series = subset["route_desc"].dropna()
        if not desc_series.empty:
            desc = str(desc_series.iloc[0])

    if has_type:
        type_series = subset["route_type"].dropna()
        if not type_series.empty:
            # route_type is an int per GTFS spec; be lenient here
            try:
                type_val = int(type_series.iloc[0])
            except (TypeError, ValueError):
                type_val = None

    return desc, type_val


def stop_name_to_ids(feed: gk.Feed, stop_name: str) -> List[str]:
    """Map a stop_name to stop_id(s).

    Returns all matching stop_ids. Multiple matches are common for
    shared names (e.g. different platforms).
    """
    stops = feed.stops
    if "stop_name" not in stops.columns:
        return []

    mask = stops["stop_name"] == stop_name
    matches = stops.loc[mask, "stop_id"].dropna().unique()
    return sorted(str(value) for value in matches)


def stop_id_to_name(feed: gk.Feed, stop_id: str) -> Optional[str]:
    """Map a stop_id back to stop_name.

    Returns the first non-null name if multiple rows match.
    """
    stops = feed.stops
    mask = stops["stop_id"] == stop_id
    subset = stops.loc[mask]

    if subset.empty or "stop_name" not in subset.columns:
        return None

    values = subset["stop_name"].dropna()
    if values.empty:
        return None
    return str(values.iloc[0])


def stop_id_to_description(
    feed: gk.Feed,
    stop_id: str,
) -> Tuple[Optional[str], Optional[int]]:
    """Return (stop_desc, location_type) for a stop_id, if available.

    If no matching row or columns are missing, returns (None, None).
    """
    stops = feed.stops

    has_desc = "stop_desc" in stops.columns
    has_loc_type = "location_type" in stops.columns
    if not has_desc and not has_loc_type:
        return None, None

    mask = stops["stop_id"] == stop_id
    subset = stops.loc[mask]
    if subset.empty:
        return None, None

    desc: Optional[str] = None
    loc_type: Optional[int] = None

    if has_desc:
        desc_series = subset["stop_desc"].dropna()
        if not desc_series.empty:
            desc = str(desc_series.iloc[0])

    if has_loc_type:
        loc_type_series = subset["location_type"].dropna()
        if not loc_type_series.empty:
            try:
                loc_type = int(loc_type_series.iloc[0])
            except (TypeError, ValueError):
                loc_type = None

    return desc, loc_type


def stop_id_to_lat_lon(feed: gk.Feed, stop_id: str) -> Optional[Tuple[float, float]]:
    """Return latitude and longitude for a stop_id.

    Returns (lat, lon) for the first matching row, or None if not found
    or if coordinates are missing.
    """
    stops = feed.stops
    if "stop_lat" not in stops.columns or "stop_lon" not in stops.columns:
        return None

    mask = stops["stop_id"] == stop_id
    subset = stops.loc[mask]
    if subset.empty:
        return None

    row = subset.iloc[0]
    lat = row["stop_lat"]
    lon = row["stop_lon"]

    if pd.isna(lat) or pd.isna(lon):
        return None

    return float(lat), float(lon)


# ---------------------------------------------------------------------------
# Core trip / timepoint helpers
# ---------------------------------------------------------------------------


def find_trips_between_stops(
    feed: gk.Feed,
    route_id: str,
    from_stop_id: str,
    to_stop_id: str,
) -> List[str]:
    """Find trip_ids on a given route that go from from_stop_id to to_stop_id
    in the correct order.
    """
    trips_df = feed.trips
    stop_times_df = feed.stop_times

    # Trips that belong to the requested route.
    route_trips = trips_df.loc[trips_df["route_id"] == route_id, "trip_id"]
    if route_trips.empty:
        return []

    stop_times_subset = stop_times_df.loc[stop_times_df["trip_id"].isin(route_trips)]

    from_stops = stop_times_subset.loc[
        stop_times_subset["stop_id"] == from_stop_id, ["trip_id", "stop_sequence"]
    ]
    to_stops = stop_times_subset.loc[
        stop_times_subset["stop_id"] == to_stop_id, ["trip_id", "stop_sequence"]
    ]

    if from_stops.empty or to_stops.empty:
        return []

    merged = pd.merge(
        from_stops,
        to_stops,
        on="trip_id",
        suffixes=("_from", "_to"),
    )

    # Keep only trips where from_stop occurs before to_stop.
    valid = merged.loc[merged["stop_sequence_from"] < merged["stop_sequence_to"]]
    return sorted(valid["trip_id"].unique().tolist())


def route_has_stop_times(feed: gk.Feed, route_id: str) -> bool:
    """Return True if any stop_times rows exist for a route.

    Checks whether there is at least one stop_times entry
    for any trip that belongs to the given route_id.
    """
    trips_df = feed.trips
    stop_times_df = feed.stop_times

    route_trips = trips_df.loc[trips_df["route_id"] == route_id, "trip_id"]
    if route_trips.empty:
        return False

    mask = stop_times_df["trip_id"].isin(route_trips)
    return bool(mask.any())


def stop_has_stop_times(feed: gk.Feed, stop_id: str) -> bool:
    """Return True if a stop_id appears in the stop_times table.

    Checks whether there is at least one stop_times row
    whose stop_id matches the provided stop_id.
    """
    stop_times_df = feed.stop_times
    if "stop_id" not in stop_times_df.columns:
        return False

    mask = stop_times_df["stop_id"] == stop_id
    return bool(mask.any())


def get_expected_and_actual_arrivals_between_stations(
    static_feed: gk.Feed,
    trip_updates_feed: gtfs_realtime_pb2.FeedMessage,
    route_id: str,
    from_stop_id: str,
    to_stop_id: str,
    service_date: date,
    tz_name: str = DEFAULT_TZ,
) -> pd.DataFrame:
    """Return planned and actual arrival times between two stops for a route.

    For all trips on the given route that go from from_stop_id to
    to_stop_id in the correct order, this returns a DataFrame with
    planned and actual arrival times at the downstream stop.
    """
    trip_ids = find_trips_between_stops(
        static_feed,
        route_id=route_id,
        from_stop_id=from_stop_id,
        to_stop_id=to_stop_id,
    )

    if not trip_ids:
        return pd.DataFrame(
            columns=[
                "route_id",
                "trip_id",
                "from_stop_id",
                "to_stop_id",
                "planned_arrival",
                "actual_arrival",
            ]
        )

    planned_arrivals = get_planned_arrival_times(
        static_feed,
        trip_ids=trip_ids,
        stop_id=to_stop_id,
        service_date=service_date,
        tz_name=tz_name,
    )

    actual_arrivals = get_actual_arrival_times_from_trip_updates(
        trip_updates_feed=trip_updates_feed,
        trip_ids=trip_ids,
        stop_id=to_stop_id,
        tz_name=tz_name,
    )

    rows: List[Dict[str, object]] = []
    for trip_id_value in trip_ids:
        rows.append(
            {
                "route_id": route_id,
                "trip_id": trip_id_value,
                "from_stop_id": from_stop_id,
                "to_stop_id": to_stop_id,
                "planned_arrival": planned_arrivals.get(trip_id_value),
                "actual_arrival": actual_arrivals.get(trip_id_value),
            }
        )

    df = pd.DataFrame(rows)
    df = df[
        [
            "route_id",
            "trip_id",
            "from_stop_id",
            "to_stop_id",
            "planned_arrival",
            "actual_arrival",
        ]
    ]
    return df


def get_planned_arrival_times(
    feed: gk.Feed,
    trip_ids: Sequence[str],
    stop_id: str,
    service_date: date,
    tz_name: str = DEFAULT_TZ,
) -> Dict[str, datetime]:
    """Get planned arrival datetimes at a specific stop for a set of trips."""
    if not trip_ids:
        return {}

    tz = ZoneInfo(tz_name)
    stop_times = feed.stop_times

    mask = (stop_times["trip_id"].isin(trip_ids)) & (stop_times["stop_id"] == stop_id)
    subset = stop_times.loc[mask, ["trip_id", "arrival_time"]]

    result: Dict[str, datetime] = {}
    for row in subset.itertuples(index=False):
        if pd.isna(row.arrival_time):
            continue
        dt = gtfs_time_to_datetime(service_date, str(row.arrival_time), tz)
        result[str(row.trip_id)] = dt

    return result


def get_actual_arrival_times_from_trip_updates(
    trip_updates_feed: gtfs_realtime_pb2.FeedMessage,
    trip_ids: Sequence[str],
    stop_id: str,
    tz_name: str = DEFAULT_TZ,
) -> Dict[str, datetime]:
    """Extract actual/predicted arrival times (GTFS-RT TripUpdates) at a given stop."""
    if not trip_ids:
        return {}

    tz = ZoneInfo(tz_name)
    wanted = set(trip_ids)

    result: Dict[str, datetime] = {}

    for entity in trip_updates_feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip_update = entity.trip_update
        trip_id_value = trip_update.trip.trip_id
        if trip_id_value not in wanted:
            continue

        for stop_time_update in trip_update.stop_time_update:
            if stop_time_update.stop_id != stop_id:
                continue

            # Prefer explicit arrival.time, fall back to departure.time if needed.
            timestamp_value = 0
            if stop_time_update.arrival and stop_time_update.arrival.time:
                timestamp_value = stop_time_update.arrival.time
            elif stop_time_update.departure and stop_time_update.departure.time:
                timestamp_value = stop_time_update.departure.time

            if timestamp_value:
                dt_utc = datetime.fromtimestamp(timestamp_value, tz=timezone.utc)
                result[trip_id_value] = dt_utc.astimezone(tz)
            break  # Stop after first match for this stop_id.

    return result


def get_vehicle_positions_for_trips(
    vehicle_positions_feed: gtfs_realtime_pb2.FeedMessage,
    trip_ids: Sequence[str],
    tz_name: str = DEFAULT_TZ,
) -> Dict[str, Tuple[datetime, float, float]]:
    """Get vehicle positions for a set of trips from a VehiclePositions snapshot.

    The snapshot is assumed to represent "a point in time" (roughly the
    file's timestamp). For each trip_id, a single (time, lat, lon) is
    returned if present in the feed.
    """
    if not trip_ids:
        return {}

    tz = ZoneInfo(tz_name)
    wanted = set(trip_ids)
    result: Dict[str, Tuple[datetime, float, float]] = {}

    header_timestamp = vehicle_positions_feed.header.timestamp or 0

    for entity in vehicle_positions_feed.entity:
        if not entity.HasField("vehicle"):
            continue

        vehicle = entity.vehicle
        trip_id_value = vehicle.trip.trip_id
        if trip_id_value not in wanted:
            continue

        if not vehicle.HasField("position"):
            continue

        latitude = vehicle.position.latitude
        longitude = vehicle.position.longitude

        # Use vehicle-level timestamp if present; otherwise fall back to header.
        timestamp_value = vehicle.timestamp or header_timestamp
        if not timestamp_value:
            continue

        dt_utc = datetime.fromtimestamp(timestamp_value, tz=timezone.utc)
        dt_local = dt_utc.astimezone(tz)

        result[trip_id_value] = (dt_local, latitude, longitude)

    return result


def get_trip_timepoints_between_stations(
    static_zip_path: str | Path,
    trip_updates_pb_path: str | Path,
    vehicle_positions_pb_path: str | Path,
    route_id: str,
    from_stop_id: str,
    to_stop_id: str,
    service_date: date,
    tz_name: str = DEFAULT_TZ,
) -> pd.DataFrame:
    """High-level helper: for a given route and two stops, return
    planned arrival, actual arrival, and GPS position (snapshot)
    for all trips between those stops as a pandas DataFrame.

    The returned DataFrame has columns:

        - route_id
        - trip_id
        - from_stop_id
        - to_stop_id
        - planned_arrival (datetime64[ns, tz])
        - actual_arrival (datetime64[ns, tz], may be NaT)
        - vehicle_position_time (datetime64[ns, tz], may be NaT)
        - vehicle_latitude (float, may be NaN)
        - vehicle_longitude (float, may be NaN)
    """
    # Load data
    static_feed = load_static_feed(static_zip_path)
    trip_updates = load_gtfs_rt_feed(trip_updates_pb_path)
    vehicle_positions = load_gtfs_rt_feed(vehicle_positions_pb_path)

    # Identify relevant trips
    trip_ids = find_trips_between_stops(
        static_feed,
        route_id=route_id,
        from_stop_id=from_stop_id,
        to_stop_id=to_stop_id,
    )

    if not trip_ids:
        return pd.DataFrame(
            columns=[
                "route_id",
                "trip_id",
                "from_stop_id",
                "to_stop_id",
                "planned_arrival",
                "actual_arrival",
                "vehicle_position_time",
                "vehicle_latitude",
                "vehicle_longitude",
            ]
        )

    # Planned and actual arrival times at the downstream stop
    planned_arrivals = get_planned_arrival_times(
        static_feed,
        trip_ids=trip_ids,
        stop_id=to_stop_id,
        service_date=service_date,
        tz_name=tz_name,
    )

    actual_arrivals = get_actual_arrival_times_from_trip_updates(
        trip_updates_feed=trip_updates,
        trip_ids=trip_ids,
        stop_id=to_stop_id,
        tz_name=tz_name,
    )

    # Vehicle positions at snapshot time
    positions = get_vehicle_positions_for_trips(
        vehicle_positions_feed=vehicle_positions,
        trip_ids=trip_ids,
        tz_name=tz_name,
    )

    rows: List[Dict[str, object]] = []
    for trip_id_value in trip_ids:
        planned = planned_arrivals.get(trip_id_value)
        actual = actual_arrivals.get(trip_id_value)

        position_tuple = positions.get(trip_id_value)
        if position_tuple is not None:
            position_time, latitude, longitude = position_tuple
        else:
            position_time = None
            latitude = None
            longitude = None

        rows.append(
            {
                "route_id": route_id,
                "trip_id": trip_id_value,
                "from_stop_id": from_stop_id,
                "to_stop_id": to_stop_id,
                "planned_arrival": planned,
                "actual_arrival": actual,
                "vehicle_position_time": position_time,
                "vehicle_latitude": latitude,
                "vehicle_longitude": longitude,
            }
        )

    df = pd.DataFrame(rows)
    # Ensure deterministic column order
    df = df[
        [
            "route_id",
            "trip_id",
            "from_stop_id",
            "to_stop_id",
            "planned_arrival",
            "actual_arrival",
            "vehicle_position_time",
            "vehicle_latitude",
            "vehicle_longitude",
        ]
    ]
    return df
