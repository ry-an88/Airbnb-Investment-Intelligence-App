# Datasets: Inside Airbnb, London (snapshot 17 September 2026)

Source: [Inside Airbnb](https://insideairbnb.com/get-the-data/), licensed **CC BY 4.0**. Files are saved in `data/datasets/` (or `data/raw/london/` for the pipeline) and are **not committed to Git** because they're too large.

## Overview

| File | Compressed size | Rows | Columns | One row is… | Used for |
|---|---|---|---|---|---|
| `listings.csv.gz` | 48 MB | 91,954 | 90 | one listing | Core analysis: price, room type, reviews, location |
| `calendar.csv.gz` | 82 MB | 33,563,890 | 5 | one listing on one day (next 365 days) | Secondary demand signal |
| `reviews.csv.gz` | 287 MB | 2,323,969 | 6 | one guest review (Dec 2009 to Sep 2026, 71,260 listings) | AI review analysis (planned) |
| `neighbourhoods.geojson` | 1 MB | 33 features | – | one borough boundary | Borough map (planned) |

**What `.csv.gz` means:** a normal CSV compressed with gzip. pandas reads it directly: `pd.read_csv("data/datasets/listings.csv.gz", low_memory=False)`.

**Privacy note:** host names, reviewer names and profile links are personal data. They are hidden in the samples below and not used anywhere in the app.

---

## 1. `listings.csv.gz` (detailed listings)

### First 15 rows (13 key columns of 90)
|      id | neighbourhood_cleansed   | room_type       | property_type               |   accommodates |   bedrooms | price   |   minimum_nights |   availability_365 |   number_of_reviews |   number_of_reviews_ltm |   review_scores_rating | last_review   |
|--------:|:-------------------------|:----------------|:----------------------------|---------------:|-----------:|:--------|-----------------:|-------------------:|--------------------:|------------------------:|-----------------------:|:--------------|
|   11551 | Lambeth                  | Entire home/apt | Entire rental unit          |              5 |          1 | $267.50 |                1 |                349 |                 197 |                       7 |                   4.55 | 2026-09-04    |
|   13913 | Islington                | Private room    | Private room in rental unit |              1 |          1 | $127.00 |                1 |                350 |                  57 |                       2 |                   4.86 | 2026-03-31    |
|   15400 | Kensington and Chelsea   | Entire home/apt | Entire rental unit          |              2 |          1 | $137.50 |                4 |                159 |                  98 |                       1 |                   4.81 | 2026-03-30    |
|   24328 | Wandsworth               | Entire home/apt | Entire townhouse            |              2 |          1 | $228.00 |                5 |                272 |                  97 |                       2 |                   4.9  | 2026-07-02    |
|   25081 | Haringey                 | Entire home/apt | Entire rental unit          |              4 |          2 | nan     |                3 |                  1 |                   0 |                       0 |                 nan    | nan           |
|   36299 | Richmond upon Thames     | Entire home/apt | Entire townhouse            |              5 |          3 | $290.00 |                3 |                350 |                 117 |                       2 |                   4.8  | 2026-08-18    |
|   17402 | Westminster              | Entire home/apt | Entire rental unit          |              6 |          3 | $517.50 |                3 |                175 |                  59 |                       3 |                   4.78 | 2026-09-07    |
| 2871410 | Islington                | Entire home/apt | Entire rental unit          |              2 |          2 | nan     |                6 |                  0 |                   3 |                       0 |                   5    | 2018-08-05    |
| 2878520 | Richmond upon Thames     | Entire home/apt | Entire home                 |              5 |          3 | nan     |                4 |                  0 |                   5 |                       0 |                   4.8  | 2017-07-30    |
| 2880265 | Richmond upon Thames     | Private room    | Private room in home        |              2 |          1 | $59.00  |                1 |                307 |                 160 |                      18 |                   4.88 | 2026-09-14    |
| 2889261 | Camden                   | Entire home/apt | Entire serviced apartment   |              5 |          3 | $525.00 |                1 |                328 |                 120 |                       3 |                   4.88 | 2026-08-27    |
| 2890867 | Hackney                  | Entire home/apt | Entire rental unit          |              3 |          1 | $215.67 |                3 |                 80 |                  42 |                       2 |                   4.88 | 2026-03-07    |
| 2895862 | Sutton                   | Private room    | Private room in home        |              7 |          3 | $77.00  |                3 |                 47 |                 304 |                       6 |                   4.93 | 2026-08-19    |
|   36660 | Haringey                 | Private room    | Private room in home        |              2 |          1 | $84.00  |                2 |                295 |                 767 |                      36 |                   4.87 | 2026-09-01    |
|   38605 | Hammersmith and Fulham   | Private room    | Private room in townhouse   |              2 |          1 | nan     |                2 |                  0 |                 388 |                       1 |                   4.77 | 2025-12-21    |

> Price is text with a `$` sign but the amounts are in **pounds**. 35% of prices are blank, mostly for inactive listings.

### Summary statistics (numeric columns)
| column                |   count |   mean |    std |   min |   25% |    50% |    75% |      max |
|:----------------------|--------:|-------:|-------:|------:|------:|-------:|-------:|---------:|
| price                 |   59905 | 248.35 | 577.02 | 10    | 99.67 | 175    | 279.75 | 75000    |
| accommodates          |   91954 |   3.41 |   2.13 |  1    |  2    |   3    |   4    |    16    |
| bedrooms              |   91909 |   1.54 |   1    |  0    |  1    |   1    |   2    |    30    |
| minimum_nights        |   91645 |   4.72 |  21.3  |  1    |  1    |   2    |   3    |  1125    |
| availability_365      |   91954 | 153.19 | 143.68 |  0    |  0    | 120    | 305    |   365    |
| number_of_reviews     |   91954 |  25.27 |  56.78 |  0    |  1    |   6    |  25    |  1959    |
| number_of_reviews_ltm |   91954 |   6.4  |  13.5  |  0    |  0    |   1    |   7    |   789    |
| review_scores_rating  |   71260 |   4.69 |   0.48 |  0    |  4.59 |   4.83 |   5    |     5    |
| reviews_per_month     |   71260 |   1.05 |   1.5  |  0.01 |  0.15 |   0.53 |   1.38 |    55.84 |

### Room types
| room_type       |   listings | share   |
|:----------------|-----------:|:--------|
| Entire home/apt |      61074 | 66.4%   |
| Private room    |      30471 | 33.1%   |
| Hotel room      |        207 | 0.2%    |
| Shared room     |        202 | 0.2%    |

### Top 10 boroughs by number of listings
| borough                |   listings |
|:-----------------------|-----------:|
| Westminster            |      10825 |
| Tower Hamlets          |       6723 |
| Kensington and Chelsea |       6271 |
| Camden                 |       6178 |
| Hackney                |       5740 |
| Southwark              |       5126 |
| Lambeth                |       4968 |
| Islington              |       4707 |
| Wandsworth             |       4611 |
| Hammersmith and Fulham |       4065 |

### All 90 columns
| column                                         | type    | missing   | example                                  |
|:-----------------------------------------------|:--------|:----------|:-----------------------------------------|
| `id`                                           | int64   | 0.0%      | 11551                                    |
| `listing_url`                                  | str     | 0.0%      | (hidden: personal data)                  |
| `scrape_id`                                    | int64   | 0.0%      | 20260917015706                           |
| `last_scraped`                                 | str     | 0.0%      | 2026-09-19                               |
| `source`                                       | str     | 64.9%     | previous scrape                          |
| `name`                                         | str     | 0.0%      | Artistic London Pied-à-Terre             |
| `description`                                  | str     | 0.8%      | Live like a local in this quintessentia… |
| `neighborhood_overview`                        | float64 | 100.0%    |                                          |
| `picture_url`                                  | str     | 0.0%      | (hidden: personal data)                  |
| `host_id`                                      | int64   | 0.0%      | 43039                                    |
| `host_url`                                     | str     | 0.0%      | (hidden: personal data)                  |
| `host_profile_id`                              | int64   | 0.0%      | (hidden: personal data)                  |
| `host_profile_url`                             | str     | 0.0%      | (hidden: personal data)                  |
| `host_name`                                    | str     | 0.0%      | (hidden: personal data)                  |
| `host_since`                                   | float64 | 100.0%    |                                          |
| `hosts_time_as_user_years`                     | float64 | 0.0%      | 16.0                                     |
| `hosts_time_as_user_months`                    | float64 | 0.0%      | 11.0                                     |
| `hosts_time_as_host_years`                     | float64 | 0.0%      | 15.0                                     |
| `hosts_time_as_host_months`                    | float64 | 0.0%      | 8.0                                      |
| `host_location`                                | str     | 24.9%     | London, United Kingdom                   |
| `host_about`                                   | str     | 46.4%     | (hidden: personal data)                  |
| `host_response_time`                           | float64 | 100.0%    |                                          |
| `host_response_rate`                           | float64 | 100.0%    |                                          |
| `host_acceptance_rate`                         | float64 | 100.0%    |                                          |
| `host_is_superhost`                            | str     | 0.0%      | f                                        |
| `host_thumbnail_url`                           | float64 | 100.0%    | (hidden: personal data)                  |
| `host_picture_url`                             | str     | 0.0%      | (hidden: personal data)                  |
| `host_neighbourhood`                           | float64 | 100.0%    |                                          |
| `host_listings_count`                          | int64   | 0.0%      | 1                                        |
| `host_total_listings_count`                    | float64 | 100.0%    |                                          |
| `host_verifications`                           | float64 | 100.0%    |                                          |
| `host_has_profile_pic`                         | str     | 0.0%      | t                                        |
| `host_identity_verified`                       | str     | 0.0%      | t                                        |
| `neighbourhood`                                | float64 | 100.0%    |                                          |
| `neighbourhood_cleansed`                       | str     | 0.0%      | Lambeth                                  |
| `neighbourhood_group_cleansed`                 | float64 | 100.0%    |                                          |
| `latitude`                                     | float64 | 0.0%      | 51.46095                                 |
| `longitude`                                    | float64 | 0.0%      | -0.11758                                 |
| `property_type`                                | str     | 0.0%      | Entire rental unit                       |
| `room_type`                                    | str     | 0.0%      | Entire home/apt                          |
| `accommodates`                                 | int64   | 0.0%      | 5                                        |
| `bathrooms`                                    | float64 | 100.0%    |                                          |
| `bathrooms_text`                               | str     | 0.1%      | 1 bath                                   |
| `bedrooms`                                     | float64 | 0.0%      | 1.0                                      |
| `beds`                                         | float64 | 2.2%      | 3.0                                      |
| `amenities`                                    | str     | 0.0%      | ["40 inch HDTV with Netflix, standard c… |
| `price`                                        | str     | 34.9%     | $267.50                                  |
| `price_quote_checkin_date`                     | str     | 31.8%     | 2026-09-23                               |
| `price_quote_checkout_date`                    | str     | 31.8%     | 2026-09-25                               |
| `price_quote_total_price`                      | float64 | 35.0%     | 535.0                                    |
| `price_quote_price_per_night`                  | float64 | 35.0%     | 267.5                                    |
| `price_quote_raw`                              | str     | 31.8%     | {"quote": {"taxes": null, "currency": "… |
| `minimum_nights`                               | float64 | 0.3%      | 1.0                                      |
| `maximum_nights`                               | float64 | 0.3%      | 1125.0                                   |
| `minimum_minimum_nights`                       | float64 | 0.3%      | 1.0                                      |
| `maximum_minimum_nights`                       | float64 | 0.3%      | 5.0                                      |
| `minimum_maximum_nights`                       | float64 | 0.3%      | 1.0                                      |
| `maximum_maximum_nights`                       | float64 | 0.3%      | 1125.0                                   |
| `minimum_nights_avg_ntm`                       | float64 | 0.0%      | 2.0                                      |
| `maximum_nights_avg_ntm`                       | float64 | 0.0%      | 84.0                                     |
| `calendar_updated`                             | float64 | 100.0%    |                                          |
| `has_availability`                             | str     | 0.8%      | t                                        |
| `availability_30`                              | int64   | 0.0%      | 15                                       |
| `availability_60`                              | int64   | 0.0%      | 44                                       |
| `availability_90`                              | int64   | 0.0%      | 74                                       |
| `availability_365`                             | int64   | 0.0%      | 349                                      |
| `calendar_last_scraped`                        | str     | 0.0%      | 2026-09-19                               |
| `number_of_reviews`                            | int64   | 0.0%      | 197                                      |
| `number_of_reviews_ltm`                        | int64   | 0.0%      | 7                                        |
| `number_of_reviews_l30d`                       | int64   | 0.0%      | 1                                        |
| `availability_eoy`                             | int64   | 0.0%      | 88                                       |
| `number_of_reviews_ly`                         | int64   | 0.0%      | 3                                        |
| `estimated_occupancy_l365d`                    | int64   | 0.0%      | 64                                       |
| `estimated_revenue_l365d`                      | float64 | 34.9%     | 17120.0                                  |
| `first_review`                                 | str     | 22.5%     | 2010-03-21                               |
| `last_review`                                  | str     | 22.5%     | 2026-09-04                               |
| `review_scores_rating`                         | float64 | 22.5%     | 4.55                                     |
| `review_scores_accuracy`                       | float64 | 22.5%     | 4.61                                     |
| `review_scores_cleanliness`                    | float64 | 22.5%     | 4.57                                     |
| `review_scores_checkin`                        | float64 | 22.5%     | 4.78                                     |
| `review_scores_communication`                  | float64 | 22.5%     | 4.84                                     |
| `review_scores_location`                       | float64 | 22.5%     | 4.54                                     |
| `review_scores_value`                          | float64 | 22.5%     | 4.49                                     |
| `license`                                      | float64 | 100.0%    |                                          |
| `instant_bookable`                             | float64 | 100.0%    |                                          |
| `calculated_host_listings_count`               | int64   | 0.0%      | 1                                        |
| `calculated_host_listings_count_entire_homes`  | int64   | 0.0%      | 1                                        |
| `calculated_host_listings_count_private_rooms` | int64   | 0.0%      | 0                                        |
| `calculated_host_listings_count_shared_rooms`  | int64   | 0.0%      | 0                                        |
| `reviews_per_month`                            | float64 | 22.5%     | 0.98                                     |

---

## 2. `calendar.csv.gz` (availability for the next 365 days)

### First 15 rows
|   listing_id | date       | available   |   minimum_nights |   maximum_nights |
|-------------:|:-----------|:------------|-----------------:|-----------------:|
|        11551 | 2026-09-19 | f           |                1 |             1125 |
|        17402 | 2026-09-18 | f           |                3 |             1125 |
|        17402 | 2026-09-19 | f           |                3 |             1125 |
|        17402 | 2026-09-20 | f           |                3 |             1125 |
|        17402 | 2026-09-21 | f           |                3 |             1125 |
|        17402 | 2026-09-22 | f           |                3 |             1125 |
|        17402 | 2026-09-23 | t           |                3 |             1125 |
|        17402 | 2026-09-24 | t           |                3 |             1125 |
|        17402 | 2026-09-25 | t           |                3 |             1125 |
|        17402 | 2026-09-26 | t           |                3 |             1125 |
|        17402 | 2026-09-27 | t           |                3 |             1125 |
|        17402 | 2026-09-28 | t           |                3 |             1125 |
|        17402 | 2026-09-29 | t           |                3 |             1125 |
|        17402 | 2026-09-30 | t           |                3 |             1125 |
|        17402 | 2026-10-01 | t           |                3 |             1125 |

`available` is `t` (open to book) or `f` (**unavailable: booked or blocked by the host; the data can't tell which**). This snapshot has no price column in the calendar.

### All columns
| column           | type   | missing   | example    |
|:-----------------|:-------|:----------|:-----------|
| `listing_id`     | int64  | 0.0%      | 11551      |
| `date`           | str    | 0.0%      | 2026-09-19 |
| `available`      | str    | 0.0%      | f          |
| `minimum_nights` | int64  | 0.0%      | 1          |
| `maximum_nights` | int64  | 0.0%      | 1125       |

---

## 3. `reviews.csv.gz` (guest reviews)

### First 10 rows (comments shortened; reviewer columns hidden)
|   listing_id |    id | date       | comments                                                               |
|-------------:|------:|:-----------|:-----------------------------------------------------------------------|
|        11551 | 30672 | 2010-03-21 | The flat was bright, comfortable and clean and Adriano was pleasant a… |
|        11551 | 32236 | 2010-03-29 | We stayed with Adriano and Valerio for a week when first moving to Lo… |
|        11551 | 41044 | 2010-05-09 | Adriano was a fantastic host. We felt very at home while staying ther… |
|        11551 | 48926 | 2010-06-01 | We had a most wonderful stay with Adriano and Valerio.  They are both… |
|        11551 | 58352 | 2010-06-28 | I'm not sure which of us misunderstood the situation, but I was not…   |
|        11551 | 66216 | 2010-07-18 | 5***** Stars for Adriano & Valerio                                     |
|              |       |            | <br/>If you are looking for a nice…                                    |
|        11551 | 79600 | 2010-08-16 | the place is in a quiet side road, very convenient (a 2 minute slow w… |
|        11551 | 89501 | 2010-09-03 | The room was as shown. Didn't have access to the living room much. I'… |
|        11551 | 97222 | 2010-09-14 | I had a great stay with Adriano! He was very friendly, knowledgeable … |
|        11551 | 97898 | 2010-09-15 | adriano is a sweet and totally gentle guy. his house is tiny, but SUP… |

Comments are free text, may contain HTML line breaks (`<br/>`), and some are in languages other than English.

### All columns (profile from the first 200,000 rows)
| column          | type   | missing   | example                                  |
|:----------------|:-------|:----------|:-----------------------------------------|
| `listing_id`    | int64  | 0.0%      | 11551                                    |
| `id`            | int64  | 0.0%      | 30672                                    |
| `date`          | str    | 0.0%      | 2010-03-21                               |
| `reviewer_id`   | int64  | 0.0%      | (hidden: personal data)                  |
| `reviewer_name` | str    | 0.0%      | (hidden: personal data)                  |
| `comments`      | str    | 0.0%      | The flat was bright, comfortable and cl… |

---

## 4. `neighbourhoods.geojson` (borough boundaries)

A GeoJSON `FeatureCollection` with 33 features, one per London borough (32 boroughs plus the City of London). Each feature has a polygon geometry and the properties `neighbourhood` (borough name, matching `neighbourhood_cleansed` in listings) and `neighbourhood_group` (empty for London).

Boroughs: Barking and Dagenham, Barnet, Bexley, Brent, Bromley, Camden, City of London, Croydon, Ealing, Enfield, Greenwich, Hackney, Hammersmith and Fulham, Haringey, Harrow, Havering, Hillingdon, Hounslow, Islington, Kensington and Chelsea, Kingston upon Thames, Lambeth, Lewisham, Merton, Newham, Redbridge, Richmond upon Thames, Southwark, Sutton, Tower Hamlets, Waltham Forest, Wandsworth, Westminster.
