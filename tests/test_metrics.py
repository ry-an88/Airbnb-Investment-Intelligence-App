import pandas as pd

from airbnb.clean import clean_listings
from airbnb.config import LONDON_NIGHT_CAP, MAX_OCCUPANCY
from airbnb.metrics import add_revenue_metrics, calendar_unavailable_share


def test_nights_follow_review_model(raw_listings):
    df = add_revenue_metrics(clean_listings(raw_listings))
    # Flat A: 40 reviews / 0.5 review rate = 80 stays x 3 nights = 240
    assert df.loc[0, "est_nights_booked"] == 240
    # Room B: 12 / 0.5 = 24 stays x 3 nights = 72
    assert df.loc[1, "est_nights_booked"] == 72


def test_nights_are_capped_at_max_occupancy(raw_listings):
    raw_listings.loc[0, "number_of_reviews_ltm"] = 200  # implausibly busy
    df = add_revenue_metrics(clean_listings(raw_listings))
    assert df.loc[0, "est_nights_booked"] == round(MAX_OCCUPANCY * 365, 1)


def test_london_entire_home_revenue_capped_at_90_nights(raw_listings):
    df = add_revenue_metrics(clean_listings(raw_listings))
    assert df.loc[0, "est_annual_revenue_capped"] == LONDON_NIGHT_CAP * 150
    assert bool(df.loc[0, "hits_90_night_cap"])
    # Private rooms are not subject to the cap
    assert df.loc[1, "est_annual_revenue_capped"] == df.loc[1, "est_annual_revenue"]


def test_invalid_price_gives_missing_revenue_not_wrong_revenue(raw_listings):
    df = add_revenue_metrics(clean_listings(raw_listings))
    assert pd.isna(df.loc[2, "est_annual_revenue"])


def test_calendar_unavailable_share():
    cal = pd.DataFrame({
        "listing_id": [1] * 4,
        "date": pd.date_range("2025-09-14", periods=4),
        "available": ["f", "f", "t", "t"],
    })
    result = calendar_unavailable_share(cal, days=90)
    assert result.loc[0, "unavailable_share_90d"] == 0.5
