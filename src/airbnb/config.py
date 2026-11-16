"""Project-wide settings: file paths, supported cities and modelling assumptions.

Keeping every assumption in one place means the app, the docs and the tests all
use the same numbers, and an assumption can be changed without hunting through code.
"""

from pathlib import Path

# Folder layout. RAW_DIR holds the files exactly as downloaded from Inside Airbnb
# (never edited); PROCESSED_DIR holds the cleaned outputs the app reads.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# UK cities that Inside Airbnb publishes. The key is the folder name under
# data/raw/, the value is the label shown in the app. London is the required baseline.
CITIES = {
    "london": "London",
    "bristol": "Bristol",
    "edinburgh": "Edinburgh",
    "greater-manchester": "Greater Manchester",
}

# The Inside Airbnb files we use for each city.
RAW_FILES = {
    "listings": "listings.csv.gz",            # detailed listings
    "calendar": "calendar.csv.gz",            # 365 days of availability per listing
    "reviews": "reviews.csv.gz",              # full review text
    "neighbourhoods_geojson": "neighbourhoods.geojson",
}

# ---------------------------------------------------------------------------
# Occupancy model assumptions (based on Inside Airbnb's own "San Francisco model").
# Not every guest leaves a review, so reviews are scaled up to estimate bookings.
# ---------------------------------------------------------------------------
REVIEW_RATE = 0.50          # assume 1 in 2 stays leaves a review
AVG_LENGTH_OF_STAY = 3.0    # nights per booking, used when minimum_nights is lower
MAX_OCCUPANCY = 0.70        # cap so a handful of very busy listings don't skew results

# London rule: without planning permission, a whole home can only be let short term
# for 90 nights in a calendar year. We cap entire-home estimates at this figure.
LONDON_NIGHT_CAP = 90

# Price cleaning: nightly prices outside this range are treated as data errors or
# extreme outliers and excluded from averages (they stay in the raw data).
MIN_VALID_PRICE = 10
MAX_VALID_PRICE = 2_000

# A listing counts as "active" if it had a review in the last 12 months of the snapshot.
ACTIVE_REVIEW_WINDOW_DAYS = 365
