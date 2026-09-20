"""Integration-ish tests for hybrid_score aggregation through Vehicle summaries.

Covers the plumbing added for pytoyoda/ha_toyota#93: the per-day/month
``scores.global`` values reported by the Toyota API are collected while
building daily/weekly/monthly/yearly ``Summary`` objects, and exposed as
``Summary.hybrid_score``.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from pytoyoda.models.endpoints.trips import _HistogramModel, _SummaryItemModel
from pytoyoda.models.summary import SummaryType
from pytoyoda.models.vehicle import Vehicle


def _histogram(
    year: int, month: int, day: int, global_score: int | None
) -> _HistogramModel:
    return _HistogramModel(
        year=year,
        month=month,
        day=day,
        summary={
            "length": 1000,
            "duration": 60,
            "averageSpeed": 20.0,
            "fuelConsumption": 100.0,
        },
        scores=(
            {"global": global_score, "acceleration": 80, "braking": 80}
            if global_score is not None
            else None
        ),
    )


def _make_vehicle_with_payload(summary_items: list[_SummaryItemModel]) -> Vehicle:
    payload = SimpleNamespace(summary=summary_items)
    api = MagicMock()
    api.get_trips = AsyncMock(return_value=SimpleNamespace(payload=payload))

    v = Vehicle.__new__(Vehicle)
    v._api = api
    v._vehicle_info = SimpleNamespace(vin="VIN1234567890", nickname="RAV4")
    v._metric = True
    v._endpoint_data = {}
    return v


@pytest.mark.asyncio
async def test_daily_summary_hybrid_score_present():
    item = _SummaryItemModel(
        year=2026,
        month=1,
        summary=None,
        histograms=[_histogram(2026, 1, 1, 90)],
    )
    v = _make_vehicle_with_payload([item])
    result = await v.get_summary(
        date(2026, 1, 1), date(2026, 1, 31), summary_type=SummaryType.DAILY
    )
    assert result[0].hybrid_score == 90.0


@pytest.mark.asyncio
async def test_daily_summary_hybrid_score_none_when_not_reported():
    item = _SummaryItemModel(
        year=2026,
        month=1,
        summary=None,
        histograms=[_histogram(2026, 1, 1, None)],
    )
    v = _make_vehicle_with_payload([item])
    result = await v.get_summary(
        date(2026, 1, 1), date(2026, 1, 31), summary_type=SummaryType.DAILY
    )
    assert result[0].hybrid_score is None


@pytest.mark.asyncio
async def test_weekly_summary_averages_only_days_with_scores():
    # Days 1-3 fall in the same ISO week; day 2 has no score reported.
    item = _SummaryItemModel(
        year=2026,
        month=1,
        summary=None,
        histograms=[
            _histogram(2026, 1, 1, 80),
            _histogram(2026, 1, 2, None),
            _histogram(2026, 1, 3, 90),
        ],
    )
    v = _make_vehicle_with_payload([item])
    result = await v.get_summary(
        date(2026, 1, 1), date(2026, 1, 31), summary_type=SummaryType.WEEKLY
    )
    assert len(result) == 1
    assert result[0].hybrid_score == 85.0


@pytest.mark.asyncio
async def test_monthly_summary_hybrid_score_from_month_level_scores():
    item = _SummaryItemModel(
        year=2026,
        month=1,
        summary={"length": 5000, "duration": 300},
        scores={"global": 75, "acceleration": 70, "braking": 70},
        histograms=[_histogram(2026, 1, 1, 75)],
    )
    v = _make_vehicle_with_payload([item])
    result = await v.get_summary(
        date(2026, 1, 1), date(2026, 1, 31), summary_type=SummaryType.MONTHLY
    )
    assert len(result) == 1
    assert result[0].hybrid_score == 75.0


@pytest.mark.asyncio
async def test_monthly_summary_hybrid_score_none_when_month_has_no_score():
    item = _SummaryItemModel(
        year=2026,
        month=1,
        summary={"length": 5000, "duration": 300},
        scores=None,
        histograms=[_histogram(2026, 1, 1, None)],
    )
    v = _make_vehicle_with_payload([item])
    result = await v.get_summary(
        date(2026, 1, 1), date(2026, 1, 31), summary_type=SummaryType.MONTHLY
    )
    assert len(result) == 1
    assert result[0].hybrid_score is None


@pytest.mark.asyncio
async def test_yearly_summary_averages_across_months():
    items = [
        _SummaryItemModel(
            year=2026,
            month=1,
            summary={"length": 5000, "duration": 300},
            scores={"global": 60, "acceleration": 60, "braking": 60},
            histograms=[_histogram(2026, 1, 1, 60)],
        ),
        _SummaryItemModel(
            year=2026,
            month=2,
            summary={"length": 5000, "duration": 300},
            scores=None,
            histograms=[_histogram(2026, 2, 1, None)],
        ),
        _SummaryItemModel(
            year=2026,
            month=3,
            summary={"length": 5000, "duration": 300},
            scores={"global": 100, "acceleration": 90, "braking": 90},
            histograms=[_histogram(2026, 3, 1, 100)],
        ),
    ]
    v = _make_vehicle_with_payload(items)
    result = await v.get_summary(
        date(2026, 1, 1), date(2026, 12, 31), summary_type=SummaryType.YEARLY
    )
    assert len(result) == 1
    assert result[0].hybrid_score == 80.0
