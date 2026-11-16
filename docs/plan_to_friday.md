# Plan to Friday 20 Nov 2026 (10:00 presentation)

The weeks 5–6 presentation was cancelled, so Friday covers **both** milestones:

| Milestone | What the schedule asks for | What we'll show |
|---|---|---|
| Weeks 5–6: Start | Project scope, roles, data plan, GitHub setup, early design | Scope and personas (below), roles, data plan, GitHub repo link, app sketch |
| Weeks 7–8: Core workflow | Data processing, review analytics, backend progress, early interface | London pipeline running, investment score, first Streamlit app with real data, first AI review summaries (stretch) |

The full app (AI memo, deployment polish, docs, video) comes **after** Friday.

---

## Day-by-day

**Monday 16 (today)**
- [x] Project structure, cleaning code, occupancy and revenue model, investment score, first Streamlit app, tests, CI (done with Claude)
- [ ] Create Python environment and install requirements (see README)
- [ ] Download London data from Inside Airbnb

**Tuesday 17**
- [ ] Run the pipeline on real London data, look at the data-quality report and fix any surprises
- [ ] Explore in a notebook: price distribution, room type mix, top boroughs. Sanity-check the estimates (are the revenue numbers believable?)
- [ ] Create the GitHub repo and push (meaningful commits, CI goes green)

**Wednesday 18**
- [ ] AI review analysis on a small sample (e.g. 20 reviews for each of 10 listings): summary, positive/negative themes, guest needs, saved as a table. Keep a cost log.
- [ ] Deploy a first version to Streamlit Community Cloud (stretch, but very impressive on Friday)
- [ ] Start the slides (outline below)

**Thursday 19**
- [ ] Finish slides, rehearse, take screenshots as a backup in case the live demo fails
- [ ] Buffer for anything that slipped

**Friday 20, 10:00: present**

---

## Project scope

**Problem.** A property investor wants to buy a UK property to run as an Airbnb. They need to know *where* to buy, *what type* of property, and *how much it might earn*, with honest risks. They want a tool they can explore, not a static report.

**In scope:** Inside Airbnb data for London (required) and other UK cities; area and property-type comparison; occupancy and revenue estimates; a transparent investment score; AI review analysis; short- vs long-term rental comparison; risk notes; a deployed Streamlit app.

**Out of scope:** real purchase listings, mortgage modelling, legal advice, live booking data.

## Personas

| Persona | Goal | What they care about | Score weights (revenue / demand / satisfaction / low competition) |
|---|---|---|---|
| **Balanced investor** | Good returns without big surprises | All-round performance | 35 / 25 / 25 / 15 |
| **Revenue-focused investor** | Maximise income | High nightly price and occupancy | 50 / 30 / 10 / 10 |
| **Risk-focused investor** (e.g. first-time buyer) | Avoid losses and regulation trouble | Guest satisfaction, steady demand, the London 90-night cap | 20 / 25 / 35 / 20 |

The persona selector already works in the app and changes the ranking.

## Roles

Currently Dip is working solo (teammate not responsive). Suggested split if the teammate returns:
- **Dip:** data pipeline, scoring model, app.
- **Teammate:** AI review analysis, documentation, slides.

*Note for the presentation:* mention the team situation briefly and honestly. It also explains scope choices.

## Data plan

| Source | Used for | Status |
|---|---|---|
| Inside Airbnb `listings.csv.gz` (detailed) | Prices, room types, bedrooms, reviews, location | Pipeline ready, need to download |
| Inside Airbnb `calendar.csv.gz` | Secondary demand signal (share of next 90 days unavailable) | Pipeline ready (optional) |
| Inside Airbnb `reviews.csv.gz` | AI review analysis | Next step |
| Inside Airbnb `neighbourhoods.geojson` | Borough map | Later |
| UK House Price Index / Land Registry | Purchase price → yield, short- vs long-term comparison | After Friday |
| ONS private rental prices | Long-term rent comparison | After Friday |

**Key assumptions** (all in `src/airbnb/config.py`):
- Occupancy is estimated from reviews: reviews in the last 12 months ÷ 0.5 review rate × average stay of 3 nights (or minimum nights, if longer), capped at 70% occupancy. This is the method Inside Airbnb uses.
- Calendar "unavailable" nights are **not** treated as bookings (they might be blocked by the host).
- London entire homes are capped at 90 nights a year (the City Hall rule without planning permission).
- Prices under £10 or over £2,000 a night are flagged as unreliable and excluded from averages.
- "Active" listing = reviewed in the last 12 months.

## Pipeline (what happens to the data)

```
Inside Airbnb files ──► load.py ──► clean.py ──► metrics.py ──► data/processed/ ──► scoring.py ──► Streamlit app
 (data/raw/, not in Git)  read only   prices,      occupancy &     listings.parquet    percentiles,     filters, charts,
                          needed      outliers,    revenue         data_quality.csv    weights,         top 3s, risks
                          columns     active flag  estimates                           explanations
```

## App sketch (current tabs)

1. **Sidebar:** city, persona, filters (borough, room type, price band, minimum reviews, availability).
2. **Headline metrics:** listings, active listings, median price, occupancy proxy, estimated revenue.
3. **Market overview:** room type mix, price distribution, map.
4. **Top areas:** top 3 with explanations, score breakdown chart, top vs bottom comparison.
5. **Top property types:** room type × bedrooms, top 3 with explanations.
6. **Listing candidates:** well-reviewed, high-earning example listings.
7. **Risks & data quality:** London 90-night rule, assumptions, data-quality table.

Coming next: AI review tab, investor memo download, short- vs long-term comparison.

## Slide outline (about 10 minutes)

1. Title and team (1 slide)
2. The investor's problem and our personas (1)
3. Data: what Inside Airbnb gives us, and its limits (1)
4. Pipeline and architecture diagram (1)
5. How we estimate occupancy and revenue, and why we don't trust the calendar (1)
6. The investment score: factors, weights, persona switch (1)
7. **Live demo** of the app (2–3 minutes)
8. First insights for London (1)
9. AI plan: review themes → recommendations, budget and cost control (1)
10. Risks, next steps and timeline (1)
