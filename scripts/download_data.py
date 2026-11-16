"""Download one city's Inside Airbnb files into data/raw/<city>/.

Usage (run from the project folder):
    python scripts/download_data.py london <listings-url>

Get <listings-url> from https://insideairbnb.com/get-the-data/ : find the city,
right-click "listings.csv.gz" and copy the link. It looks like
    https://data.insideairbnb.com/united-kingdom/england/london/2025-09-14/data/listings.csv.gz
The other files for the same snapshot sit next to it, so we build their links from it.
"""

import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from airbnb.config import CITIES, RAW_DIR  # noqa: E402

# File name on the website -> where it sits relative to the listings link.
FILES = {
    "listings.csv.gz": "data/listings.csv.gz",
    "calendar.csv.gz": "data/calendar.csv.gz",
    "reviews.csv.gz": "data/reviews.csv.gz",
    "neighbourhoods.geojson": "visualisations/neighbourhoods.geojson",
}


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    city, listings_url = sys.argv[1], sys.argv[2]
    if city not in CITIES:
        sys.exit(f"Unknown city '{city}'. Choose one of: {', '.join(CITIES)}")
    if not listings_url.endswith("data/listings.csv.gz"):
        sys.exit("The link should end with data/listings.csv.gz")

    base = listings_url.removesuffix("data/listings.csv.gz")
    out_dir = RAW_DIR / city
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, rel in FILES.items():
        target = out_dir / name
        print(f"Downloading {name} ...", end=" ", flush=True)
        try:
            urllib.request.urlretrieve(base + rel, target)
            print(f"done ({target.stat().st_size / 1e6:.1f} MB)")
        except OSError as err:  # keep going so one missing file doesn't stop the rest
            print(f"FAILED: {err}")

    # Record which snapshot we used, for the README and the app's footer.
    snapshot = base.rstrip("/").split("/")[-1]
    (out_dir / "SNAPSHOT.txt").write_text(f"{snapshot}\n{listings_url}\n")
    print(f"Snapshot {snapshot} saved to {out_dir}")


if __name__ == "__main__":
    main()
