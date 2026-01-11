
# Singleton to hold global state
import asyncio
from datetime import date
import os
from fastapi import APIRouter, FastAPI
from fastapi.concurrency import asynccontextmanager
import pandas as pd
from pydantic import BaseModel

from training.common import FeedID, Operator
from training.gtfs import load_gtfs_rt_immediately
from training.static_data import StaticData

data_folder = f"./data"

router = APIRouter()

df_buses = None

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
        gtfs_static_data = StaticData.load_static_data(gtfs_static_path, todayDate)

        gtfs_static_data.save_to_pkl(gtfs_static_path)

    return gtfs_static_data

gtfs_static_data = gtfs_static_data_load()

from training.data_processing import feed_message_to_vehicle_position_dataframe, join_static_data_on_rt_vehicle_positions

GTFS_RT_API_KEY = os.environ.get("GTFS_REGIONAL_RT_API_KEY", "")
if GTFS_RT_API_KEY == "":
    raise Exception("GTFS_REGIONAL_RT_API_KEY environment variable not set")

def load_gtfs_rt_positions() -> pd.DataFrame:
    gtfs_feed_message = load_gtfs_rt_immediately(
        operator=Operator.SL, 
        feedId=FeedID.VehiclePositions, 
        api_key= GTFS_RT_API_KEY,
    )

    df = feed_message_to_vehicle_position_dataframe(gtfs_feed_message)
    df = join_static_data_on_rt_vehicle_positions(gtfs_static_data, df)

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
        )
    )

@router.get("/vehicles/{route_short_name}")
async def get_vehicle_positions(route_short_name: str) -> list[Vehicle]:
    if df_buses is None:
        return []
    
    SL_AGENCY_ID = gtfs_static_data.agencies[gtfs_static_data.agencies["agency_name"] == "AB Storstockholms Lokaltrafik"].index[0]

    buses = df_buses[(df_buses["route_short_name"] == route_short_name) & (df_buses["agency_id"] == SL_AGENCY_ID)]

    result_vehicles = [bus_row_to_vehicle(row) for _, row in buses.iterrows()]

    return result_vehicles
