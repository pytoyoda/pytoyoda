"""Regression tests for Vehicle.get_summary limit & offset (pytoyoda#162)."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from pytoyoda.models.endpoints.trips import _HistogramModel, _SummaryItemModel
from pytoyoda.models.summary import SummaryType
from pytoyoda.models.vehicle import Vehicle


def _daily_summary_item(year: int, month: int, days: list[int]) -> _SummaryItemModel:
    histograms = [
        _HistogramModel(
            year=year,
            month=month,
            day=d,
            summary={
                "length": 1000,
                "duration": 60,
                "averageSpeed": 20.0,
                "fuelConsumption": 100.0,
            },
        )
        for d in days
    ]
    return _SummaryItemModel(
        year=year, month=month, summary=None, histograms=histograms
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
async def test_get_summary_default_behavior_unchanged_no_limit_offset():
    v = _make_vehicle_with_payload([_daily_summary_item(2026, 1, list(range(1, 11)))])
    result = await v.get_summary(
        date(2026, 1, 1), date(2026, 1, 31), summary_type=SummaryType.DAILY
    )
    assert len(result) == 10


@pytest.mark.asyncio
async def test_get_summary_limit_smaller_than_available():
    v = _make_vehicle_with_payload([_daily_summary_item(2026, 1, list(range(1, 11)))])
    result = await v.get_summary(
        date(2026, 1, 1), date(2026, 1, 31), summary_type=SummaryType.DAILY, limit=3
    )
    assert len(result) == 3
    assert [s.from_date.day for s in result] == [1, 2, 3]


@pytest.mark.asyncio
async def test_get_summary_offset_without_limit():
    v = _make_vehicle_with_payload([_daily_summary_item(2026, 1, list(range(1, 11)))])
    result = await v.get_summary(
        date(2026, 1, 1), date(2026, 1, 31), summary_type=SummaryType.DAILY, offset=7
    )
    assert len(result) == 3
    assert [s.from_date.day for s in result] == [8, 9, 10]


@pytest.mark.asyncio
async def test_get_summary_offset_combined_with_limit():
    v = _make_vehicle_with_payload([_daily_summary_item(2026, 1, list(range(1, 11)))])
    result = await v.get_summary(
        date(2026, 1, 1),
        date(2026, 1, 31),
        summary_type=SummaryType.DAILY,
        offset=2,
        limit=4,
    )
    assert [s.from_date.day for s in result] == [3, 4, 5, 6]


@pytest.mark.asyncio
async def test_get_summary_limit_exceeds_available():
    v = _make_vehicle_with_payload([_daily_summary_item(2026, 1, [1, 2])])
    result = await v.get_summary(
        date(2026, 1, 1), date(2026, 1, 31), summary_type=SummaryType.DAILY, limit=50
    )
    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_summary_invalid_limit_raises():
    v = _make_vehicle_with_payload([_daily_summary_item(2026, 1, [1])])
    with pytest.raises(ValueError, match="limit must be >= 1"):
        await v.get_summary(
            date(2026, 1, 1), date(2026, 1, 31), summary_type=SummaryType.DAILY, limit=0
        )


@pytest.mark.asyncio
async def test_get_summary_negative_offset_raises():
    v = _make_vehicle_with_payload([_daily_summary_item(2026, 1, [1])])
    with pytest.raises(ValueError, match="offset must be >= 0"):
        await v.get_summary(
            date(2026, 1, 1),
            date(2026, 1, 31),
            summary_type=SummaryType.DAILY,
            offset=-1,
        )
