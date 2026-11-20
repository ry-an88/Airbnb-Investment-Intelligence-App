# Airbnb Investment Intelligence App

A Streamlit app that helps a property investor decide **where**, **what** and **how** to invest in short-term rental property in UK cities, using [Inside Airbnb](https://insideairbnb.com/get-the-data/) data. London is the required baseline. The app ranks boroughs and property types with a **transparent investment score**, explains every recommendation, and states the risks and assumptions behind it.

> **Status:** early demo (Rockborne Advance project, weeks 7–8 checkpoint, 20 Nov 2026).
> **Not financial or legal advice.**

![App overview](docs/screenshots/01_overview.png)

---

## Contents
- [The problem](#the-problem)
- [What the app does](#what-the-app-does)
- [First results for London](#first-results-for-london)
- [How it works](#how-it-works)
- [Key assumptions](#key-assumptions)
- [Run it locally](#run-it-locally)
- [Project structure](#project-structure)
- [Testing and CI](#testing-and-ci)
- [Data sources](#data-sources)
- [Roadmap](#roadmap)
- [Documentation](#documentation)
- [Team](#team)

---

## The problem
A property investor wants to buy a UK property to run as an Airbnb. They need to know which area to buy in, what type of property to buy, and what it might realistically earn, including the legal and data risks. They want something they can explore and question, not a static report.

**Personas.** The user picks one of three investor personas, which changes how the score weighs each factor:

| Persona | Revenue | Demand | Guest satisfaction | Low competition |
|---|---|---|---|---|
| Balanced investor | 35% | 25% | 25% | 15% |
| Revenue focused | 50% | 30% | 10% | 10% |
| Risk focused | 20% | 25% | 35% | 20% |

---

## What the app does

| Feature | Details |
|---|---|
| City selector | London (built), Bristol, Edinburgh, Greater Manchester (shown once their data is processed) |
| Persona selector | Balanced, revenue focused, risk focused |
| Filters | Borough, room type, price band, minimum reviews, availability |
| Key metrics | Listings, active listings, median nightly price, occupancy proxy, estimated annual revenue |
| Market overview | Room type mix, price distribution, map of listings |
| **Top 3 areas** | Ranked by investment score, each with an explanation and a chart of how many points each factor contributed |
| **Top 3 property types** | Room type × bedroom group, ranked and explained |
| **Listing candidates** | Real, well-reviewed, high-earning listings as examples of strong performance (not properties for sale) |
| Top vs bottom comparison | Average of the 5 best and 5 worst areas |
| Risks and data quality | London 90-night rule, assumptions, limitations, data-quality counts |

| Top areas and score breakdown | Risks and data quality |
|---|---|
| ![Top areas](docs/screenshots/02_areas.png) | ![Risks](docs/screenshots/05_risks.png) |

---

## First results for London
Inside Airbnb snapshot from **17 September 2026**: 91,954 listings, of which ~40,000 are active with a valid price. Balanced investor, listings with 5+ reviews:

| Rank | Borough | Score | Median price | Occupancy proxy | Median est. revenue |
|---|---|---|---|---|---|
| 1 | Richmond upon Thames | 73 | £150 | 16% | £10,140 |
| 2 | City of London | 69 | £235 | 20% | £15,289 |
| 3 | Lambeth | 63 | £147 | 20% | £10,170 |

- **Top 5 vs bottom 5 areas:** median price £195 vs £93, occupancy 19% vs 14%, revenue £12.8k vs £5.3k a year. Ratings are nearly identical (4.73 vs 4.71), so **price and demand drive the gap, not guest satisfaction**.
- **The persona changes the answer.** Revenue focused: City of London, Westminster, Camden. Risk focused: Richmond, Greenwich, Kingston upon Thames.
- **Top property types (balanced):** private room in a 2-bed home, entire home 3+ bed, entire home 2 bed.
- **Regulation matters:** 26% of active London entire homes are estimated above the 90-night limit, so their revenue is capped in the model.

---

## How it works

```
Inside Airbnb files ─► load ─► clean ─► estimate ─► data/processed/ ─► score ─► Streamlit app
(data/raw/, not in Git)        prices,   occupancy    listings.parquet   percentiles  filters, charts,
                               outliers, & revenue,   data_quality.csv   × persona    top 3s, risks
                               active    90-night cap                    weights
```

1. **Load** (`src/airbnb/load.py`): reads only the 34 columns needed from the detailed listings, plus the calendar.
2. **Clean** (`src/airbnb/clean.py`): converts prices from text, flags prices outside £10–£2,000 (flagged, not deleted), marks listings **active** if reviewed in the last 12 months, and builds a data-quality report.
3. **Estimate** (`src/airbnb/metrics.py`): occupancy and revenue from reviews, using Inside Airbnb's own method:
   `nights = reviews in last 12 months ÷ 0.5 × max(3, minimum nights)`, capped at 70% occupancy; `revenue = nights × price`. London entire homes are also capped at **90 nights**.
4. **Score** (`src/airbnb/scoring.py`): for each area, four factors (revenue, demand, satisfaction, low competition) become 0–100 percentiles, are multiplied by the persona's weights and added up. Areas with fewer than 10 active listings are left out, and every result gets a High/Medium/Low confidence label.
5. **App** (`app/streamlit_app.py`): filters, charts, top 3s with explanations, risks.

Every design choice and its justification is in **[docs/DESIGN_DECISIONS.md](docs/DESIGN_DECISIONS.md)**.

---

## Key assumptions
| Assumption | Value | Why |
|---|---|---|
| Share of stays that leave a review | 50% | Inside Airbnb's standard assumption |
| Average stay length | 3 nights (or minimum nights, up to 30) | Inside Airbnb's default |
| Maximum occupancy | 70% | Prevents implausible estimates |
| London entire-home limit | 90 nights/year | City Hall rule without planning permission |
| Valid nightly price | £10–£2,000 | Removes placeholders and extreme values (0.3% of listings) |
| Active listing | Reviewed in last 365 days | 49% of listings are dormant |
| Calendar "unavailable" | **Not** counted as booked | Could be booked or blocked by the host |

All values live in [`src/airbnb/config.py`](src/airbnb/config.py), so they're easy to find and change.

**Limitations:** single snapshot (no seasonality); 35% of listings have no price; locations are shifted by up to 150 m; advertised price may differ from price paid; operating costs and purchase prices aren't modelled yet.

---

## Run it locally

Requires Python 3.11+.

```powershell
# 1. Create and activate a virtual environment (once)
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate         # macOS / Linux

# 2. Install the libraries
pip install -r requirements.txt

# 3. Start the app (processed London data is already in the repo)
streamlit run app/streamlit_app.py
```

**Rebuilding the data from scratch (optional):**
```powershell
# Copy the London listings.csv.gz link from https://insideairbnb.com/get-the-data/
python scripts/download_data.py london <link>
python scripts/build_processed.py london
```
Or download `listings.csv.gz`, `calendar.csv.gz`, `reviews.csv.gz` and `neighbourhoods.geojson` by hand into `data/raw/london/`.

If PowerShell refuses to activate the environment, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

---

## Project structure
```
app/streamlit_app.py        the web app (user interface only)
src/airbnb/config.py        paths, cities and every modelling assumption
src/airbnb/load.py          reads raw Inside Airbnb files, with clear errors if missing
src/airbnb/clean.py         cleaning, outlier flags, active flag, data-quality report
src/airbnb/metrics.py       occupancy and revenue estimates, 90-night cap
src/airbnb/scoring.py       investment score, personas, explanations
scripts/download_data.py    downloads one city's raw files
scripts/build_processed.py  builds data/processed/<city>/ from raw files
tests/                      pytest unit tests
docs/                       design decisions, plan, screenshots
slides/                     presentation slides
data/raw/                   raw downloads (ignored by Git: too large)
data/processed/             cleaned data the app reads (committed)
```

---

## Testing and CI
```powershell
pytest          # 18 unit tests
ruff check .    # code style
```
Tests use a small hand-made dataset where the right answers can be worked out by hand. They cover price parsing, outlier flags, the active flag, the occupancy formula and caps, the London 90-night cap, missing-price handling, persona weights summing to 1, score points adding up, and empty results.
GitHub Actions (`.github/workflows/ci.yml`) runs both checks on every push.

---

## Data sources
| Source | Licence | Used for |
|---|---|---|
| [Inside Airbnb](https://insideairbnb.com/get-the-data/): London, 17 Sep 2026 (detailed listings, calendar, reviews, neighbourhoods) | CC BY 4.0 | Main dataset |
| *Planned:* UK House Price Index / HM Land Registry Price Paid Data | Open Government Licence | Purchase prices, yield |
| *Planned:* ONS Price Index of Private Rents | Open Government Licence | Long-term rent comparison |

---

## Roadmap
- [x] Project scope, personas, data plan
- [x] Cleaning pipeline, occupancy and revenue model, investment score
- [x] Streamlit app with filters, top 3s, explanations, risks
- [x] Tests and CI
- [ ] AI review analysis with OpenAI: themes, guest needs, risk flags (JSON, cached, cost-logged)
- [ ] AI rationales per recommendation and persona; investor memo download
- [ ] Short- vs long-term rental comparison (Land Registry, ONS)
- [ ] Borough map from GeoJSON; more cities
- [ ] Deploy to Streamlit Community Cloud
- [ ] Final docs, slides, demo video

---

## Documentation
- [docs/DESIGN_DECISIONS.md](docs/DESIGN_DECISIONS.md): every choice, its alternatives and justification, the full assumptions list, limitations, data dictionary and decision log
- [docs/plan_to_friday.md](docs/plan_to_friday.md): project plan for the 20 Nov checkpoint
- [slides/airbnb_checkpoint_20nov.pptx](slides/airbnb_checkpoint_20nov.pptx): checkpoint presentation

---

## Team
- Dip
