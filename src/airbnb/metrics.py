"""Occupancy and revenue estimates.

Inside Airbnb does not tell us how many nights a listing was actually booked. We
estimate it from reviews (a stay usually comes before a review), following the
"San Francisco model" that Inside Airbnb itself uses:

    estimated stays per year  = reviews in last 12 months / REVIEW_RATE
    estimated nights per year = stays x length of stay (at least AVG_LENGTH_OF_STAY,
                                or the listing's minimum nights if that's higher)
    occupancy proxy           = nights / 365, capped at MAX_OCCUPANCY
    estimated annual revenue  = nights x nightly price

We do NOT use the calendar's "unavailable" nights as bookings, because a night can
be unavailable simply because the host blocked it. The calendar is used only as a
secondary signal (see calendar_unavailable_share).
"""

import numpy as np
import pandas as pd

from airbnb.config import AVG_LENGTH_OF_STAY, LONDON_NIGHT_CAP, MAX_OCCUPANCY, REVIEW_RATE

# Stays longer than a month are really medium-term lets, so we cap the stay length.
MAX_STAY_LENGTH = 30


def estimate_nights_booked(df: pd.DataFrame) -> pd.Series:
    """Estimated nights booked per year for each listing (see module docstring)."""
    if "number_of_reviews_ltm" in df.columns:
        reviews_last_year = df["number_of_reviews_ltm"].fillna(0)
    else:
        reviews_last_year = df["reviews_per_month"].fillna(0) * 12

    stays = reviews_last_year / REVIEW_RATE
    stay_length = np.clip(df["minimum_nights"].fillna(1), AVG_LENGTH_OF_STAY, MAX_STAY_LENGTH)
    nights = stays * stay_length
    return nights.clip(upper=MAX_OCCUPANCY * 365)


def add_revenue_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add nights, occupancy and revenue estimates to a cleaned listings table.

    For London, entire homes are also given a "90-night capped" revenue: what the
    listing could legally earn without planning permission.
    """
    out = df.copy()
    out["est_nights_booked"] = estimate_nights_booked(out).round(1)
    out["occupancy_proxy"] = (out["est_nights_booked"] / 365).round(3)

    # Only use trusted prices; untrusted prices give a missing revenue, not a wrong one.
    price = out["price"].where(out["price_valid"])
    out["est_annual_revenue"] = (out["est_nights_booked"] * price).round(0)

    is_london_entire_home = (out["city"] == "london") & (out["room_type"] == "Entire home/apt")
    capped_nights = out["est_nights_booked"].where(
        ~is_london_entire_home, out["est_nights_booked"].clip(upper=LONDON_NIGHT_CAP)
    )
    out["est_annual_revenue_capped"] = (capped_nights * price).round(0)
    out["hits_90_night_cap"] = is_london_entire_home & (out["est_nights_booked"] > LONDON_NIGHT_CAP)
    return out


def calendar_unavailable_share(calendar: pd.DataFrame, days: int = 90) -> pd.DataFrame:
    """Share of the next `days` days marked unavailable, per listing.

    Treat this as an UPPER BOUND on demand: unavailable can mean booked OR blocked.
    """
    start = calendar["date"].min()
    window = calendar[calendar["date"] < start + pd.Timedelta(days=days)]
    unavailable = window["available"].eq("f")
    share = unavailable.groupby(window["listing_id"]).mean().rename(f"unavailable_share_{days}d")
    return share.reset_index().rename(columns={"listing_id": "id"})
