import os
from common import Operator
import __generated__.gtfs_realtime_pb2 as gtfs_realtime_pb2
import requests
import py7zr

def download_gtfs_static_file(operator: Operator, *, api_key: str, data_dir: str):
    file_name = f"{data_dir}/{operator.value}_gtfs_static.zip"

    if os.path.exists(file_name):
        print(f"File {file_name} already exists. Skipping download.")
        return
    
    url = f"https://opendata.samtrafiken.se/gtfs/{operator.value}/{operator.value}.zip?key={api_key}";
    
    print(f"Downloading {url}...")
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Failed to download file: {response.status_code} {response.text}")
    
    with open(file_name, 'wb') as f:
        f.write(response.content)

def download_gtfs_rt_file(operator: Operator, feedId: str, *, api_key: str, data_dir: str):
    file_name = f"{data_dir}/{operator.value}_{feedId}.pb"

    # Check if data is already downloaded
    if os.path.exists(file_name):
        print(f"File {file_name} already exists. Skipping download.")
        return

    url = f"https://opendata.samtrafiken.se/gtfs-rt/{operator.value}/{feedId}.pb?key={api_key}";

    print(f"Downloading {url}...")
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Failed to download file: {response.status_code} {response.text}")

    with open(file_name, 'wb') as f:
        f.write(response.content)

def load_pb_file(file_path: str) -> gtfs_realtime_pb2.FeedMessage:
    with open(file_path, 'rb') as f:
        data = f.read()
    
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(data)
    return feed
