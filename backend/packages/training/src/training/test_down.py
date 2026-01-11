#from data_pipeline import download_data_in_range
from training.gtfs import download_gtfs_rt_file, download_gtfs_static_file_with_if_mod
from training.common import *
from datetime import date
import os

#download_data_in_range(date(2024, 6, 15), date(2024, 6, 15+7))

api_key_static = os.environ.get("REGION_STATIC_API_KEY", "")
api_key_rt = os.environ.get("REGION_RT_API_KEY", "")
root_dir = os.environ.get("ROOT_DIR", ".")
sl = Operator.SL
tripUps = FeedID.TripUpdates

download_gtfs_static_file_with_if_mod(operator=sl, api_key=api_key_static, data_dir=f"{root_dir}/data")
download_gtfs_rt_file(operator=sl, feedId=tripUps, api_key=api_key_rt, data_dir=f"{root_dir}/data")
