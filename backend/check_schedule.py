#!/usr/bin/env python
import argparse
import os
from datetime import datetime
from pathlib import Path
import pandas as pd
def parse_gtfs_date(value) -> datetime.date:
    """Parse GTFS YYYYMMDD date value into a date."""
    s = str(value)
    return datetime.strptime(s, "%Y%m%d").date()
def inspect_static_schedule(static_dir: Path) -> None:
    calendar_path = static_dir / "calendar.txt"
    calendar_dates_path = static_dir / "calendar_dates.txt"
    print(f"Inspecting static GTFS in: {static_dir.resolve()}")
    print()
    spans = []
    # calendar.txt: regular service date ranges
    if calendar_path.exists():
        cal = pd.read_csv(calendar_path, dtype={"service_id": "string"})
        cal["start_date"] = cal["start_date"].apply(parse_gtfs_date)
        cal["end_date"] = cal["end_date"].apply(parse_gtfs_date)
        n_services = cal["service_id"].nunique()
        start = cal["start_date"].min()
        end = cal["end_date"].max()
        span_days = (end - start).days + 1
        spans.append(span_days)
        print("calendar.txt")
        print(f"  service_ids: {n_services}")
        print(f"  overall date span: {start} -> {end} ({span_days} days)")
        print()
    else:
        print(f"No calendar.txt found in {static_dir}")
        print()
    # calendar_dates.txt: exceptions / added / removed service
    if calendar_dates_path.exists():
        cald = pd.read_csv(calendar_dates_path, dtype={"service_id": "string"})
        cald["date"] = cald["date"].apply(parse_gtfs_date)
        n_services_ex = cald["service_id"].nunique()
        start_ex = cald["date"].min()
        end_ex = cald["date"].max()
        span_ex_days = (end_ex - start_ex).days + 1
        spans.append(span_ex_days)
        print("calendar_dates.txt")
        print(f"  service_ids: {n_services_ex}")
        print(f"  overall date span: {start_ex} -> {end_ex} ({span_ex_days} days)")
        print()
    else:
        print(f"No calendar_dates.txt found in {static_dir}")
        print()
    # Verdict
    if not spans:
        print("Verdict: could not determine schedule span (no calendar files).")
        return
    max_span = max(spans)
    if max_span <= 1:
        print("Verdict: static schedule appears to cover a SINGLE day.")
    elif max_span <= 7:
        print("Verdict: static schedule appears to cover up to about a WEEK.")
    else:
        print("Verdict: static schedule appears to cover MULTIPLE WEEKS or more.")
def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether GTFS static data covers a single day or a longer period "
            "based on calendar.txt/calendar_dates.txt."
        )
    )
    parser.add_argument(
        "--static-dir",
        type=Path,
        default=None,
        help=(
            "Path to folder containing GTFS static files "
            "(trips.txt, stop_times.txt, calendar.txt, ...). "
            "Defaults to ROOT_DIR/data/data-tmp."
        ),
    )
    args = parser.parse_args()
    if args.static_dir is None:
        root_dir = Path(os.environ.get("ROOT_DIR", "."))
        static_dir = root_dir / "data" / "data-tmp"
    else:
        static_dir = args.static_dir
    inspect_static_schedule(static_dir)
if __name__ == "__main__":
    main()
