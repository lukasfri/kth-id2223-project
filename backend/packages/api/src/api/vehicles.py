
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
from training.data_processing import explode_to_stops_with_join_static, join_static_data_on_rt_trip_updates
from training.model_training import load_route_model
from training.data_processing import feed_message_to_vehicle_position_dataframe, join_static_data_on_rt_vehicle_positions

data_folder = f"./data"
model_path = f"./models"

router = APIRouter()

df_buses = None
xgbModels:dict[str, XGBRegressor] = {}

STAM_BUSES_ROUTE_SET = {"9011001000100000", 
                    "9011001000200000",
                    "9011001000300000",
                    "9011001000400000"}

for route in STAM_BUSES_ROUTE_SET:
    xgbModels[route] = load_route_model(route, model_path=model_path)

async def update_buses_loop():
    global df_buses

    while True:
        start_time = datetime.datetime.now()
        try:
            print("Updating vehicle positions...")
            # Run the blocking data loading in a separate thread to keep the event loop responsive
            df_buses = await asyncio.to_thread(load_gtfs_rt_positions)
            print("Updated vehicle positions.")
        except Exception as e:
            print(f"Error updating vehicle positions: {e}")
        
        elapsed = (datetime.datetime.now() - start_time).total_seconds()
        SLEEP_TIME = 15  # seconds
        sleep_duration = max(0, SLEEP_TIME - elapsed)
        await asyncio.sleep(sleep_duration)

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

GTFS_RT_API_KEY = os.environ.get("GTFS_REGIONAL_RT_API_KEY", "")
if GTFS_RT_API_KEY == "":
    raise Exception("GTFS_REGIONAL_RT_API_KEY environment variable not set")

def do_inference_on_route(route_id: str, model: XGBRegressor, data: pd.DataFrame) -> pd.DataFrame:
    filtered_data = data[data["route_id"] == route_id].copy()
    filtered_data["arrival_time_late_prev"] = filtered_data["arrival_time_late_prev"].fillna(
        pd.to_timedelta(1, unit="s")
    )

    x_data = create_X_from_df(filtered_data)
    #print(x_data)
    late_preds = model.predict(x_data)
    #print(late_preds)
    filtered_data["arrival_delay_estimate"] = late_preds.astype(float)
    # ensure datetime type + add timedelta seconds
    filtered_data["arrival_time_estimate"] = (
        pd.to_datetime(filtered_data["arrival_time_planned"])
        + pd.to_timedelta(filtered_data["arrival_delay_estimate"] , unit="s")
    )

    return filtered_data

def load_gtfs_rt_positions() -> pd.DataFrame:
    gtfs_vehicle_positions = load_gtfs_rt_immediately(
        operator=Operator.SL, 
        feedId=FeedID.VehiclePositions, 
        api_key= GTFS_RT_API_KEY,
    )

    buses_df = feed_message_to_vehicle_position_dataframe(gtfs_vehicle_positions)
    buses_df = join_static_data_on_rt_vehicle_positions(gtfs_static_data, buses_df)

    now = datetime.datetime.now(datetime.timezone.utc)
    ten_minute_files = list_gtfs_files(
        base_path=f"{data_folder}/gtfs-rt/data-tmp/sl/TripUpdates",
        start_dt=now - datetime.timedelta(minutes=10),
        end_dt=now
    )

    gtfs_feed_df = load_gtfs_frame_from_files(ten_minute_files, gtfs_static_data)

    trip_updates_df = gtfs_feed_df[gtfs_feed_df["route_id"].isin(STAM_BUSES_ROUTE_SET)]
    trip_updates_df = join_static_data_on_rt_trip_updates(gtfs_static_data, trip_updates_df)
    trip_updates_df = explode_to_stops_with_join_static(gtfs_static_data, trip_updates_df)
    trip_updates_df = lag_times(trip_updates_df)


    # Only keep the last line stop_sequence per trip_id
    # multiindex: trip_id	stop_sequence	
    trip_updates_df = trip_updates_df.sort_values(['trip_id', 'stop_sequence'])

    current_time_utc = pd.Timestamp.now(tz="Europe/Stockholm")
    # Remove timezone from current time for comparison
    current_time_utc = current_time_utc.tz_localize(None)
    trip_updates_df = trip_updates_df[(trip_updates_df["arrival_time_planned"] + trip_updates_df["arrival_time_late_prev"]) > current_time_utc]

    trip_updates_df = trip_updates_df.groupby(level='trip_id').first()

    trip_updates_df = trip_updates_df.reset_index()


    inferences = []

    for route_id in STAM_BUSES_ROUTE_SET:
        inferences.append(do_inference_on_route(route_id=route_id, model=xgbModels[route_id], data=trip_updates_df))

    inference_df = pd.concat(inferences)
    buses_df = buses_df.set_index("trip_id")
    inference_df = inference_df.reset_index()
    inference_df = inference_df.set_index("trip_id")

    inference_df = inference_df.join(buses_df, on="trip_id", rsuffix="_trip", how="inner")

    inference_df = inference_df.reset_index()

    return inference_df


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
    next_stop_estimated_arrival_time: float | None


def nan_if_nat(value: pd.Timestamp) -> float | None:
    if pd.isnull(value):
        return None
    
    return value.timestamp()

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
        next_stop_scheduled_arrival_time=row["arrival_time_planned"].timestamp(),
        next_stop_estimated_arrival_time=nan_if_nat(row["arrival_time_estimate"]),
    )

@router.get("/vehicles/{route_short_name}")
async def get_vehicle_positions(route_short_name: str) -> list[Vehicle]:
    if df_buses is None:
        return []
    
    SL_AGENCY_ID = gtfs_static_data.agencies[gtfs_static_data.agencies["agency_name"] == "AB Storstockholms Lokaltrafik"].index[0]

    buses = df_buses[(df_buses["route_short_name"] == route_short_name) & (df_buses["agency_id"] == SL_AGENCY_ID)]

    result_vehicles = [bus_row_to_vehicle(row) for _, row in buses.iterrows()]

    return result_vehicles
