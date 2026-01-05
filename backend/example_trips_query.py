from datetime import date
from sl_trip_queries import *
    
feed_static = load_static_feed("./data/sl_2024-06-15.zip")
routes = route_short_name_to_ids(feed_static, "14")

print(routes)

print(route_id_to_long_name(feed_static, routes[0]))

routeID = routes[0]

fromStop = stop_name_to_ids(feed_static, "Bergshamra")
fromStopID = []
toStop = stop_name_to_ids(feed_static, "Tekniska högskolan")
toStopID = []

print(fromStop)
print(toStop)

for id in fromStop:
    if stop_has_stop_times(feed_static, id):
        fromStopID.append(id)

for id in toStop:
    if stop_has_stop_times(feed_static, id):
        toStopID.append(id)

print(fromStopID)
print(toStopID)
        

updates_list = ["./data/data-tmp-rt/sl/TripUpdates/2024/06/15/10/sl-tripupdates-2024-06-15T10-03-05Z.pb","./data/data-tmp-rt/sl/TripUpdates/2024/06/15/10/sl-tripupdates-2024-06-15T10-03-19Z.pb","./data/data-tmp-rt/sl/TripUpdates/2024/06/15/10/sl-tripupdates-2024-06-15T10-03-33Z.pb","./data/data-tmp-rt/sl/TripUpdates/2024/06/15/10/sl-tripupdates-2024-06-15T10-03-47Z.pb"]

feed_ups = [load_gtfs_rt_feed(f) for f in updates_list]

for frID in fromStopID:
    for toID in toStopID:
        for feed_updates in feed_ups:
            df = get_expected_and_actual_arrivals_between_stations(feed_static, feed_updates, routeID, frID, toID, date(2024, 6, 15)).dropna()
            if df.empty:
                continue
            print("number of rows:", df.shape[0])
            print(df.head())

# df = get_trip_timepoints_between_stations(
#     static_zip_path="./data/sl_2024-06-15.zip",
#     trip_updates_pb_path="./data/data-tmp-rt/sl/TripUpdates/2024/06/15/10/sl-tripupdates-2024-06-15T10-00-17Z.pb",
#     vehicle_positions_pb_path="./data/data-tmp-rt/sl/VehiclePositions/2024/06/15/10/sl-vehiclepositions-2024-06-15T10-00-16Z.pb",
#     route_id=routeID,
#     from_stop_id=fromStopID,
#     to_stop_id=toStopID,
#     service_date=date(2024, 6, 15),
# )
# print(df.head())
