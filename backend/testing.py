from datetime import datetime
import pykoda
import numpy as np
import tqdm

def timestmp_to_time_of_day(timestamp):
    time_of_day = []
    for ts in timestamp:
        t = datetime.fromtimestamp(ts)
        time_of_day.append(t.hour / 24 + t.minute / (24 * 60) + t.second / (24 * 3600))

    return time_of_day

def get_features(company, date_start, date_end, start_hour, end_hour, selected_features, n_select=None):
    # Load all the data for the selected route.
    df = pykoda.datautils.get_data_range(feed='TripUpdates', company=company, start_date=date_start,
                                         end_date=date_end, start_hour=start_hour, end_hour=end_hour,
                                         merge_static=True,
                                         query='route_short_name == "3"')  # 'route_desc == "blåbuss"'

    # Find out the corresponding trips (each individual instance of the route)
    grouped_trips = df.groupby('trip_id')
    candidate_trips = list(df.trip_id.unique())
    if n_select is not None:
        candidate_trips = candidate_trips[:n_select]
    delay_list = []
    feature_list = []

    for tripid in tqdm.tqdm(candidate_trips, desc='Loading trips'):
        this_data = grouped_trips.get_group(tripid).sort_values(by='stop_sequence')

        # Extract and compute some of the possible features
        latitude = this_data.stop_lat
        longitude = this_data.stop_lon
        time_observed = this_data.observed_arrival_time

        _sched_arrival = this_data.scheduled_arrival_time.values.astype(np.int64) // 10 ** 9  # Convert to timestamp
        travel_time_scheduled = (_sched_arrival - _sched_arrival.min()) / 60
        delay = this_data.arrival_delay
        stop_length = (this_data.scheduled_departure_time - this_data.scheduled_departure_time).astype(np.int64) / 60e9
        travelled_distance = this_data.shape_dist_traveled / 1000.
        this_delay = np.array(delay, dtype=np.float32) / 60 / 60
        time_of_day = timestmp_to_time_of_day(_sched_arrival)
        direction_id = this_data.direction_id.values

        # Stack the ones that we selected
        locs = locals()
        features = np.stack([locs[f] for f in selected_features], axis=1).astype(np.float32)

        is_nan = np.logical_or(np.isnan(features).any(axis=1), np.isnan(this_delay))

        if (~is_nan).sum() > 2:
            delay_list.append(this_delay[~is_nan, np.newaxis])
            feature_list.append(features[~is_nan, :])
    return feature_list, delay_list

def main():
    # Training and testing data parameters
    start_hour = 0
    end_hour = 23
    company_name = 'sl'
    date_train_start = '2020_09_15'
    date_train_end = '2020_09_17'
    # Training features
    features = ['travelled_distance', 'travel_time_scheduled', 'stop_length', 'latitude', 'longitude', 'time_of_day']

    print(get_features(company_name, date_train_start, date_train_end, start_hour, end_hour, features))

if __name__=="__main__":
    main()
