import pandas as pd
import training.__generated__.gtfs_realtime_pb2 as gtfs_rt


class StaticData:
    trips: pd.DataFrame
    routes: pd.DataFrame
    stop_times: pd.DataFrame
    agencies: pd.DataFrame
    stops: pd.DataFrame
    calendar_dates: pd.DataFrame

    def __init__(
        self,
        trips: pd.DataFrame,
        routes: pd.DataFrame,
        stop_times: pd.DataFrame,
        agencies: pd.DataFrame,
        stops: pd.DataFrame,
        calendar_dates: pd.DataFrame,
    ):
        self.trips = trips
        self.routes = routes
        self.stop_times = stop_times
        self.agencies = agencies
        self.stops = stops
        self.calendar_dates = calendar_dates

    def save_to_pkl(self, pkl_folder_path: str):
        self.trips.to_pickle(f"{pkl_folder_path}/trips.pkl")
        self.routes.to_pickle(f"{pkl_folder_path}/routes.pkl")
        self.stop_times.to_pickle(f"{pkl_folder_path}/stop_times.pkl")
        self.agencies.to_pickle(f"{pkl_folder_path}/agencies.pkl")
        self.stops.to_pickle(f"{pkl_folder_path}/stops.pkl")
        self.calendar_dates.to_pickle(f"{pkl_folder_path}/calendar_dates.pkl")

    @staticmethod
    def load_static_data(folder_path: str) -> "StaticData":
        trips = StaticData.load_trips(f"{folder_path}/trips.txt")
        calendar_dates = StaticData.load_calendar_dates(f"{folder_path}/calendar_dates.txt")
        routes = StaticData.load_routes(f"{folder_path}/routes.txt")
        stop_times = StaticData.load_stop_times(f"{folder_path}/stop_times.txt")
        agencies = StaticData.load_agencies(f"{folder_path}/agency.txt")
        stops = StaticData.load_stops(f"{folder_path}/stops.txt")

        return StaticData(trips, routes, stop_times, agencies, stops, calendar_dates)

    @staticmethod
    def load_from_pkl(pkl_folder_path: str) -> "StaticData":
        trips = pd.read_pickle(f"{pkl_folder_path}/trips.pkl")
        routes = pd.read_pickle(f"{pkl_folder_path}/routes.pkl")
        stop_times = pd.read_pickle(f"{pkl_folder_path}/stop_times.pkl")
        agencies = pd.read_pickle(f"{pkl_folder_path}/agencies.pkl")
        stops = pd.read_pickle(f"{pkl_folder_path}/stops.pkl")
        calendar_dates = pd.read_pickle(f"{pkl_folder_path}/calendar_dates.pkl")

        return StaticData(trips, routes, stop_times, agencies, stops, calendar_dates)

    @staticmethod
    def load_trips(path: str) -> pd.DataFrame:
        trips = pd.read_csv(
            path,
            dtype={
                "trip_id": pd.StringDtype(),
                "route_id": pd.StringDtype(),
                "trip_headsign": pd.StringDtype(),
                "service_id": "Int64",
                "shape_id": "Int64",
            },
        )

        trips = trips.set_index("trip_id")

        return trips

    @staticmethod
    def load_stops(path: str) -> pd.DataFrame:
        stops = pd.read_csv(
            path,
            dtype={
                "stop_id": pd.StringDtype(),
                "stop_name": pd.StringDtype(),
                "stop_lat": pd.Float64Dtype(),
                "stop_lon": pd.Float64Dtype(),
                "location_type": "Int64",
                "parent_station": pd.StringDtype(),
                "platform_code": pd.StringDtype(),
            },
        )

        return stops

    @staticmethod
    def load_routes(path: str) -> pd.DataFrame:
        routes = pd.read_csv(
            path,
            dtype={
                "agency_id": pd.StringDtype(),
                "route_short_name": pd.StringDtype(),
                "route_long_name": pd.StringDtype(),
                "route_desc": pd.StringDtype(),
                "route_type": "Int64",
            },
        )

        routes = routes.set_index("route_id")

        return routes

    @staticmethod
    def load_stop_times(path: str) -> pd.DataFrame:
        DropOffType = (
            gtfs_rt.TripUpdate.StopTimeUpdate.StopTimeProperties.DropOffPickupType
        )
        drop_off_type = pd.CategoricalDtype(
            [
                DropOffType.REGULAR,
                DropOffType.NONE,
                DropOffType.PHONE_AGENCY,
                DropOffType.COORDINATE_WITH_DRIVER,
            ]
        )

        stop_times = pd.read_csv(
            path,
            dtype={
                "trip_id": pd.StringDtype(),
                "stop_id": pd.StringDtype(),
                "stop_headsign": pd.StringDtype(),
                "pickup_type": drop_off_type,
                "drop_off_type": drop_off_type,
            },
        )

        stop_times = stop_times.set_index(["trip_id", "stop_sequence"])


        def time_stamp_to_seconds(time_str: str):
            if time_str == "":
                return pd.NA
            hours, minutes, seconds = map(int, time_str.split(":"))
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return pd.Timedelta(seconds=total_seconds)

        stop_times["arrival_time_seconds_since_midnight"] = stop_times["arrival_time"].map(time_stamp_to_seconds)
        stop_times["departure_time_seconds_since_midnight"] = stop_times["departure_time"].map(time_stamp_to_seconds)
        stop_times.drop(columns=["arrival_time", "departure_time"], inplace=True)

        return stop_times

    @staticmethod
    def load_agencies(path: str) -> pd.DataFrame:
        agencies = pd.read_csv(
            path,
            dtype={
                "agency_id": pd.StringDtype(),
                "agency_name": pd.StringDtype(),
                "agency_url": pd.StringDtype(),
                "agency_timezone": pd.StringDtype(),
                "agency_lang": pd.StringDtype(),
                "agency_fare_url": pd.StringDtype(),
            },
        )

        agencies = agencies.set_index("agency_id")

        return agencies

    @staticmethod
    def load_calendar_dates(path: str) -> pd.DataFrame:
        # service_id,date,exception_type
        # 1,20260302,1
        calendar_dates = pd.read_csv(
            path,
            dtype={
                "service_id": "Int64",
                "date": pd.StringDtype(),
                "exception_type": "Int64",
            },
        )

        calendar_dates["date"] = pd.to_datetime(
            calendar_dates["date"], format="%Y%m%d",
        )

        return calendar_dates
