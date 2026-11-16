"""Transparent investment score.

How it works, in plain English:
1. Group active listings by area (or by property type) and work out a few factors,
   such as median revenue and average guest rating.
2. Turn each factor into a 0–100 percentile: 100 means "best area on this factor",
   0 means "worst". This puts factors measured in pounds, ratings and counts on
   the same scale.
3. Multiply each percentile by a weight and add them up. The weights depend on the
   investor persona, and always add up to 1, so the final score is also 0–100.

Because the score is just a weighted sum, every point can be traced back to a
factor. The `*_points` columns show exactly how much each factor contributed.
"""

import pandas as pd

# Each factor: the column it uses and whether higher values are better.
FACTORS = {
    "revenue": {"column": "median_revenue", "higher_is_better": True,
                "label": "Revenue potential (median estimated annual revenue)"},
    "demand": {"column": "median_occupancy", "higher_is_better": True,
               "label": "Demand (median occupancy proxy)"},
    "satisfaction": {"column": "avg_rating", "higher_is_better": True,
                     "label": "Guest satisfaction (average review score)"},
    "competition": {"column": "active_listings", "higher_is_better": False,
                    "label": "Low competition (fewer active listings)"},
}

# Persona weights. Each row must add up to 1.0 (checked in the tests).
PERSONA_WEIGHTS = {
    "Balanced investor": {"revenue": 0.35, "demand": 0.25, "satisfaction": 0.25, "competition": 0.15},
    "Revenue focused": {"revenue": 0.50, "demand": 0.30, "satisfaction": 0.10, "competition": 0.10},
    "Risk focused": {"revenue": 0.20, "demand": 0.25, "satisfaction": 0.35, "competition": 0.20},
}

# Areas with very few listings can look great by luck, so we require a minimum
# sample and label confidence by sample size.
MIN_LISTINGS = 10


def aggregate(listings: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Summarise active, validly-priced listings by the given columns."""
    usable = listings[listings["is_active"] & listings["price_valid"]]
    grouped = usable.groupby(group_cols, observed=True).agg(
        active_listings=("id", "count"),
        median_price=("price", "median"),
        median_occupancy=("occupancy_proxy", "median"),
        median_revenue=("est_annual_revenue_capped", "median"),
        avg_rating=("review_scores_rating", "mean"),
        reviews_last_12m=("number_of_reviews_ltm", "sum"),
        share_hitting_90_night_cap=("hits_90_night_cap", "mean"),
    )
    return grouped.reset_index().round(3)


def confidence_label(n: int) -> str:
    """Simple confidence label based on how many listings sit behind a number."""
    if n >= 100:
        return "High"
    if n >= 30:
        return "Medium"
    return "Low"


def score(summary: pd.DataFrame, persona: str = "Balanced investor",
          min_listings: int = MIN_LISTINGS) -> pd.DataFrame:
    """Add percentile factors, per-factor points and a total investment score."""
    weights = PERSONA_WEIGHTS[persona]
    df = summary[summary["active_listings"] >= min_listings].copy()
    if df.empty:
        return df

    total = pd.Series(0.0, index=df.index)
    for name, spec in FACTORS.items():
        values = df[spec["column"]]
        pct = values.rank(pct=True, ascending=spec["higher_is_better"]) * 100
        pct = pct.fillna(50)  # a missing factor neither helps nor hurts
        df[f"{name}_pct"] = pct.round(1)
        df[f"{name}_points"] = (pct * weights[name]).round(1)
        total += pct * weights[name]

    df["investment_score"] = total.round(1)
    df["confidence"] = df["active_listings"].apply(confidence_label)
    return df.sort_values("investment_score", ascending=False).reset_index(drop=True)


def explain_row(row: pd.Series, persona: str = "Balanced investor") -> str:
    """One-line, rule-based explanation of a score (the AI rationale comes later)."""
    weights = PERSONA_WEIGHTS[persona]
    parts = sorted(
        ((row[f"{name}_points"], name) for name in weights), reverse=True
    )
    best = FACTORS[parts[0][1]]["label"].split(" (")[0].lower()
    second = FACTORS[parts[1][1]]["label"].split(" (")[0].lower()
    return (
        f"Score {row['investment_score']:.0f}/100, driven mostly by {best} and {second}. "
        f"Median price £{row['median_price']:.0f}/night, occupancy proxy "
        f"{row['median_occupancy']:.0%}, based on {int(row['active_listings'])} active "
        f"listings ({row['confidence']} confidence)."
    )
