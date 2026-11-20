# Design decisions, assumptions and justifications

This document explains **every significant choice** in the project so far: what was decided, the alternatives considered, and why. It is written so that a reviewer, an interviewer or a new teammate can understand the reasoning without reading the code.

Status: weeks 7–8 checkpoint (20 Nov 2026). Sections marked *(planned)* describe decisions for work not yet built.

---

## Contents

1. [Product decisions](#1-product-decisions)
2. [Data source decisions](#2-data-source-decisions)
3. [Data cleaning decisions](#3-data-cleaning-decisions)
4. [Occupancy and revenue model](#4-occupancy-and-revenue-model)
5. [Investment score](#5-investment-score)
6. [Recommendations: areas, property types, listings](#6-recommendations-areas-property-types-listings)
7. [App design decisions](#7-app-design-decisions)
8. [Engineering decisions](#8-engineering-decisions)
9. [AI design (planned)](#9-ai-design-planned)
10. [Full list of assumptions](#10-full-list-of-assumptions)
11. [Known limitations and risks](#11-known-limitations-and-risks)
12. [Data dictionary (processed listings)](#12-data-dictionary-processed-listings)
13. [Decision log](#13-decision-log)

---

## 1. Product decisions

### 1.1 Who the app is for
**Decision:** A single user type, the *property investor*, viewed through three **personas**: Balanced investor, Revenue focused, Risk focused.

**Why:** The brief asks the app to "make clear which persona it is serving or allow the user to select a persona". Investors differ mainly in how they trade off income against risk, so the personas differ only in how they weight the score factors (section 5.4). This keeps the logic simple: one model, three framings, and switching persona visibly changes the recommendation, which is easy to demonstrate.

**Alternatives considered:** Separate personas such as "holiday-let operator" or "first-time buyer" with different screens. Rejected for now because they would need different data (mortgage costs, management fees) that we don't have yet.

### 1.2 What the app answers
The investor's three questions from the brief map to three outputs:

| Question | Output in the app |
|---|---|
| **Where** to invest? | Top 3 boroughs, with score breakdown and explanation |
| **What** to buy? | Top 3 property types (room type × bedroom count) |
| **How** do good operators perform? | Listing candidates: real Airbnb listings with strong results |

### 1.3 London first, other cities pluggable
**Decision:** Build and test everything on London, but keep the city as a parameter throughout (`config.CITIES`, `data/raw/<city>/`, `data/processed/<city>/`).

**Why:** London is required by the brief and is the largest UK dataset (≈92k listings), so if it works for London it will work for smaller cities. The app's city selector already lists Bristol, Edinburgh and Greater Manchester; they show a setup message until their data is processed.

---

## 2. Data source decisions

### 2.1 Inside Airbnb, 17 September 2026 London snapshot
**Decision:** Use the most recent quarterly snapshot at the time of building.

**Why:** It is the brief's required source, it's free, and it's licensed CC BY 4.0. The most recent snapshot gives the most current prices and the "last 12 months" review counts that our occupancy model depends on.

### 2.2 Which files
| File | Used? | Why |
|---|---|---|
| `listings.csv.gz` (detailed) | **Yes, core** | Has everything per listing: price, room type, bedrooms, review counts and scores, minimum nights, location. |
| `calendar.csv.gz` | **Yes, secondary** | Used only as a supporting demand signal (section 4.4), never as bookings. |
| `reviews.csv.gz` | Downloaded, *planned* for AI | Contains the free-text comments needed for AI review analysis. |
| `neighbourhoods.geojson` | Downloaded, *planned* | Borough boundaries for a choropleth map. |
| `listings.csv` (summary), `reviews.csv` (summary), `neighbourhoods.csv` | **No** | Everything in them is already in the detailed files. Using one file per concept avoids two sources disagreeing. |

### 2.3 Raw data is never edited and not committed to Git
**Decision:** Raw files live in `data/raw/` (ignored by Git). Cleaned outputs live in `data/processed/` and **are** committed.

**Why:**
- Raw files are large (reviews alone is 287 MB), and GitHub rejects files over 100 MB.
- Keeping raw data untouched means the whole pipeline can be re-run from scratch, which makes it reproducible.
- The processed Parquet file is only ~7 MB, and the deployed app needs data to read, since Streamlit Cloud can't download Inside Airbnb data at start-up reliably.

### 2.4 Parquet for processed data
**Decision:** Save cleaned listings as Parquet, not CSV.

**Why:** Parquet keeps data types (dates stay dates, booleans stay booleans), is compressed, and loads much faster than CSV. That makes the app start quicker.

### 2.5 Extra public data *(planned)*
For the short- vs long-term comparison: **UK House Price Index** / **HM Land Registry Price Paid Data** for purchase prices, and **ONS Price Index of Private Rents** for long-term rents. These are official, free sources, as the brief recommends.

---

## 3. Data cleaning decisions

All cleaning lives in `src/airbnb/clean.py`.

### 3.1 Load only the columns we need
**Decision:** Read 34 of the 90 listing columns (`load.LISTING_COLUMNS`).

**Why:** It's faster, uses less memory, and makes it obvious which fields the analysis depends on. Columns missing from older snapshots are skipped instead of crashing, so the code works across snapshots.

### 3.2 Price parsing
Prices arrive as text like `"$1,250.00"`. We strip everything except digits and the decimal point, then convert to a number. Unreadable values become missing (NaN).

**Currency note:** Inside Airbnb always writes `$`, but UK listings are priced in **pounds**. We treat the number as GBP.

### 3.3 Flag outliers, don't delete rows
**Decision:** Prices outside **£10–£2,000 per night** get `price_valid = False`. They stay in the data but are excluded from averages, revenue and scoring.

**Why:**
- Deleting rows would change listing counts and hide data-quality problems. Flagging keeps counts honest and lets us report the issue.
- £10 is below any realistic London nightly price (it's usually a placeholder). £2,000 removes luxury and error values (some listings show £10,000+), which would distort means. In the London data this flags only **270 listings (0.3%)**, so the threshold barely affects results but protects against extreme values.
- We use **medians** for area summaries anyway, which are robust to outliers.

### 3.4 Missing prices
**Finding:** 32,049 listings (**35%**) have no price. Most of them are inactive (Inside Airbnb leaves price blank when a listing can't be booked).

**Decision:** Leave missing prices missing. Their revenue is missing, never zero, because guessing a price would invent data.

### 3.5 "Active" listings
**Decision:** A listing is **active** if it received a review in the **last 365 days** before the snapshot date.

**Why:** 49% of London listings had no review in the last year. Many are dormant or abandoned. Including them would drag down occupancy and revenue and make areas full of dead listings look worse than they are. Scoring uses **active, validly priced listings only** (≈40k in London).

**Trade-off:** A brand-new listing with no reviews yet is excluded. That's acceptable, because without reviews we can't estimate its demand anyway.

### 3.6 Other cleaning
| Field | Treatment | Why |
|---|---|---|
| `bathrooms` | Fill from `bathrooms_text` ("1.5 shared baths" → 1.5, "Half-bath" → 0.5) | Recent snapshots often leave the numeric column empty. |
| `host_is_superhost`, `instant_bookable` | `"t"/"f"` → True/False, missing stays missing | Correct data types for filtering. |
| `reviews_per_month` | Missing → 0 | Missing means "no reviews", so 0 is the true value. |
| `last_review`, `last_scraped` | Parsed to dates | Needed for the active flag. |
| `price_band` | Under £75 / £75–150 / £150–250 / £250–500 / £500+ | A friendlier filter than a raw slider. Bands match how people think about nightly prices. |

### 3.7 Data-quality report
`data_quality_report()` counts every issue above and is shown in the app's *Risks & data quality* tab. London results:

| Check | Count | Share |
|---|---|---|
| Listings in snapshot | 91,954 | 100% |
| Missing or unreadable price | 32,049 | 34.9% |
| Price outside £10–£2,000 | 270 | 0.3% |
| No reviews ever | 20,694 | 22.5% |
| Missing overall review score | 20,694 | 22.5% |
| Missing bedrooms | 45 | 0.0% |
| Not active (no review in 12 months) | 44,905 | 48.8% |

---

## 4. Occupancy and revenue model

Code: `src/airbnb/metrics.py`. Assumption values: `src/airbnb/config.py`.

### 4.1 The problem
Inside Airbnb does **not** publish bookings. We have to estimate how many nights each listing is booked.

### 4.2 Decision: a review-based model (the "San Francisco model")
```
stays per year   = reviews in last 12 months ÷ REVIEW_RATE (0.5)
nights per year  = stays × stay length
stay length      = minimum_nights, but at least 3 (AVG_LENGTH_OF_STAY) and at most 30
nights per year  capped at 70% of 365 (MAX_OCCUPANCY) = 255.5 nights
occupancy proxy  = nights ÷ 365
annual revenue   = nights × nightly price
```

**Why this model:**
- It's the method **Inside Airbnb itself** uses, so it's established and citable.
- Reviews only happen after a real stay, so they are evidence of actual bookings, unlike calendar availability.
- Each step is simple arithmetic that a non-technical stakeholder can follow.

**Why each parameter:**
| Parameter | Value | Justification |
|---|---|---|
| `REVIEW_RATE` | 0.5 | Inside Airbnb's assumption that roughly half of guests leave a review. Lower would raise all estimates; we chose the established, middle value. |
| `AVG_LENGTH_OF_STAY` | 3 nights | Inside Airbnb's default for cities without published stay data. |
| Stay length = max(3, minimum nights) | | If a host requires a 5-night minimum, every stay is at least 5 nights. |
| Stay length cap | 30 nights | Minimum stays above 30 are effectively medium/long lets. Without a cap, one review on a 365-night-minimum listing would imply a full year booked. |
| `MAX_OCCUPANCY` | 70% | Inside Airbnb's cap. It stops a few listings with unusual review patterns from showing impossible occupancy. |
| Reviews in last 12 months (`number_of_reviews_ltm`) | | Measures recent demand rather than lifetime average. Falls back to `reviews_per_month × 12` if the column is missing. |

### 4.3 London 90-night rule
**Decision:** For **entire homes in London**, we also calculate `est_annual_revenue_capped`, which limits nights to **90 per year**. All area and property-type scoring uses the **capped** figure. Private rooms are not capped.

**Why:** London City Hall guidance says that, without planning permission, Londoners can let their whole home short term for at most 90 nights a calendar year. The brief requires a risk note on this. Using the capped revenue means the app never recommends an area based on income that would be unlawful without permission. The flag `hits_90_night_cap` shows which listings exceed it: **26% of active London entire homes** do.

**Why private rooms aren't capped:** The rule applies to letting a *whole* home. Letting a room while the host lives there is treated differently.

### 4.4 Why we do NOT use the calendar as bookings
Inside Airbnb states that an "unavailable" night may be **booked or blocked by the host**. In London the median listing is **64% unavailable** over the next 90 days, far higher than plausible occupancy. Counting those nights as bookings would overstate revenue roughly 3–4×.

**Decision:** The calendar gives only `unavailable_share_90d`, stored as an **upper bound** on demand for context. It is not used in the score.

### 4.5 Sanity check
Our London medians (active listings): **~13–18% occupancy, ~£7.7k–10.4k revenue a year** (depending on filters). Inside Airbnb's own estimate column gives a median of 64 nights (~17.5%) and ~£11.3k. Ours is slightly lower because of the 90-night cap and the 70% ceiling, so it's **deliberately conservative**, which is the safer error for an investment tool.

---

## 5. Investment score

Code: `src/airbnb/scoring.py`.

### 5.1 Goal
The brief requires a "transparent scoring model" where "users should be able to understand what factors contribute to it". So we chose a **weighted sum of percentiles**, not a machine-learning model.

**Why not machine learning?** There is no "right answer" to train on: we don't know which areas are actually good investments. A model would also be harder to explain. A weighted sum lets us show exactly where every point comes from.

### 5.2 Factors
| Factor | Measure | Better when | Why it matters |
|---|---|---|---|
| Revenue potential | Median estimated annual revenue (90-night capped) | Higher | The main thing an investor cares about. |
| Demand | Median occupancy proxy | Higher | High occupancy means reliable bookings and less dependence on high prices. |
| Guest satisfaction | Mean review score (out of 5) | Higher | Areas where guests are happy support good reviews and repeat demand. |
| Low competition | Number of active listings | Fewer | More listings means more competing supply for guests. |

**Why medians:** Revenue and price are heavily skewed by luxury listings. A median shows the typical listing.
**Why mean for rating:** Ratings are bounded (1–5) and tightly clustered, so the mean is stable and distinguishes small differences better.

### 5.3 Normalising: percentiles
Each factor is converted to a **0–100 percentile rank across areas** (100 = best area on that factor).

**Why percentiles, not min-max scaling:** Percentiles aren't distorted by one extreme area (e.g. Westminster's listing count is far above all others). They are also easy to explain: "Richmond is in the top 10% of boroughs for guest satisfaction."

A missing factor gets 50 (neutral), so it neither helps nor hurts.

### 5.4 Persona weights
| Persona | Revenue | Demand | Satisfaction | Low competition |
|---|---|---|---|---|
| Balanced investor | 0.35 | 0.25 | 0.25 | 0.15 |
| Revenue focused | 0.50 | 0.30 | 0.10 | 0.10 |
| Risk focused | 0.20 | 0.25 | 0.35 | 0.20 |

**Why these weights:**
- Weights always add up to 1, so the score is always 0–100 (checked by a unit test).
- **Balanced:** revenue counts most, as it's an investment, but no single factor dominates.
- **Revenue focused:** 80% on revenue and demand; satisfaction and competition are secondary.
- **Risk focused:** the largest weight is satisfaction. Happy guests mean steady demand and fewer operational problems. Competition is weighted higher because crowded markets are more exposed to price wars and regulation.

These weights are a **judgement call**, which we state openly. The persona switch exists precisely so users can see how sensitive the ranking is to them.

### 5.5 Minimum sample size and confidence
- Areas with **fewer than 10 active listings are excluded**: a tiny area can top the table by luck.
- Each result gets a **confidence label**: High (100+ listings), Medium (30–99), Low (10–29).

### 5.6 Explanations
`explain_row()` produces a one-line, **rule-based** explanation naming the two factors that contributed most points, plus the median price, occupancy and sample size. This is deterministic, so it can't "hallucinate". AI-written rationales *(planned)* will be added alongside, not instead.

---

## 6. Recommendations: areas, property types, listings

### 6.1 Areas
Group by `neighbourhood_cleansed`, which for London is the **33 boroughs** (32 + City of London). Boroughs are the unit used by planning rules and official statistics, so they will join cleanly to house price and rent data later.

### 6.2 Property types
**Decision:** Define property type as **room type × bedroom group** (Studio/1 bed, 2 bed, 3+ bed).

**Why:** Room type (entire home, private room, shared, hotel) is the biggest driver of price and regulation. Bedrooms are what an investor actually buys. Inside Airbnb's `property_type` field has 89 different values in London ("Entire rental unit", "Entire condo"…), too fragmented to rank.

**Caveat:** "Private room, 2 bed" ranks #1 for the balanced persona but is a small group (268 listings). We call this out.

### 6.3 Listing candidates
**Rule:** active, valid price, **20+ reviews**, rating **4.7+**, sorted by capped estimated revenue, top 10.

**Why:** 20+ reviews means a proven track record, not luck. 4.7+ keeps about two-thirds of active London listings (the median rating is 4.82): it removes the weaker third rather than picking a tiny elite. These are presented as examples of strong operating performance, **not properties for sale**, as the brief specifies.

**Known issue:** With no filter, the top candidates are luxury £1,500+/night homes. Users can narrow with the price band filter; a future version may rank by a balanced listing score instead.

### 6.4 Top vs bottom comparison
The app compares the average of the top 5 and bottom 5 scored areas. London (balanced persona, 5+ reviews): median price **£195 vs £93**, occupancy **19% vs 14%**, revenue **£12.8k vs £5.3k**, rating **4.73 vs 4.71**. The insight: **price and demand drive the gap, not guest satisfaction.**

---

## 7. App design decisions

### 7.1 Streamlit
**Why:** It's recommended by the brief, it's pure Python (no separate front end to build), it has built-in widgets for every filter we need, and it deploys free to Streamlit Community Cloud.

### 7.2 Layout
- **Sidebar = inputs** (city, persona, filters). **Main area = outputs.** This is the standard dashboard pattern, so users know where to look.
- **Headline metrics** at the top give the big picture before details.
- **Tabs** follow the investor's journey: overview → where → what → examples → risks.

### 7.3 Filters
The brief requires borough, room type, price band, review count and availability. Defaults: all areas, all room types, all bands, **5+ reviews**, any availability. The 5-review default removes listings with too little evidence while keeping most of the market.

### 7.4 Charts
- **Plotly**, because it's interactive (hover to see values) and works well in Streamlit.
- **Stacked bar of score points** shows the score breakdown visually, so transparency is visual as well as numeric.
- **Map** samples up to 5,000 points so the page stays fast. We note that locations are approximate.

### 7.5 Error handling in the app
- No processed data for a city → friendly message with the exact command to fix it.
- Filters return nothing → message suggesting how to widen them.
- Not enough listings to score → message instead of an empty table.
- `@st.cache_data` caches loaded data so changing filters doesn't re-read files.

### 7.6 Disclaimers
"Not financial or legal advice" appears under the title and in the risks tab, as the brief requires.

---

## 8. Engineering decisions

### 8.1 Project structure
```
src/airbnb/   reusable logic (no Streamlit code)   → testable, reusable in notebooks
scripts/      command-line steps (download, build) → pipeline runs separately from the app
app/          the Streamlit user interface only
tests/        unit tests
docs/         documentation
```
**Why separate logic from the app:** Functions in `src/` can be unit tested without starting a web server, and the app file stays readable.

### 8.2 One config file for assumptions
Every number that's an assumption (review rate, caps, price limits, active window) is in `config.py`. That way one change updates the app, the pipeline and the docs, and the assumptions are easy to find and defend.

### 8.3 Pipeline runs offline, app reads results
Cleaning 92k listings and 33.5M calendar rows takes ~35 seconds. Doing it once in `build_processed.py` means the app loads in about a second.

### 8.4 Testing
18 `pytest` tests on a tiny hand-made dataset, covering price and bathroom parsing, outlier flagging, the active flag, the occupancy formula, the 70% cap, the 90-night cap, missing-price handling, the calendar share, that persona weights sum to 1, that points sum to the score, the small-area exclusion and empty results.

**Why hand-made data:** The expected answer can be worked out by hand, so the tests prove the logic is right, not just that it runs.

### 8.5 CI
GitHub Actions runs **ruff** (lint) and **pytest** on every push, so broken code is caught immediately.

### 8.6 Secrets
API keys go in `.env` (ignored by Git) or Streamlit secrets. `.env.example` shows the variable name without a value.

---

## 9. AI design *(planned)*

**Provider:** OpenAI (chosen 16 Nov 2026, the brief's default).

**Two-step approach** (the brief's "multi-step reasoning"):
1. **Extract:** for a sample of ~20 recent reviews per listing or area, return **JSON**: summary, positive themes, negative themes, guest needs (cleanliness, location, communication, check-in, comfort, value, amenities, noise), risk flags and a confidence label.
2. **Recommend:** combine stored themes with score data to write a plain-English, persona-aware rationale for each top recommendation.

**Cost control (budget £1–5):** a small, cheap model, testing on a handful of listings first, sampling reviews rather than sending all of them, caching outputs in a table so nothing is processed twice, a cost log, and versioned prompts.

**Safety:** JSON validated against a schema; retries and fallbacks on bad responses; AI rationale shown next to the underlying numbers so claims can be checked; multilingual reviews handled by asking for English output.

---

## 10. Full list of assumptions

| # | Assumption | Where | Effect if wrong |
|---|---|---|---|
| A1 | 50% of stays leave a review | `REVIEW_RATE` | If fewer review, real occupancy is higher than estimated |
| A2 | Average stay is 3 nights (or the minimum, if higher, up to 30) | `AVG_LENGTH_OF_STAY` | Longer stays → higher occupancy |
| A3 | Occupancy can't exceed 70% | `MAX_OCCUPANCY` | Underestimates the very busiest listings |
| A4 | London entire homes limited to 90 nights | `LONDON_NIGHT_CAP` | Hosts with planning permission could earn more |
| A5 | Advertised price ≈ price paid | `price` | Discounts and seasonal pricing make real revenue differ |
| A6 | Prices are in GBP despite the `$` sign | `parse_price` | n/a (confirmed by Inside Airbnb) |
| A7 | Prices outside £10–£2,000 are unreliable | `MIN/MAX_VALID_PRICE` | A few genuine luxury listings are excluded from averages |
| A8 | "Active" = reviewed in the last 365 days | `ACTIVE_REVIEW_WINDOW_DAYS` | New listings without reviews are excluded |
| A9 | Calendar unavailable ≠ booked | `metrics.py` | n/a: this is a stated limitation of the data |
| A10 | Persona weights reflect those investor types | `PERSONA_WEIGHTS` | Different weights would change rankings (the persona switch shows how much) |
| A11 | Fewer active listings = less competition | `FACTORS` | Busy areas may also have more guest demand |
| A12 | 10 listings is the minimum to score an area | `MIN_LISTINGS` | Small areas excluded |
| A13 | One snapshot represents the market | data | Seasonality isn't captured |

---

## 11. Known limitations and risks

**Data:** snapshot only; 35% missing prices; locations shifted by up to 150 m; review-based occupancy is an estimate; no seasonality.

**Regulatory:** London 90-night rule (handled in revenue); other councils may add rules; this tool isn't legal advice.

**Market:** advertised vs actual price; competition may grow; demand can shift (events, tourism trends).

**Operational:** no costs yet (cleaning, management ~15–20%, Airbnb fees, utilities, furnishing, voids).

**Financial:** no purchase price or yield yet *(planned with Land Registry/ONS data)*; not financial advice.

---

## 12. Data dictionary (processed listings)

File: `data/processed/<city>/listings.parquet`. One row per listing.

| Column | Type | Source | Meaning |
|---|---|---|---|
| `id` | int | Inside Airbnb | Listing ID |
| `name` | text | Inside Airbnb | Listing title |
| `host_id` | int | Inside Airbnb | Host ID |
| `host_is_superhost` | bool | cleaned | Superhost status |
| `host_listings_count` | int | Inside Airbnb | Listings the host has |
| `neighbourhood_cleansed` | text | Inside Airbnb | Borough (London) / neighbourhood |
| `latitude`, `longitude` | float | Inside Airbnb | Approximate location (shifted for privacy) |
| `property_type` | text | Inside Airbnb | Host-chosen type, e.g. "Entire rental unit" |
| `room_type` | text | Inside Airbnb | Entire home/apt, Private room, Shared room, Hotel room |
| `accommodates` | int | Inside Airbnb | Max guests |
| `bathrooms` | float | cleaned | Number of bathrooms (filled from text) |
| `bathrooms_text` | text | Inside Airbnb | Original text, e.g. "1.5 shared baths" |
| `bedrooms`, `beds` | float | Inside Airbnb | Counts |
| `price` | float | cleaned | Nightly price, £ |
| `price_valid` | bool | derived | Price within £10–£2,000 |
| `price_band` | category | derived | Under £75 … £500+ |
| `minimum_nights` | int | Inside Airbnb | Minimum stay |
| `availability_30`, `availability_365` | int | Inside Airbnb | Days available in next 30/365 |
| `number_of_reviews` | int | Inside Airbnb | Lifetime reviews |
| `number_of_reviews_ltm` | int | Inside Airbnb | Reviews in last 12 months |
| `reviews_per_month` | float | cleaned | Missing → 0 |
| `last_review`, `last_scraped` | date | cleaned | Dates |
| `review_scores_*` | float | Inside Airbnb | Scores out of 5 (rating, cleanliness, location, value, communication, check-in) |
| `license`, `instant_bookable` | text / bool | Inside Airbnb | Licence text, instant booking |
| `estimated_occupancy_l365d`, `estimated_revenue_l365d` | float | Inside Airbnb | Inside Airbnb's own estimates (kept for comparison only) |
| `city` | text | derived | City key, e.g. "london" |
| `is_active` | bool | derived | Reviewed in the last 365 days |
| `est_nights_booked` | float | derived | Estimated nights booked per year (section 4.2) |
| `occupancy_proxy` | float | derived | Nights ÷ 365 |
| `est_annual_revenue` | float | derived | Nights × price (uncapped) |
| `est_annual_revenue_capped` | float | derived | As above, with the London 90-night cap on entire homes |
| `hits_90_night_cap` | bool | derived | London entire home estimated above 90 nights |
| `unavailable_share_90d` | float | derived | Share of next 90 days unavailable (upper bound on demand) |

---

## 13. Decision log

| Date | Decision | Reason |
|---|---|---|
| 16 Nov 2026 | Weeks 5–6 and 7–8 checkpoints combined into one on 20 Nov | Weeks 5–6 session cancelled |
| 16 Nov 2026 | Streamlit + pandas + Plotly; Python package in `src/` | Brief's recommended stack; testable structure |
| 16 Nov 2026 | Review-based occupancy model; calendar not used as bookings | Established method; brief's warning about calendar data |
| 16 Nov 2026 | Weighted-percentile score with 3 personas | Brief requires transparency and persona framing |
| 16 Nov 2026 | OpenAI as AI provider | Dip's choice; the brief's default |
| 20 Nov 2026 | London snapshot 17 Sep 2026 processed; processed data committed | Needed for demo and deployment |
