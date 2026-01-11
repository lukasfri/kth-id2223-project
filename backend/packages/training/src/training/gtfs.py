import os
from datetime import datetime, timezone
from email.utils import format_datetime
import zipfile
from training.common import FeedID, Operator
import training.__generated__.gtfs_realtime_pb2 as gtfs_realtime_pb2
import requests
import py7zr

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


def download_gtfs_rt_file(
    operator: Operator, feedId: FeedID, *, api_key: str, data_dir: str
):
    """Download GTFS-RT feed, using If-Modified-Since when possible."""
    file_name = f"{data_dir}/{operator.value}_{feedId.value}.pb"
    url = f"https://opendata.samtrafiken.se/gtfs-rt/{operator.value}/{feedId.value}.pb?key={api_key}"

    headers: dict[str, str] = {}

    if os.path.exists(file_name):
        # Use the local file's modification time for conditional GET
        mtime = os.path.getmtime(file_name)
        last_modified = format_datetime(datetime.fromtimestamp(mtime, tz=timezone.utc))
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