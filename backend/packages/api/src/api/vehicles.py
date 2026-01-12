
# Singleton to hold global state
import asyncio
from datetime import date
import datetime
import os
from fastapi import APIRouter, FastAPI
from fastapi.concurrency import asynccontextmanager
import pandas as pd
from pydantic import BaseModel
from training.data_pipeline import create_X_from_df, lag_times
from xgboost import XGBRegressor

from training.common import FeedID, Operator
from training.gtfs import load_gtfs_rt_immediately, list_gtfs_files , load_gtfs_frame_from_files
from training.static_data import StaticData
from training.data_processing import explode_to_stops_with_join_static
from training.model_training import load_route_model

data_folder = f"./data"

router = APIRouter()

df_buses = None
xgbModels:dict[str, XGBRegressor] = {}

STAM_BUSES_ROUTE_SET = {"9011001000100000", 
                    "9011001000200000",
                    "9011001000300000",
                    "9011001000400000"}

for route in STAM_BUSES_ROUTE_SET:
    xgbModels[route] = load_route_model(route)

async def update_buses_loop():
    global df_buses

    while True:
        try:
            print("Updating vehicle positions...")
            # Run the blocking data loading in a separate thread to keep the event loop responsive
            df_buses = await asyncio.to_thread(load_gtfs_rt_positions)
            print("Updated vehicle positions.")
        except Exception as e:
            print(f"Error updating vehicle positions: {e}")
        
        await asyncio.sleep(15)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create the background task
    task = asyncio.create_task(update_buses_loop())
    yield
    # Shutdown: Cancel the task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    

def gtfs_static_data_load():
    gtfs_static_path = f"{data_folder}/gtfs-static/data-tmp"

    todayDate = date.today()

    # Load data similarly to api
    try:
        gtfs_static_data = StaticData.load_from_pkl(gtfs_static_path)
    except FileNotFoundError:
        gtfs_static_data = StaticData.load_static_data(gtfs_static_path) #,todayDate)

        gtfs_static_data.save_to_pkl(gtfs_static_path)

    return gtfs_static_data

gtfs_static_data = gtfs_static_data_load()

from training.data_processing import feed_message_to_vehicle_position_dataframe, join_static_data_on_rt_vehicle_positions

# print(x_test.dtypes)
    # print(x_test.head())
    # print(x_test.max())
    # print(x_test.min())

    # y_pred = model.predict(x_test)
    # print("MSE:", mean_squared_error(y_test, y_pred))
GTFS_RT_API_KEY = os.environ.get("GTFS_REGIONAL_RT_API_KEY", "")
if GTFS_RT_API_KEY == "":
    raise Exception("GTFS_REGIONAL_RT_API_KEY environment variable not set")

# xgb_model = XGBRegressor()
# xgb_model.load_model(f"./models/9011001001300000_xgb_model.json")

def do_infrence_on_route(route_id: str, model: XGBRegressor, data: pd.DataFrame) -> pd.DataFrame:
    filtered_data = data[data["route_id"] == route_id].copy()
    filtered_data["arrival_time_late_prev"] = filtered_data["arrival_time_late_prev"].fillna(
        pd.to_timedelta(1, unit="s")
    )

    x_data = create_X_from_df(filtered_data)

    late_preds = model.predict(x_data)

    # ensure datetime type + add timedelta seconds
    filtered_data["arrival_time_estimate"] = (
        pd.to_datetime(filtered_data["arrival_time_planned"])
        + pd.to_timedelta(pd.Series(late_preds), unit="s")
    )

    return filtered_data

def load_gtfs_rt_positions() -> pd.DataFrame:
    gtfs_vehicle_positions = load_gtfs_rt_immediately(
        operator=Operator.SL, 
        feedId=FeedID.VehiclePositions, 
        api_key= GTFS_RT_API_KEY,
    )

    df = feed_message_to_vehicle_position_dataframe(gtfs_vehicle_positions)
    df = join_static_data_on_rt_vehicle_positions(gtfs_static_data, df)

    now = datetime.datetime.now(datetime.timezone.utc)
    ten_minute_files = list_gtfs_files(
        base_path=f"{data_folder}/gtfs-rt/data-tmp/sl/TripUpdates",
        start_dt=now - datetime.timedelta(minutes=10),
        end_dt=now
    )
    
    
    trip_updates_df = load_gtfs_frame_from_files(ten_minute_files, gtfs_static_data)

    trip_updates_df = trip_updates_df[trip_updates_df["route_id"].isin(STAM_BUSES_ROUTE_SET)]
    trip_updates_df = explode_to_stops_with_join_static(gtfs_static_data, trip_updates_df)
    trip_updates_df = lag_times(trip_updates_df)

    # Only keep the last line stop_sequence per trip_id
    # multiindex: trip_id	stop_sequence	
    trip_updates_df = trip_updates_df.sort_values(['trip_id', 'stop_sequence'])
    trip_updates_df = trip_updates_df.groupby(level='trip_id').last()
    
    tmp_df = pd.DataFrame()

    for route_id in STAM_BUSES_ROUTE_SET:
        if tmp_df.empty:
            tmp_df = do_infrence_on_route(route_id=route_id, model=xgbModels[route_id], data=trip_updates_df)
            continue
        tmp_df = pd.concat([tmp_df, do_infrence_on_route(route_id=route_id, model=xgbModels[route_id], data=trip_updates_df)])


    df = df.join(tmp_df, on="trip_id", rsuffix="_trip", how="inner")

    return df


class VehiclePosition(BaseModel):
    latitude: float
    longitude: float
    bearing: float
    speed: float
    odometer: float

class Vehicle(BaseModel):
    id: str
    position: VehiclePosition
    trip_id: str
    next_stop_id: str
    next_stop_scheduled_arrival_time: float
    next_stop_estimated_arrival_time: float

def bus_row_to_vehicle(row) -> Vehicle:
    return Vehicle(
        id=str(row["id"]),
        trip_id=row["trip_id"],
        position=VehiclePosition(
            latitude=row["vehicle_latitude"],
            longitude=row["vehicle_longitude"],
            bearing=row["vehicle_bearing"],
            speed=row["vehicle_speed"],
            odometer=row["vehicle_odometer"],
        ),
        next_stop_id=row["stop_id"],
        next_stop_scheduled_arrival_time=row["arrival_time_planned"],
        next_stop_estimated_arrival_time=row["arrival_time_estimate"],
    )

@router.get("/vehicles/{route_short_name}")
async def get_vehicle_positions(route_short_name: str) -> list[Vehicle]:
    if df_buses is None:
        return []
    
    SL_AGENCY_ID = gtfs_static_data.agencies[gtfs_static_data.agencies["agency_name"] == "AB Storstockholms Lokaltrafik"].index[0]

    buses = df_buses[(df_buses["route_short_name"] == route_short_name) & (df_buses["agency_id"] == SL_AGENCY_ID)]

    result_vehicles = [bus_row_to_vehicle(row) for _, row in buses.iterrows()]

    return result_vehicles
