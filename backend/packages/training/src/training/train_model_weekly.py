from training.model_training import train_and_save_route_model
from training.koda import download_koda_static_file
from training.data_pipeline import download_data_in_range
from training.common import Operator, FeedID

from datetime import date, datetime
import argparse
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("start_date")
    parser.add_argument("end_date")
    parser.add_argument("data_dir")

    args = parser.parse_args()

    start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()

    koda_api_key = os.environ.get("KODA_API_KEY", "")

    download_koda_static_file(Operator.SL, start_date, api_key=koda_api_key, data_dir=args.data_dir)
    download_data_in_range(start_date, end_date)

    STAM_BUSES_ROUTE_SET = {    "9011001000100000", 
                                "9011001000200000",
                                "9011001000300000",
                                "9011001000400000"}

    print("Starting model training")
    train_and_save_route_model(STAM_BUSES_ROUTE_SET, start_date, end_date)

