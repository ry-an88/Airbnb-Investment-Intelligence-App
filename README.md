# Airbnb Investment Intelligence App

A Streamlit app that helps a property investor decide **where**, **what** and **how** to invest in short-term rental property in UK cities, using [Inside Airbnb](https://insideairbnb.com/get-the-data/) data. London is the baseline city.

> Status: early demo (Rockborne Advance project, weeks 7–8). Not financial or legal advice.

## Features (so far)

- City selector and investor persona (balanced, revenue focused, risk focused)
- Filters: borough, room type, price band, minimum reviews, availability
- Key metrics: nightly price, occupancy proxy, estimated annual revenue, reviews
- Transparent investment score, with each factor's contribution shown
- Top 3 areas, top 3 property types and example listing candidates, each with an explanation
- Top vs bottom area comparison
- London 90-night rule applied to revenue estimates, plus a risks and data-quality tab

Planned: AI review analysis, investor memo download, short- vs long-term rental comparison, deployment.

## Project structure

```
app/streamlit_app.py      the web app
src/airbnb/config.py      paths, cities and every modelling assumption
src/airbnb/load.py        reads raw Inside Airbnb files
src/airbnb/clean.py       cleaning, outlier flags, data-quality report
src/airbnb/metrics.py     occupancy and revenue estimates
src/airbnb/scoring.py     investment score and explanations
scripts/download_data.py  downloads one city's raw files
scripts/build_processed.py builds data/processed/<city>/ from raw files
tests/                    pytest unit tests
docs/                     plan and project documentation
data/raw/                 raw downloads (ignored by Git, too big)
data/processed/           cleaned data the app reads (committed)
```

## Run it locally (Windows, PowerShell)

```powershell
# 1. Create and activate a virtual environment (once)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install the libraries
pip install -r requirements.txt

# 3. Get London data. Copy the link to London's listings.csv.gz from
#    https://insideairbnb.com/get-the-data/ and paste it in place of <link>
python scripts/download_data.py london <link>

# 4. Clean the data and build the app's tables
python scripts/build_processed.py london

# 5. Start the app (opens in your browser)
streamlit run app/streamlit_app.py

# Run the tests
pytest
```

If PowerShell refuses to run the activate script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

## Data sources

| Source | Licence / terms | Used for |
|---|---|---|
| Inside Airbnb (detailed listings, calendar, reviews, neighbourhoods) | CC BY 4.0 | Main dataset |

## Key assumptions

See `src/airbnb/config.py` and `docs/plan_to_friday.md`. In short: occupancy is estimated from reviews (Inside Airbnb's San Francisco model); calendar "unavailable" nights are not counted as bookings; London entire homes are capped at 90 nights per year; implausible prices are flagged and excluded from averages.

## Team

- Dip
