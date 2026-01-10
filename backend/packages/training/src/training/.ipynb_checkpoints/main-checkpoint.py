import os
from dotenv import load_dotenv
import gtfs_kit as gk
import pathlib as pl
from backend.src.common import Operator

def main():
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    if not API_KEY:
        raise ValueError("API_KEY not found in environment variables")
    
    data_dir = "./data"

    # Use one of 'blekinge', 'dintur', 'dt', 'gotland', 'halland', 'klt', 'krono', 'orebro', 'otraf', 'sj', 'skane', 'sl', 'sormland', 'ul', 'varm', 'vastmanland', 'vt', 'xt'
    operator = Operator.SL
    year = 2024
    month = 6
    day = 15
    download_koda_file(operator, year, month, day, API_KEY, data_dir=data_dir)

    feedId = "ServiceAlerts"
    download_gtfs_rt_file(operator, feedId, year, month, day, 10, API_KEY, data_dir=data_dir)
    
    sl_path = pl.Path(f"{data_dir}/sl_2024-06-15.zip")

    a = gk.list_feed(sl_path)

    print(a)

    service_alert_file = f"{data_dir}/data-tmp-rt/sl/ServiceAlerts/2024/06/15/10/sl-servicealerts-2024-06-15T10-00-03Z.pb"

    service_alert = load_feed_file(service_alert_file)
    debug_print_feed(service_alert)
    

if __name__ == "__main__":
    main()