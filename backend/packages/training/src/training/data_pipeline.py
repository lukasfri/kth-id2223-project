from datetime import date
import os

from static import StaticData
from data_processing import *
from common import *
from gtfs import load_pb_file
from koda import download_koda_rt_file, download_koda_static_file


def make_df_from_stations(from_station:str, to_station:str):

    dateOfStatic = date(2024, 6, 15) # TODO: find better way

    static_data:StaticData
    if os.path.exists("./data/data-tmp/static_pkl/trips.pkl"):
        static_data = StaticData.load_from_pkl("./data/data-tmp/static_pkl")
    else:
        static_data = StaticData.load_static_data("./data/data-tmp", dateOfStatic)
        static_data.save_to_pkl("./data/data-tmp/static_pkl")
    
    # TODO: Find better way
    rt_data_dir = f"./data/data-tmp-rt/sl/TripUpdates/{dateOfStatic.year:04d}/{dateOfStatic.month:02d}/{dateOfStatic.day:02d}/10" 
    files_in_rt_dir = os.listdir(rt_data_dir)

    df_rt = pd.DataFrame()

    for f in files_in_rt_dir:
        feed_message = load_pb_file(str(os.path.join(rt_data_dir, f)))
        df_tmp = feed_message_to_dataframe(feed_message)

        if df_rt.empty:
            df_rt = df_tmp
        else:
            df_rt = pd.concat([df_rt, df_tmp])
    
    # print(static_data.stops.head())
    station_targets = [from_station, to_station]
    station_df = static_data.stops[static_data.stops["stop_name"].isin(station_targets)]

    # print(station_df.head())

    station_list = list(station_df["stop_id"])

    rt_joined_static_df = join_static_data_on_rt(static_data, df_rt)

    # print(rt_joined_static_df.head())

    exploded_df = explode_to_stops_with_join_static(static_data, rt_joined_static_df)
    
    filtered_exp_df = exploded_df[exploded_df["stop_id"].isin(station_list)]

    # print(filtered_exp_df.head())

    return filtered_exp_df

    
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

    print(df_exploded_with_stop_times.dtypes)
    print(df_exploded_with_stop_times.head(40))

    return df_exploded_with_stop_times

def create_X_Y_df(from_station:str, to_station:str) -> tuple[pd.DataFrame, pd.DataFrame]:

    df = make_df_from_stations(from_station, to_station)
    df_lag = lag_times(df)

    # TODO: add weather
    df_X = df_lag["arrival_time_planned", "arrival_time_planned_prev", "arrival_time_late_prev", "stop_id"]
    df_X["stop_id"] = df_X["stop_id"].astype("category")

    df_y = df_lag["arrival_time_late"]

    return df_X, df_y
