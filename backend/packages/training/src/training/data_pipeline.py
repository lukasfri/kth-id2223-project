from datetime import date, datetime, timedelta
from time import sleep
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import openmeteo_requests
import requests_cache
from retry_requests import retry

from training.static_data import StaticData
from data_processing import *
from common import *
from gtfs import load_pb_file
from koda import download_koda_rt_file, download_koda_static_file


def download_data_in_range(start_date: date, end_date: date):
    d = start_date
    api_key = os.environ.get("API_KEY", "")
    root_dir = os.environ.get("ROOT_DIR", ".")
    data_dir = f"{root_dir}/data"
    while d <= end_date:  # <= makes it inclusive
        res_code = download_koda_rt_file(
            operator=Operator.SL,
            feedId=FeedID.TripUpdates,
            date=d,
            api_key=api_key,
            data_dir=data_dir,
        )
        attempts = 0
        while res_code != 200 and attempts < 5:
            attempts += 1
            sleep(30)
            res_code = download_koda_rt_file(
                operator=Operator.SL,
                feedId=FeedID.TripUpdates,
                date=d,
                api_key=api_key,
                data_dir=data_dir,
            )

        d += timedelta(days=1)


def _load_and_filter_rt_file(path: str, station_ids: set[str]) -> pd.DataFrame:
    """Load one real-time protobuf file and filter to relevant station_ids."""
    feed_message = load_pb_file(path)
    df_tmp = feed_message_to_dataframe(feed_message)

    mask = df_tmp["stop_time_updates"].apply(
        lambda stus: any(stu["stop_id"] in station_ids for stu in stus)
    )
    df_tmp = df_tmp[mask]

    return df_tmp


def make_df_from_stations(
    from_station: str, to_station: str, start_date: date, end_date: date
) -> tuple[pd.DataFrame, set[str]]:
    dateStr = os.environ.get("STATIC_DATA_DATE", "2024-06-15")
    dateOfStatic = datetime.strptime(dateStr, "%Y-%m-%d").date()

    root_dir = os.environ.get("ROOT_DIR", ".")
    static_data: StaticData
    if os.path.exists(f"{root_dir}/data/data-tmp/static_pkl/trips.pkl"):
        print("Using pickled static data")
        static_data = StaticData.load_from_pkl(f"{root_dir}/data/data-tmp/static_pkl")
    else:
        static_data = StaticData.load_static_data(f"{root_dir}/data/data-tmp")
        static_data.save_to_pkl(f"{root_dir}/data/data-tmp/static_pkl")
    # print(static_data.stops.head())
    station_targets = [from_station, to_station]
    station_df = static_data.stops[static_data.stops["stop_name"].isin(station_targets)]

    # print(station_df.head())

    station_ids: set[str] = set(station_df["stop_id"])

    base_dir = os.path.join(root_dir, "data", "data-tmp-rt", "sl", "TripUpdates")

    # 1) Discover all files in a canonical (sorted) order
    day = start_date
    rt_file_paths: list[str] = []

    while day <= end_date:
        rt_data_dir = os.path.join(
            base_dir, f"{day.year:04d}", f"{day.month:02d}", f"{day.day:02d}"
        )
        print("Reading data from date:", day)

        if not os.path.exists(rt_data_dir):
            raise Exception(f"No path to data: {rt_data_dir}")

        # Sort hour directories and files for deterministic behavior.
        for hour_dir in sorted(os.listdir(rt_data_dir)):
            hour_path = os.path.join(rt_data_dir, hour_dir)
            if not os.path.isdir(hour_path):
                continue

            for filename in sorted(os.listdir(hour_path)):
                file_path = os.path.join(hour_path, filename)
                if not os.path.isfile(file_path):
                    continue
                rt_file_paths.append(file_path)

        day += timedelta(days=1)

    # 2) Process all files concurrently using a ThreadPoolExecutor
    df_rt = pd.DataFrame()
    if rt_file_paths:
        max_workers_env = os.environ.get("RT_READ_WORKERS")
        if max_workers_env is not None:
            try:
                max_workers = int(max_workers_env)
            except ValueError:
                max_workers = 8
        else:
            max_workers = 8

        results_by_path: dict[str, pd.DataFrame] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(
                    _load_and_filter_rt_file,
                    path,
                    station_ids,
                ): path
                for path in rt_file_paths
            }

            for future in as_completed(future_to_path):
                path = future_to_path[future]
                df_tmp = future.result()
                if not df_tmp.empty:
                    results_by_path[path] = df_tmp

        # 3) Rebuild df_rt in the same logical order as rt_file_paths
        ordered_dfs: list[pd.DataFrame] = []
        for path in rt_file_paths:
            df_tmp = results_by_path.get(path)
            if df_tmp is not None and not df_tmp.empty:
                ordered_dfs.append(df_tmp)

        if ordered_dfs:
            df_rt = pd.concat(ordered_dfs)
        else:
            df_rt = pd.DataFrame()

    rt_joined_static_df = join_static_data_on_rt(static_data, df_rt)

    # print(rt_joined_static_df.head())

    exploded_df = explode_to_stops_with_join_static(static_data, rt_joined_static_df)

    # print(filtered_exp_df.head())

    return exploded_df, station_ids


def get_historical_weather(
    latitude: float, longitude: float, start_date: date, end_date: date
) -> pd.DataFrame:
    """Fetch daily historical weather from Open-Meteo archive API.

    Returns one row per day with:
      - date
      - temperature_2m_mean
      - precipitation_sum
      - wind_speed_10m_max
      - wind_direction_10m_dominant
    """
    
    url = "https://archive-api.open-meteo.com/v1/archive"

    start_str = start_date.isoformat()
    end_str = end_date.isoformat()

    cache_session = requests_cache.CachedSession(".cache/openmeteo", expire_after=3600)
    retry_session = retry(cache_session, retries=3, backoff_factor=0.2)

    client = openmeteo_requests.Client(session=retry_session)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_str,
        "end_date": end_str,
        "daily": [
            "temperature_2m_mean",
            "precipitation_sum",
            "wind_speed_10m_max",
            "wind_direction_10m_dominant",
        ],
        "timezone": "Europe/Stockholm",
    }

    responses = client.weather_api(url, params=params)
    if not responses:
        return pd.DataFrame()

    response = responses[0]
    daily = response.Daily()

    if daily == None:
        return pd.DataFrame()

    daily_time = pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", origin="unix"),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", origin="unix"),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left",
    )

    temperature_2m_mean = daily.Variables(0).ValuesAsNumpy()
    precipitation_sum = daily.Variables(1).ValuesAsNumpy()
    wind_speed_10m_max = daily.Variables(2).ValuesAsNumpy()
    wind_direction_10m_dominant = daily.Variables(3).ValuesAsNumpy()

    data = {
        "date": daily_time,
        "temperature_2m_mean": temperature_2m_mean,
        "precipitation_sum": precipitation_sum,
        "wind_speed_10m_max": wind_speed_10m_max,
        "wind_direction_10m_dominant": wind_direction_10m_dominant,
    }

    df_weather = pd.DataFrame(data)
    df_weather = df_weather.sort_values("date").reset_index(drop=True)

    return df_weather


def lag_times(df_exploded_with_stop_times: pd.DataFrame) -> pd.DataFrame:
    df_exploded_with_stop_times["arrival_time_prev"] = (
        df_exploded_with_stop_times.groupby("trip_id")["arrival_time"].shift(1)
    )
    df_exploded_with_stop_times["departure_time_prev"] = (
        df_exploded_with_stop_times.groupby("trip_id")["departure_time"].shift(1)
    )
    df_exploded_with_stop_times["arrival_time_planned_prev"] = (
        df_exploded_with_stop_times.groupby("trip_id")["arrival_time_planned"].shift(1)
    )
    df_exploded_with_stop_times["departure_time_planned_prev"] = (
        df_exploded_with_stop_times.groupby("trip_id")["departure_time_planned"].shift(
            1
        )
    )
    df_exploded_with_stop_times["arrival_time_late_prev"] = (
        df_exploded_with_stop_times.groupby("trip_id")["arrival_time_late"].shift(1)
    )
    df_exploded_with_stop_times["departure_time_late_prev"] = (
        df_exploded_with_stop_times.groupby("trip_id")["departure_time_late"].shift(1)
    )

    # print(df_exploded_with_stop_times.dtypes)
    # print(df_exploded_with_stop_times.head(40))

    return df_exploded_with_stop_times


def create_X_Y_df(
    from_station: str, to_station: str, start_date: date, end_date: date
) -> tuple[pd.DataFrame, pd.DataFrame]:
    df, station_ids = make_df_from_stations(
        from_station, to_station, start_date, end_date
    )
    df_lag = lag_times(df)

    df_lag = df_lag[df_lag["stop_id"].isin(station_ids)]

    # Fetch historical weather for the same date range
    latitude = float(os.environ.get("WEATHER_LATITUDE", "59.3293"))
    longitude = float(os.environ.get("WEATHER_LONGITUDE", "18.0686"))

    df_weather = get_historical_weather(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
    )

    weather_available = not df_weather.empty
    if weather_available:
        df_weather["date"] = pd.to_datetime(df_weather["date"]).dt.date
        df_lag["service_date"] = pd.to_datetime(
            df_lag["start_date"], format="%Y%m%d", errors="coerce"
        ).dt.date

        df_lag = df_lag.merge(
            df_weather,
            left_on="service_date",
            right_on="date",
            how="left",
        )
    else:
        raise Exception("Could not get weather")

    x_cols = [
            "arrival_time_planned",
            "arrival_time_planned_prev",
            "arrival_time_late_prev",
            "temperature_2m_mean",
            "precipitation_sum",
            "wind_speed_10m_max",
            "wind_direction_10m_dominant",
        ]
   
    y_col = "arrival_time_late"

    # Build X and y only from the relevant columns
    df_X = df_lag[x_cols].copy()

    df_y = df_lag[y_col].copy()

    # Drop rows only where X_cols or y_col are NA (ignore NA in other df_lag cols)
    mask = df_X.notna().all(axis=1) & df_y.notna()
    df_X = df_X.loc[mask].reset_index(drop=True)
    df_y = df_y.loc[mask].reset_index(drop=True)

    # Time-related columns are already represented as seconds.
    df_X = df_X.astype("float")
    df_y = df_y.astype("float")

    return df_X, df_y
