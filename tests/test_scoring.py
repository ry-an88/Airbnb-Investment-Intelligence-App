import pandas as pd
import pytest

from airbnb.scoring import PERSONA_WEIGHTS, explain_row, score


@pytest.mark.parametrize("persona", list(PERSONA_WEIGHTS))
def test_persona_weights_add_up_to_one(persona):
    assert sum(PERSONA_WEIGHTS[persona].values()) == pytest.approx(1.0)


@pytest.fixture
def summary():
    return pd.DataFrame({
        "area": ["A", "B", "C", "Tiny"],
        "active_listings": [200, 50, 40, 3],
        "median_price": [150, 120, 90, 500],
        "median_occupancy": [0.5, 0.4, 0.2, 0.7],
        "median_revenue": [20000, 15000, 6000, 90000],
        "avg_rating": [4.8, 4.7, 4.3, 5.0],
    })


def test_small_areas_are_excluded(summary):
    assert "Tiny" not in score(summary)["area"].tolist()


def test_points_add_up_to_score(summary):
    result = score(summary)
    points = result.filter(like="_points").sum(axis=1)
    assert (points - result["investment_score"]).abs().max() <= 0.3  # rounding only


def test_best_area_ranks_first_and_score_is_0_to_100(summary):
    result = score(summary)
    assert result.loc[0, "area"] == "A"
    assert result["investment_score"].between(0, 100).all()


def test_explanation_mentions_score_and_confidence(summary):
    row = score(summary).iloc[0]
    text = explain_row(row)
    assert "/100" in text and "High confidence" in text


def test_empty_result_when_no_area_is_big_enough(summary):
    assert score(summary, min_listings=1000).empty
