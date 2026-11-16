import pandas as pd

from airbnb.clean import clean_listings, data_quality_report, parse_bathrooms, parse_price


def test_parse_price_handles_symbols_commas_and_missing():
    result = parse_price(pd.Series(["$1,250.00", "$80.00", None, "free"]))
    assert result.iloc[0] == 1250.0
    assert result.iloc[1] == 80.0
    assert result.iloc[2:].isna().all()


def test_parse_bathrooms_reads_text_and_half_bath():
    result = parse_bathrooms(pd.Series(["1.5 shared baths", "Half-bath", None]))
    assert result.iloc[0] == 1.5
    assert result.iloc[1] == 0.5
    assert pd.isna(result.iloc[2])


def test_clean_flags_bad_prices_without_dropping_rows(raw_listings):
    df = clean_listings(raw_listings)
    assert len(df) == len(raw_listings)
    assert df["price_valid"].tolist() == [True, True, False, False]


def test_active_flag_uses_last_year_of_reviews(raw_listings):
    df = clean_listings(raw_listings)
    assert df["is_active"].tolist() == [True, True, False, False]


def test_quality_report_counts_missing_price(raw_listings):
    report = data_quality_report(clean_listings(raw_listings)).set_index("check")
    assert report.loc["Missing or unreadable price", "count"] == 1
