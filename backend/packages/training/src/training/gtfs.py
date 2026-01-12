import os
import pandas as pd
from datetime import datetime, timezone
import datetime
from email.utils import formatdate
import zipfile
from training.static_data import StaticData
from training.data_processing import feed_message_to_trip_update_dataframe, join_static_data_on_rt_trip_updates 
from training.common import FeedID, Operator
import training.__generated__.gtfs_realtime_pb2 as gtfs_realtime_pb2
import requests

def load_gtfs_frame_from_files(
    file_paths: list[str],
    gtfs_static_data: StaticData
) -> pd.DataFrame:
    trips = []
    for file_path in file_paths:
        gtfs_feed_message = load_pb_file(file_path)
        trip_update_df = feed_message_to_trip_update_dataframe(gtfs_feed_message)
        trip_update_df = join_static_data_on_rt_trip_updates(gtfs_static_data, trip_update_df)
        trips.append(trip_update_df)

    trips = pd.concat(trips, ignore_index=True)
    return trips

def list_gtfs_files(base_path: str, start_dt: datetime.datetime, end_dt: datetime.datetime):
    found_files = []

    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=datetime.timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=datetime.timezone.utc)

    if not os.path.exists(base_path):
        return []

    with os.scandir(base_path) as years:
        for year_entry in years:
            if not year_entry.is_dir() or not year_entry.name.isdigit():
                continue
            
            year = int(year_entry.name)
            if not (start_dt.year <= year <= end_dt.year):
                continue

            with os.scandir(year_entry.path) as months:
                for month_entry in months:
                    if not month_entry.is_dir() or not month_entry.name.isdigit():
                        continue
                    
                    month = int(month_entry.name)
                    if year == start_dt.year and month < start_dt.month:
                        continue
                    if year == end_dt.year and month > end_dt.month:
                        continue

                    # 3. DAY Level
                    with os.scandir(month_entry.path) as days:
                        for day_entry in days:
                            if not day_entry.is_dir() or not day_entry.name.isdigit():
                                continue
                            
                            day = int(day_entry.name)
                            
                            current_date = datetime.date(year, month, day)
                            
                            if current_date < start_dt.date() or current_date > end_dt.date():
                                continue

                            with os.scandir(day_entry.path) as hours:
                                for hour_entry in hours:
                                    if not hour_entry.is_dir() or not hour_entry.name.isdigit():
                                        continue
                                    
                                    hour = int(hour_entry.name)
                                    
                                    # Lower bound check
                                    if current_date == start_dt.date() and hour < start_dt.hour:
                                        continue
                                    # Upper bound check
                                    if current_date == end_dt.date() and hour > end_dt.hour:
                                        continue
                                    with os.scandir(hour_entry.path) as files:
                                        for file_entry in files:
                                            # Parse timestamp from filename
                                            ts_str = file_entry.name.split('tripupdates-')[-1].replace('.pb', '')
                                            
                                            # Standard parsing
                                            file_dt = datetime.datetime.strptime(ts_str, "%Y-%m-%dT%H-%M-%SZ")
                                            file_dt = file_dt.replace(tzinfo=datetime.timezone.utc)
                                            
                                            if start_dt <= file_dt <= end_dt:
                                                found_files.append(file_entry.path)

    return found_files

def download_gtfs_static_file(operator: Operator, *, api_key: str, data_dir: str):
    file_name = f"{data_dir}/{operator.value}_gtfs_static.zip"

    if os.path.exists(file_name):
        print(f"File {file_name} already exists. Skipping download.")
        return

    url = f"https://opendata.samtrafiken.se/gtfs/{operator.value}/{operator.value}.zip?key={api_key}"
    print(f"Downloading {url}...")
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(
            f"Failed to download file: {response.status_code} {response.text}"
        )

    with open(file_name, "wb") as f:
        f.write(response.content)
    
    print(f"Extracting {file_name}...")
    
    with zipfile.ZipFile(file_name, 'r') as zip_ref:
        zip_ref.extractall(f"{data_dir}/data-tmp")

def download_gtfs_static_file_with_if_mod(operator: "Operator", *, api_key: str, data_dir: str):
    file_name = f"{data_dir}/{operator.value}_gtfs_static.zip"
    url = f"https://opendata.samtrafiken.se/gtfs/{operator.value}/{operator.value}.zip?key={api_key}"

    os.makedirs(data_dir, exist_ok=True)

    headers: dict[str, str] = {}

   
    if os.path.exists(file_name):
        # Use local file mtime for HTTP If-Modified-Since (IMF-fixdate format)
        mtime = os.path.getmtime(file_name)
        last_modified = formatdate(timeval=mtime, usegmt=True)  # ex "Mon, 13 Jul 2020 04:24:36 GMT"
        headers["If-Modified-Since"] = last_modified
        print(f"File {file_name} exists. Sending If-Modified-Since: {last_modified}")
    else:
        print(f"No existing file found. Downloading {url} without If-Modified-Since...")

    response = requests.get(url, headers=headers)

    if response.status_code == 304:
        print(
            f"GTFS static for {operator.value} not modified. Using existing file {file_name}."
        )
        return

    elif response.status_code == 200:
        with open(file_name, "wb") as f:
            f.write(response.content)
        print(f"Downloaded and saved GTFS static zip to {file_name}.")

    else:
        raise Exception(
            f"Failed to download file: {response.status_code} {response.text}"
        )


    with zipfile.ZipFile(file_name, 'r') as zip_ref:
        zip_ref.extractall(f"{data_dir}/data-tmp")

    return
    
def download_gtfs_rt_file(
    operator: Operator, feedId: FeedID, *, api_key: str, data_dir: str
):
    """Download GTFS-RT feed, using If-Modified-Since when possible."""
    file_name = f"{data_dir}/{operator.value}_{feedId.value}.pb"
    url = f"https://opendata.samtrafiken.se/gtfs-rt/{operator.value}/{feedId.value}.pb?key={api_key}"

    headers: dict[str, str] = {}

    if os.path.exists(file_name):
        # Use local file mtime for HTTP If-Modified-Since (IMF-fixdate format)
        mtime = os.path.getmtime(file_name)
        last_modified = formatdate(timeval=mtime, usegmt=True)  # ex "Mon, 13 Jul 2020 04:24:36 GMT"
        headers["If-Modified-Since"] = last_modified
        print(f"File {file_name} exists. Sending If-Modified-Since: {last_modified}")
    else:
        print(f"No existing file found. Downloading {url} without If-Modified-Since...")

    response = requests.get(url, headers=headers)

    if response.status_code == 304:
        # Not modified; keep existing file
        print(
            f"GTFS-RT feed for {operator.value}/{feedId.value} not modified. "
            f"Using existing file {file_name}."
        )
        return

    if response.status_code != 200:
        raise Exception(
            f"Failed to download GTFS-RT feed: {response.status_code} {response.text}"
        )

    with open(file_name, "wb") as f:
        f.write(response.content)

    print(f"Downloaded and saved GTFS-RT feed to {file_name}.")


def load_pb_file(file_path: str) -> gtfs_realtime_pb2.FeedMessage:
    with open(file_path, "rb") as f:
        data = f.read()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(data)
    return feed

def load_gtfs_rt_immediately(operator: Operator, feedId: FeedID, *, api_key: str) -> gtfs_realtime_pb2.FeedMessage:
    url = f"https://opendata.samtrafiken.se/gtfs-rt/{operator.value}/{feedId.value}.pb?key={api_key}"

    print(f"Downloading {url}...")
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Failed to download file: {response.status_code} {response.text}")
    
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    return feed
    
