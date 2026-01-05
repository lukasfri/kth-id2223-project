import os
from typing import Optional
import zipfile
import py7zr
import requests
from common import Operator
from datetime import date

def date_to_str(date: date) -> str:
    return f"{date.year:04d}-{date.month:02d}-{date.day:02d}"

def download_koda_rt_file(operator: Operator, feedId: str, date: date, hour: Optional[int] = None, *, api_key: str, data_dir: str):
    date_str = date_to_str(date)
    file_name = f"{data_dir}/{operator.value}_{date_str}.7z"

    if os.path.exists(file_name):
        print(f"File {file_name} already exists. Skipping download.")
        return
    
    url = f"https://api.koda.trafiklab.se/KoDa/api/v2/gtfs-rt/{operator.value}/{feedId}?date={date}&key={api_key}";

    print(f"Downloading {url}...")
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Failed to download file: {response.status_code} {response.text}")

    with open(file_name, 'wb') as f:
        f.write(response.content)
    
    print(f"Extracting {file_name}...")
    with py7zr.SevenZipFile(file_name, mode='r') as z:
        z.extractall(f"{data_dir}/data-tmp")


def download_koda_static_file(operator: Operator, date: date, *, api_key: str, data_dir: str):
    date_str = date_to_str(date)
    file_name = f"{data_dir}/{operator.value}_{date_str}.zip"

    if os.path.exists(file_name):
        print(f"File {file_name} already exists. Skipping download.")
        return
    
    url = f"https://api.koda.trafiklab.se/KoDa/api/v2/gtfs-static/{operator.value}?date={date_str}&key={api_key}";

    print(f"Downloading {url}...")
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Failed to download file: {response.status_code} {response.text}")

    with open(file_name, 'wb') as f:
        f.write(response.content)
    
    print(f"Extracting {file_name}...")
    # with py7zr.SevenZipFile(file_name, mode='r') as z:
    #     z.extractall('./data-tmp')
    with zipfile.ZipFile(file_name, 'r') as zip_ref:
        zip_ref.extractall(f"{data_dir}/data-tmp")
