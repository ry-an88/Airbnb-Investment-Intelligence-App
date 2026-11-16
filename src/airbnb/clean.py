"""Clean the raw listings table.

Main jobs:
- turn text columns into numbers and dates (price arrives as text like "$1,250.00")
- flag, rather than delete, listings with missing or extreme prices
- mark which listings look "active"
- produce a simple data-quality report for the app and the docs
"""

import numpy as np
import pandas as pd

from airbnb.config import ACTIVE_REVIEW_WINDOW_DAYS, MAX_VALID_PRICE, MIN_VALID_PRICE


def parse_price(series: pd.Series) -> pd.Series:
    """Convert price text like "$1,250.00" to the number 1250.0.

    Inside Airbnb always writes a "$" sign, but for UK cities the value is in pounds.
    Anything that can't be read becomes NaN (missing).
    """
    cleaned = series.astype("string").str.replace(r"[^0-9.]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce").astype(float)


def parse_bathrooms(text: pd.Series) -> pd.Series:
    """Pull the number out of text like "1.5 shared baths". "Half-bath" counts as 0.5."""
    text = text.astype("string").str.lower()
    number = pd.to_numeric(text.str.extract(r"(\d+(?:\.\d+)?)")[0], errors="coerce").astype(float)
    return number.mask(number.isna() & text.str.contains("half", na=False), 0.5)


def to_bool(series: pd.Series) -> pd.Series:
    """Inside Airbnb stores booleans as "t"/"f". Keep missing values as missing."""
    return series.map({"t": True, "f": False})


def clean_listings(raw: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned copy of the listings table with helper columns added."""
    df = raw.copy()

    df["price"] = parse_price(df["price"])

    # Some snapshots have an empty numeric "bathrooms" column but a text version.
    if "bathrooms_text" in df.columns:
        from_text = parse_bathrooms(df["bathrooms_text"])
        existing = pd.to_numeric(df.get("bathrooms", from_text), errors="coerce").astype(float)
        df["bathrooms"] = existing.fillna(from_text)

    for col in ["host_is_superhost", "instant_bookable"]:
        if col in df.columns:
            df[col] = to_bool(df[col])

    for col in ["last_review", "last_scraped"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # A listing with no reviews has no reviews_per_month; zero is the honest value.
    df["reviews_per_month"] = df["reviews_per_month"].fillna(0)

    # Flag prices we don't trust instead of dropping rows, so counts stay complete.
    df["price_valid"] = df["price"].between(MIN_VALID_PRICE, MAX_VALID_PRICE)

    # "Active" = reviewed within the last year of the snapshot date.
    snapshot = df["last_scraped"].max() if "last_scraped" in df.columns else pd.NaT
    if pd.isna(snapshot):
        snapshot = df["last_review"].max()
    days_since_review = (snapshot - df["last_review"]).dt.days
    df["is_active"] = days_since_review <= ACTIVE_REVIEW_WINDOW_DAYS

    # Price bands make the app filter simpler than a raw slider for most users.
    df["price_band"] = pd.cut(
        df["price"],
        bins=[0, 75, 150, 250, 500, np.inf],
        labels=["Under £75", "£75–150", "£150–250", "£250–500", "£500+"],
    )
    return df


def data_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    """Summarise data issues so we can show them in the app and the documentation."""
    total = len(df)
    checks = {
        "Listings in snapshot": total,
        "Missing or unreadable price": int(df["price"].isna().sum()),
        f"Price outside £{MIN_VALID_PRICE}–£{MAX_VALID_PRICE} (excluded from averages)":
            int((~df["price_valid"] & df["price"].notna()).sum()),
        "No reviews ever": int((df["number_of_reviews"] == 0).sum()),
        "Missing overall review score": int(df["review_scores_rating"].isna().sum()),
        "Missing bedrooms": int(df["bedrooms"].isna().sum()) if "bedrooms" in df else None,
        "Not active (no review in last 12 months)": int((~df["is_active"]).sum()),
    }
    report = pd.DataFrame({"check": checks.keys(), "count": checks.values()})
    report["share_of_listings"] = (report["count"] / total).round(3)
    return report
