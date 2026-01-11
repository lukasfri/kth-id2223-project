import asyncio
from datetime import datetime, timezone
import os

import dotenv
import requests
from training.common import FeedID, Operator
from email.utils import format_datetime


# backend/data/koda-rt/data-tmp-rt/sl/TripUpdates/2024/06/15/04/sl-tripupdates-2024-06-15T04-00-05Z.pb
def file_path(data_path: str, operator: Operator, timestamp: datetime) -> str:
    return f"{data_path}/{operator.value}/TripUpdates/{timestamp.year:04d}/{timestamp.month:02d}/{timestamp.day:02d}/{timestamp.hour:02d}/{operator.value.lower()}-tripupdates-{timestamp.year:04d}-{timestamp.month:02d}-{timestamp.day:02d}T{timestamp.hour:02d}-{timestamp.minute:02d}-{timestamp.second:02d}Z.pb"

testFilePath = file_path("/backend/data/koda-rt/data-tmp-rt", Operator.SL, datetime(2024, 6, 15, 4, 0, 5))
resultFilePath = "/backend/data/koda-rt/data-tmp-rt/sl/TripUpdates/2024/06/15/04/sl-tripupdates-2024-06-15T04-00-05Z.pb"
assert testFilePath == resultFilePath, f"Expected {resultFilePath}, but got {testFilePath}"


def download_gtfs_rt_file(
    operator: Operator, feedId: FeedID, *, api_key: str, data_dir: str
):
    """Download GTFS-RT feed, using If-Modified-Since when possible."""
    file_name = file_path(data_dir, operator, datetime.now(timezone.utc))
    url = f"https://opendata.samtrafiken.se/gtfs-rt/{operator.value}/{feedId.value}.pb?key={api_key}"

    headers: dict[str, str] = {}

    # if os.path.exists(file_name):
    #     # Use the local file's modification time for conditional GET
    #     mtime = os.path.getmtime(file_name)
    #     last_modified = format_datetime(datetime.fromtimestamp(mtime, tz=timezone.utc))
    #     headers["If-Modified-Since"] = last_modified
    #     print(f"File {file_name} exists. Sending If-Modified-Since: {last_modified}")
    # else:
    #     print(f"No existing file found. Downloading {url} without If-Modified-Since...")

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

    os.makedirs(os.path.dirname(file_name), exist_ok=True)

    with open(file_name, "wb") as f:
        f.write(response.content)

    print(f"Downloaded and saved GTFS-RT feed to {file_name}.")


async def run_periodically(interval: int):
    """Run the downloader every `interval` seconds."""
    while True:
        try:
            # You might want to load these from env vars or config
            api_key = os.environ.get("GTFS_REGIONAL_RT_API_KEY")

            if not api_key:
                raise ValueError("GTFS_REGIONAL_RT_API_KEY environment variable not set")
            
            # Since download_gtfs_rt_file is blocking (requests), run it in a thread executor
            # to avoid blocking the event loop if you add more async tasks later.
            await asyncio.to_thread(
                download_gtfs_rt_file, 
                Operator.SL, 
                FeedID.TripUpdates, 
                api_key=api_key, 
                data_dir="data/gtfs-rt/data-tmp"
            )
        except Exception as e:
            print(f"Error during download: {e}")
        
        await asyncio.sleep(interval)

def main() -> None:
    dotenv.load_dotenv()
    
    interval = 15  # 15 seconds
    asyncio.run(run_periodically(interval))

if __name__ == "__main__":
    main()