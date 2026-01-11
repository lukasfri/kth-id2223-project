
import os
import pickle
from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from training.common import FeedID, Operator
from training.static_data import StaticData

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Trip(BaseModel):
    id: str
    delay: int

class Route(BaseModel):
    id: str
    name: str
    stops: list['Stop']

class LatLon(BaseModel):
    latitude: float
    longitude: float

class Stop(BaseModel):
    id: str
    name: str
    position: LatLon

operator = Operator.SL
myDate = date(2024, 6, 15)
hour = 10
feedId = FeedID.TripUpdates

data_folder = f"./data/koda-static"

static_data: StaticData
pickle_file_path = f"{data_folder}/static-data-{myDate.year:04d}-{myDate.month:02d}-{myDate.day:02d}.pkl"
if os.path.exists(pickle_file_path):
    print("Static data pickle file exists.")

    static_data = pickle.load(open(pickle_file_path, "rb"))
else:
    print("Loading static data from GTFS files.")
    static_data = StaticData.load_static_data(f"{data_folder}/data-tmp", myDate)
    pickle.dump(static_data, open(pickle_file_path, "wb"))
    
@app.get("/routes/{route_short_name}")
async def get_route(route_short_name: str) -> Route:
    SL_AGENCY_ID = static_data.agencies[static_data.agencies["agency_name"] == "AB Storstockholms Lokaltrafik"].index[0]

    possible_routes = static_data.routes[
        (static_data.routes['route_short_name'] == route_short_name) & \
        (static_data.routes["agency_id"] == SL_AGENCY_ID)]

    if possible_routes.empty:
        raise HTTPException(status_code=404, detail="Route not found")

    route_id = possible_routes.index[0]

    trips_for_route = static_data.trips[static_data.trips["route_id"] == route_id]

    if trips_for_route.empty:
        raise HTTPException(status_code=404, detail="No trips found for this route")

    trip_ids = trips_for_route.index

    # Filter stop times for the relevant trips
    # Index level 0 is trip_id
    relevant_stop_times = static_data.stop_times[
        static_data.stop_times.index.get_level_values(0).isin(trip_ids)
    ].sort_index() # Sort by index to ensure stop_sequence order

    if relevant_stop_times.empty:
        raise HTTPException(status_code=404, detail="No stop times found for sequences")

    # Group by trip_id and get sequence of stop_ids
    sequences = relevant_stop_times.groupby("trip_id")["stop_id"].apply(tuple)

    # Get the most common sequence
    most_common_sequence = sequences.value_counts().index[0]

    # Map stop_ids to Stop objects
    stops_map = static_data.stops.set_index("stop_id")
    
    result_stops = []
    for stop_id in most_common_sequence:
        if stop_id in stops_map.index:
            stop_info = stops_map.loc[stop_id]
            result_stops.append(Stop(
                id=stop_id,
                name=stop_info["stop_name"],
                position=LatLon(
                    latitude=stop_info["stop_lat"], 
                    longitude=stop_info["stop_lon"]
                )
            ))

    return Route(id=route_id, name=route_short_name, stops=result_stops)

def main():
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
    
if __name__ == "__main__":
    main()