from training.data_pipeline import download_data_in_range
from training.koda import download_koda_static_file
from training.gtfs import download_gtfs_rt_file, download_gtfs_static_file_with_if_mod
from training.common import *
from datetime import date
import os

#download_data_in_range(date(2024, 6, 15), date(2024, 6, 15+7))

api_key_static = os.environ.get("KODA_API_KEY", "")
root_dir = os.environ.get("ROOT_DIR", ".")
sl = Operator.SL
#tripUps = FeedID.TripUpdates


download_koda_static_file(operator=sl, date=date(2026,1,5), api_key=api_key_static, data_dir=f"{root_dir}/data/koda-static")

download_data_in_range(start_date=date(2026,1,5), end_date=date(2026,1,5))
# api_key_rt = os.environ.get("REGION_RT_API_KEY", "")
# root_dir = os.environ.get("ROOT_DIR", ".")
# sl = Operator.SL
# tripUps = FeedID.TripUpdates
#
# download_gtfs_static_file_with_if_mod(operator=sl, api_key=api_key_static, data_dir=f"{root_dir}/data")
# download_gtfs_rt_file(operator=sl, feedId=tripUps, api_key=api_key_rt, data_dir=f"{root_dir}/data")
