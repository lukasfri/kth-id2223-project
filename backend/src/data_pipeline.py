from datetime import date
import os

from static import StaticData
from data_processing import *
from common import *
from gtfs import load_pb_file
from koda import download_koda_rt_file, download_koda_static_file

from xgboost import XGBRegressor

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

    
