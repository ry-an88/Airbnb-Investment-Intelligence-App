"""Read raw Inside Airbnb files from data/raw/<city>/.

Each loader raises a clear DataFileMissing error if the file isn't there, so the
app can show a friendly message instead of crashing with a stack trace.
"""

from pathlib import Path

import pandas as pd

from airbnb.config import RAW_DIR, RAW_FILES

# Only the listing columns the project actually uses. Reading fewer columns makes
# loading much faster (the full file has ~75 columns, many of them long text).
LISTING_COLUMNS = [
    "id", "name", "host_id", "host_is_superhost", "host_listings_count",
    "neighbourhood_cleansed", "latitude", "longitude",
    "property_type", "room_type", "accommodates", "bathrooms", "bathrooms_text",
    "bedrooms", "beds", "price", "minimum_nights",
    "availability_30", "availability_365",
    "number_of_reviews", "number_of_reviews_ltm", "last_review", "reviews_per_month",
    "review_scores_rating", "review_scores_cleanliness", "review_scores_location",
    "review_scores_value", "review_scores_communication", "review_scores_checkin",
    "license", "instant_bookable", "last_scraped",
    # Newer snapshots include Inside Airbnb's own estimates; we keep them for comparison.
    "estimated_occupancy_l365d", "estimated_revenue_l365d",
]


class DataFileMissing(FileNotFoundError):
    """Raised when an expected Inside Airbnb file hasn't been downloaded yet."""


def raw_path(city: str, file_key: str, raw_dir: Path = RAW_DIR) -> Path:
    """Return the path of one raw file, e.g. data/raw/london/listings.csv.gz."""
    path = Path(raw_dir) / city / RAW_FILES[file_key]
    if not path.exists():
        raise DataFileMissing(
            f"Missing {path}. Download it from https://insideairbnb.com/get-the-data/ "
            f"and save it in {path.parent}."
        )
    return path


def load_listings(city: str, raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Load the detailed listings file, keeping only the columns we need.

    Columns missing from older snapshots are simply skipped rather than failing.
    """
    path = raw_path(city, "listings", raw_dir)
    available = pd.read_csv(path, nrows=0).columns
    usecols = [c for c in LISTING_COLUMNS if c in available]
    df = pd.read_csv(path, usecols=usecols, low_memory=False)
    df["city"] = city
    return df


def load_calendar(city: str, raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Load the calendar file (one row per listing per day for the next year)."""
    path = raw_path(city, "calendar", raw_dir)
    return pd.read_csv(
        path,
        usecols=["listing_id", "date", "available"],
        parse_dates=["date"],
    )


def load_reviews(city: str, raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Load the full reviews file (one row per review, with the comment text)."""
    path = raw_path(city, "reviews", raw_dir)
    return pd.read_csv(
        path,
        usecols=["listing_id", "id", "date", "comments"],
        parse_dates=["date"],
    )
