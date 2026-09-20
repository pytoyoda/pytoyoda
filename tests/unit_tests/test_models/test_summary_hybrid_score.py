"""Unit tests for Summary.hybrid_score (pytoyoda/ha_toyota#93)."""

from __future__ import annotations

from datetime import date

from pytoyoda.models.endpoints.trips import _SummaryBaseModel
from pytoyoda.models.summary import Summary


def _summary_with_scores(scores: list[int] | None) -> Summary:
    return Summary(
        summary=_SummaryBaseModel.model_validate({"length": 1000, "duration": 60}),
        metric=True,
        from_date=date(2024, 1, 1),
        to_date=date(2024, 1, 31),
        hdc=None,
        scores=scores,
    )


def test_hybrid_score_averages_multiple_scores():
    summary = _summary_with_scores([80, 90, 70])
    assert summary.hybrid_score == 80.0


def test_hybrid_score_ignores_missing_scores_mixed_in():
    # Simulates some days/months having scores=None (excluded before reaching
    # Summary) mixed with days that did report a score.
    summary = _summary_with_scores([100, 50])
    assert summary.hybrid_score == 75.0


def test_hybrid_score_none_when_no_scores_reported():
    summary = _summary_with_scores(None)
    assert summary.hybrid_score is None


def test_hybrid_score_none_when_scores_list_empty():
    summary = _summary_with_scores([])
    assert summary.hybrid_score is None
