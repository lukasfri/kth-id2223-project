from datetime import date, datetime, timedelta
from time import sleep
import os

import pandas as pd

from static import StaticData
from data_processing import *
from common import *
from gtfs import load_pb_file
from koda import download_koda_rt_file, download_koda_static_file


def download_data_in_range(start_date:date, end_date:date):
    d = start_date
    api_key = os.environ.get("API_KEY", "")
    root_dir = os.environ.get("ROOT_DIR", ".")
    data_dir = f"{root_dir}/data"
    while d <= end_date: # <= makes it inclusive
        
        res_code = download_koda_rt_file(operator=Operator.SL, feedId=FeedID.TripUpdates, date=d, api_key=api_key, data_dir=data_dir)
        attempts = 0
        while res_code != 200 and attempts < 5:
            attempts += 1
            sleep(30)
            res_code = download_koda_rt_file(operator=Operator.SL, feedId=FeedID.TripUpdates, date=d, api_key=api_key, data_dir=data_dir)
        
        d += timedelta(days=1)


def make_df_from_stations(from_station:str, to_station:str, start_date:date, end_date:date) -> tuple[pd.DataFrame, set[str]]:

    dateStr = os.environ.get("STATIC_DATA_DATE", "2024-06-15")
    dateOfStatic = datetime.strptime(dateStr, "%Y-%m-%d").date()


    root_dir = os.environ.get("ROOT_DIR", ".")
    static_data:StaticData
    if os.path.exists(f"{root_dir}/data/data-tmp/static_pkl/trips.pkl"):
        static_data = StaticData.load_from_pkl(f"{root_dir}/data/data-tmp/static_pkl")
    else:
        static_data = StaticData.load_static_data(f"{root_dir}/data/data-tmp", dateOfStatic)
        static_data.save_to_pkl(f"{root_dir}/data/data-tmp/static_pkl")
    # print(static_data.stops.head())
    station_targets = [from_station, to_station]
    station_df = static_data.stops[static_data.stops["stop_name"].isin(station_targets)]

    # print(station_df.head())

    station_ids:set[str] = set(station_df["stop_id"])
    
    # TODO: Find better way
    rt_data_dir = f"{root_dir}/data/data-tmp-rt/sl/TripUpdates/{start_date.year:04d}/{start_date.month:02d}/{start_date.day:02d}"
    
    if not os.path.exists(rt_data_dir):
        raise Exception(f"No path to data: {rt_data_dir}")

    dirs_in_rt_dir = os.listdir(rt_data_dir)

    df_rt = pd.DataFrame()
    for d in dirs_in_rt_dir:
        files_in_rt_dir = os.listdir(os.path.join(rt_data_dir, d))
        for f in files_in_rt_dir:
            feed_message = load_pb_file(str(os.path.join(rt_data_dir, d, f)))
            df_tmp = feed_message_to_dataframe(feed_message)
            mask = df_tmp["stop_time_updates"].apply(
                lambda stus: any(stu["stop_id"] in station_ids for stu in stus)
            )
            df_tmp = df_tmp[mask]
            if df_rt.empty:
                df_rt = df_tmp
            else:
                df_rt = pd.concat([df_rt, df_tmp])
    
    rt_joined_static_df = join_static_data_on_rt(static_data, df_rt)

    # print(rt_joined_static_df.head())

    exploded_df = explode_to_stops_with_join_static(static_data, rt_joined_static_df)
    
    # print(filtered_exp_df.head())

    return exploded_df, station_ids

    
# TODO: 
def get_historical_weather(latitude:float, longitude:float, start_date:date, end_date:date) -> pd.DataFrame:
    
    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["temperature_2m_mean", "precipitation_sum", "wind_speed_10m_max", "wind_direction_10m_dominant"]
    }

    return pd.DataFrame()

def lag_times(df_exploded_with_stop_times:pd.DataFrame) -> pd.DataFrame:

    df_exploded_with_stop_times['arrival_time_prev'] = df_exploded_with_stop_times.groupby('trip_id')['arrival_time'].shift(1)
    df_exploded_with_stop_times['departure_time_prev'] = df_exploded_with_stop_times.groupby('trip_id')['departure_time'].shift(1)
    df_exploded_with_stop_times['arrival_time_planned_prev'] = df_exploded_with_stop_times.groupby('trip_id')['arrival_time_planned'].shift(1)
    df_exploded_with_stop_times['departure_time_planned_prev'] = df_exploded_with_stop_times.groupby('trip_id')['departure_time_planned'].shift(1)
    df_exploded_with_stop_times['arrival_time_late_prev'] = df_exploded_with_stop_times.groupby('trip_id')['arrival_time_late'].shift(1)
    df_exploded_with_stop_times['departure_time_late_prev'] = df_exploded_with_stop_times.groupby('trip_id')['departure_time_late'].shift(1)

    #print(df_exploded_with_stop_times.dtypes)
    #print(df_exploded_with_stop_times.head(40))

    return df_exploded_with_stop_times

def create_X_Y_df(from_station:str, to_station:str, start_date:date, end_date:date) -> tuple[pd.DataFrame, pd.DataFrame]:

    df, station_ids = make_df_from_stations(from_station, to_station, start_date, end_date)
    df_lag = lag_times(df)

    df_lag = df_lag[df_lag["stop_id"].isin(station_ids)]

    x_cols = [
        "arrival_time_planned",
        "arrival_time_planned_prev",
        "arrival_time_late_prev",
        "stop_id",
    ]
    y_col = "arrival_time_late"

    # Build X and y only from the relevant columns
    df_X = df_lag[x_cols].copy()

    df_y = df_lag[y_col].copy()

    # Drop rows only where X_cols or y_col are NA (ignore NA in other df_lag cols)
    mask = df_X.notna().all(axis=1) & df_y.notna()
    df_X = df_X.loc[mask].reset_index(drop=True)
    df_y = df_y.loc[mask].reset_index(drop=True)
    
    datetime_cols = ["arrival_time_planned", "arrival_time_planned_prev"]
    for col in datetime_cols:
        # Ensure datetime dtype
        df_X[col] = pd.to_datetime(df_X[col])

        # Convert to unix timestamp (seconds since epoch)
        df_X[col] = df_X[col].astype("int64") / 1e9

    timedelta_cols = ["arrival_time_late_prev"]
    for col in timedelta_cols:
        df_X[col] = pd.to_timedelta(df_X[col])
        df_X[col] = df_X[col].dt.total_seconds()

    df_y = pd.to_timedelta(df_y).dt.total_seconds()

    df_X["stop_id"] = df_X["stop_id"].astype("category")
    df_X = pd.get_dummies(df_X, columns=["stop_id"], prefix="stop_id", dummy_na=False)

    return df_X, df_y
