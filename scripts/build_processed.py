"""Turn raw Inside Airbnb files into the cleaned tables the app reads.

Usage (run from the project folder):
    python scripts/build_processed.py london

Outputs in data/processed/<city>/:
    listings.parquet       cleaned listings with occupancy and revenue estimates
    data_quality.csv       counts of missing values, outliers and inactive listings
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from airbnb.clean import clean_listings, data_quality_report  # noqa: E402
from airbnb.config import CITIES, PROCESSED_DIR  # noqa: E402
from airbnb.load import DataFileMissing, load_calendar, load_listings  # noqa: E402
from airbnb.metrics import add_revenue_metrics, calendar_unavailable_share  # noqa: E402


def build(city: str) -> None:
    print(f"[{city}] loading listings ...")
    listings = load_listings(city)

    print(f"[{city}] cleaning {len(listings):,} listings ...")
    listings = add_revenue_metrics(clean_listings(listings))

    # The calendar is optional: useful as a second demand signal, but not required.
    try:
        print(f"[{city}] loading calendar ...")
        share = calendar_unavailable_share(load_calendar(city), days=90)
        listings = listings.merge(share, on="id", how="left")
    except DataFileMissing as err:
        print(f"[{city}] skipping calendar: {err}")

    out_dir = PROCESSED_DIR / city
    out_dir.mkdir(parents=True, exist_ok=True)
    listings.to_parquet(out_dir / "listings.parquet", index=False)
    data_quality_report(listings).to_csv(out_dir / "data_quality.csv", index=False)
    print(f"[{city}] saved to {out_dir}")


if __name__ == "__main__":
    cities = sys.argv[1:] or ["london"]
    for c in cities:
        if c not in CITIES:
            sys.exit(f"Unknown city '{c}'. Choose from: {', '.join(CITIES)}")
        try:
            build(c)
        except DataFileMissing as err:
            sys.exit(str(err))
