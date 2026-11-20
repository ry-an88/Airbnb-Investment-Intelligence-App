"""Airbnb Investment Intelligence App: first working version (early demo).

Run locally from the project folder:
    streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from airbnb.config import CITIES, LONDON_NIGHT_CAP, PROCESSED_DIR  # noqa: E402
from airbnb.scoring import FACTORS, PERSONA_WEIGHTS, aggregate, explain_row, score  # noqa: E402

st.set_page_config(page_title="Airbnb Investment Intelligence", layout="wide")


@st.cache_data
def load_city(city: str) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    """Load processed data for a city, or None if it hasn't been built yet."""
    folder = PROCESSED_DIR / city
    if not (folder / "listings.parquet").exists():
        return None
    listings = pd.read_parquet(folder / "listings.parquet")
    quality = pd.read_csv(folder / "data_quality.csv")
    return listings, quality


def bedroom_bucket(bedrooms: pd.Series) -> pd.Series:
    """Group bedroom counts into buckets an investor would recognise."""
    return pd.cut(bedrooms.fillna(0), bins=[-1, 1, 2, 99],
                  labels=["Studio / 1 bed", "2 bed", "3+ bed"]).astype(str)


# ---------------------------------------------------------------- sidebar
st.sidebar.title("Settings")
available = [c for c in CITIES if (PROCESSED_DIR / c / "listings.parquet").exists()]
city = st.sidebar.selectbox(
    "City", options=list(CITIES), format_func=CITIES.get,
    index=list(CITIES).index("london"),
    help="Cities without processed data are listed but will show a setup message.",
)
persona = st.sidebar.radio("Investor persona", list(PERSONA_WEIGHTS),
                           help="Changes how much each factor counts in the score.")

loaded = load_city(city)
if loaded is None:
    st.title("Airbnb Investment Intelligence")
    st.warning(
        f"No processed data for {CITIES[city]} yet. Run "
        f"`python scripts/build_processed.py {city}` after downloading the raw files. "
        f"Cities ready now: {', '.join(CITIES[c] for c in available) or 'none'}."
    )
    st.stop()

listings, quality = loaded

st.sidebar.subheader("Filters")
areas = sorted(listings["neighbourhood_cleansed"].dropna().unique())
chosen_areas = st.sidebar.multiselect("Borough / neighbourhood", areas,
                                      help="Leave empty for all areas.")
room_types = sorted(listings["room_type"].dropna().unique())
chosen_rooms = st.sidebar.multiselect("Room type", room_types, default=room_types)
bands = [b for b in listings["price_band"].cat.categories] \
    if hasattr(listings["price_band"], "cat") else sorted(listings["price_band"].dropna().unique())
chosen_bands = st.sidebar.multiselect("Price band", bands, default=bands)
min_reviews = st.sidebar.slider("Minimum number of reviews", 0, 100, 5)
avail_range = st.sidebar.slider("Availability (days open in next year)", 0, 365, (0, 365))

mask = (
    listings["room_type"].isin(chosen_rooms)
    & listings["price_band"].astype(str).isin([str(b) for b in chosen_bands])
    & (listings["number_of_reviews"] >= min_reviews)
    & listings["availability_365"].between(*avail_range)
)
if chosen_areas:
    mask &= listings["neighbourhood_cleansed"].isin(chosen_areas)
filtered = listings[mask].copy()

# ---------------------------------------------------------------- header
st.title(f"Airbnb Investment Intelligence: {CITIES[city]}")
st.caption(f"Persona: **{persona}**. Early demo. Not financial or legal advice.")

if filtered.empty:
    st.info("No listings match these filters. Try widening the price band or lowering the review minimum.")
    st.stop()

active = filtered[filtered["is_active"] & filtered["price_valid"]]
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Listings (filtered)", f"{len(filtered):,}")
c2.metric("Active listings", f"{len(active):,}")
c3.metric("Median nightly price", f"£{active['price'].median():,.0f}")
c4.metric("Median occupancy proxy", f"{active['occupancy_proxy'].median():.0%}")
c5.metric("Median est. annual revenue", f"£{active['est_annual_revenue_capped'].median():,.0f}")

tab_market, tab_areas, tab_types, tab_listings, tab_risk = st.tabs(
    ["Market overview", "Top areas", "Top property types", "Listing candidates", "Risks & data quality"]
)

# ---------------------------------------------------------------- market overview
with tab_market:
    left, right = st.columns(2)
    room_mix = filtered["room_type"].value_counts().reset_index()
    left.plotly_chart(px.bar(room_mix, x="room_type", y="count", title="Room type mix"),
                      width="stretch")
    right.plotly_chart(
        px.histogram(active, x="price", nbins=60, title="Nightly price (active listings)",
                     labels={"price": "£ per night"}),
        width="stretch",
    )
    map_df = active.dropna(subset=["latitude", "longitude"]).sample(min(len(active), 5000), random_state=1)
    st.plotly_chart(
        px.scatter_map(map_df, lat="latitude", lon="longitude", color="room_type",
                       hover_name="name", hover_data={"price": True}, height=500,
                       center={"lat": map_df["latitude"].mean(), "lon": map_df["longitude"].mean()},
                       zoom=12 if chosen_areas else 9,
                       title="Where listings are (sample of up to 5,000; locations are approximate)"),
        width="stretch",
    )

# ---------------------------------------------------------------- areas
with tab_areas:
    area_scores = score(aggregate(filtered, ["neighbourhood_cleansed"]), persona)
    if area_scores.empty:
        st.info("Not enough active listings per area to score. Widen the filters.")
    else:
        st.subheader("Top 3 recommended areas")
        for _, row in area_scores.head(3).iterrows():
            st.markdown(f"**{row['neighbourhood_cleansed']}**: {explain_row(row, persona)}")

        points = area_scores.head(10).melt(
            id_vars="neighbourhood_cleansed",
            value_vars=[f"{f}_points" for f in FACTORS], var_name="factor", value_name="points",
        )
        points["factor"] = points["factor"].str.replace("_points", "")
        st.plotly_chart(
            px.bar(points, y="neighbourhood_cleansed", x="points", color="factor", orientation="h",
                   title="What makes up each area's score (top 10)").update_yaxes(autorange="reversed"),
            width="stretch",
        )
        with st.expander("How the score works"):
            st.write("Each factor is turned into a 0–100 percentile across areas, then weighted:")
            st.table(pd.DataFrame(
                [{"Factor": FACTORS[f]["label"], "Weight": w} for f, w in PERSONA_WEIGHTS[persona].items()]
            ))
            st.write("Areas with fewer than 10 active listings are left out.")
        st.dataframe(area_scores, width="stretch")

        st.subheader("Top vs bottom areas")
        compare_cols = ["median_price", "median_occupancy", "median_revenue", "avg_rating", "active_listings"]
        top_bottom = pd.DataFrame({
            "Top 5 average": area_scores.head(5)[compare_cols].mean(),
            "Bottom 5 average": area_scores.tail(5)[compare_cols].mean(),
        }).round(2)
        st.table(top_bottom)

# ---------------------------------------------------------------- property types
with tab_types:
    filtered["bedroom_group"] = bedroom_bucket(filtered["bedrooms"])
    type_scores = score(aggregate(filtered, ["room_type", "bedroom_group"]), persona)
    if type_scores.empty:
        st.info("Not enough listings per property type to score.")
    else:
        type_scores["property_type"] = type_scores["room_type"] + ", " + type_scores["bedroom_group"]
        st.subheader("Top 3 recommended property types")
        for _, row in type_scores.head(3).iterrows():
            st.markdown(f"**{row['property_type']}**: {explain_row(row, persona)}")
        st.dataframe(type_scores, width="stretch")

# ---------------------------------------------------------------- listing candidates
with tab_listings:
    st.write(
        "Examples of existing Airbnb listings with strong operating results: well reviewed, "
        "busy and high earning. These are not properties for sale."
    )
    candidates = active[(active["number_of_reviews"] >= 20) & (active["review_scores_rating"] >= 4.7)]
    candidates = candidates.sort_values("est_annual_revenue_capped", ascending=False).head(10)
    st.dataframe(
        candidates[["name", "neighbourhood_cleansed", "room_type", "bedrooms", "price",
                    "occupancy_proxy", "est_annual_revenue_capped", "review_scores_rating",
                    "number_of_reviews"]],
        width="stretch",
    )

# ---------------------------------------------------------------- risks
with tab_risk:
    if city == "london":
        st.warning(
            f"**London short-term letting rule:** without planning permission, a whole home can be "
            f"let short term for at most {LONDON_NIGHT_CAP} nights per calendar year. Revenue figures "
            f"for entire homes in this app are capped at {LONDON_NIGHT_CAP} nights."
        )
    st.markdown(
        """
**Key assumptions and limitations**
- Data is a single Inside Airbnb snapshot, not a full booking history.
- Occupancy is estimated from reviews (assumes 1 in 2 stays leaves a review and a stay of 3+ nights).
- Calendar "unavailable" nights may be bookings **or** dates the host blocked, so they are not counted as bookings.
- Listing locations are shifted by up to ~150m by Inside Airbnb for privacy.
- Prices are the advertised nightly price on the snapshot date, not what guests actually paid.
- This is an analytical tool, **not financial or legal advice**.
"""
    )
    st.subheader("Data quality")
    st.dataframe(quality, width="stretch")
