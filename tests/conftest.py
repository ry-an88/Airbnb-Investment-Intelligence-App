"""Shared test data: a tiny fake listings table shaped like Inside Airbnb's."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture
def raw_listings() -> pd.DataFrame:
    return pd.DataFrame({
        "id": [1, 2, 3, 4],
        "name": ["Flat A", "Room B", "House C", "Flat D"],
        "neighbourhood_cleansed": ["Camden", "Camden", "Hackney", "Hackney"],
        "latitude": [51.54, 51.55, 51.55, 51.54],
        "longitude": [-0.14, -0.15, -0.06, -0.05],
        "room_type": ["Entire home/apt", "Private room", "Entire home/apt", "Entire home/apt"],
        "bathrooms": [None, None, None, None],
        "bathrooms_text": ["1 bath", "1 shared bath", "Half-bath", None],
        "bedrooms": [1, 1, 3, None],
        "price": ["$150.00", "$60.00", "$5,000.00", None],
        "minimum_nights": [2, 1, 5, 3],
        "availability_365": [200, 300, 100, 0],
        "number_of_reviews": [100, 30, 10, 0],
        "number_of_reviews_ltm": [40, 12, 3, 0],
        "reviews_per_month": [3.0, 1.0, 0.2, None],
        "last_review": ["2025-08-01", "2025-07-01", "2023-01-01", None],
        "last_scraped": ["2025-09-14"] * 4,
        "review_scores_rating": [4.9, 4.6, 4.2, None],
        "host_is_superhost": ["t", "f", "f", None],
        "instant_bookable": ["t", "t", "f", "f"],
        "city": ["london"] * 4,
    })
