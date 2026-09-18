"""Regression tests for Vehicle.get_trips / get_last_trip limit & offset.

Covers pytoyoda/pytoyoda#162: get_summary (and, by extension, get_trips /
get_last_trip which share the same pagination bugs) does not honour limit
and offset. These tests pin the fixed semantics:

- ``limit`` bounds the *total* number of trips returned to the caller, not
  the page size sent to the API.
- ``offset`` skips that many trips from the start of the most-recent-first
  result set before ``limit`` is applied.
- No more API pages are fetched than necessary to satisfy limit/offset.
- ``get_last_trip(offset=N)`` returns the (N+1)-th most recent trip.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from pytoyoda.models.endpoints.trips import _TripModel
from pytoyoda.models.trips import Trip
from pytoyoda.models.vehicle import Vehicle

PAGE_SIZE = 5


def _make_trip_dict(trip_index: int) -> dict:
    return {
        "id": str(uuid.UUID(int=trip_index)),
        "category": 0,
        "summary": {
            "startTs": "2026-01-01T08:00:00Z",
            "endTs": "2026-01-01T08:10:00Z",
            "startLat": 47.1,
            "startLon": 20.2,
            "endLat": 47.2,
            "endLon": 20.3,
            "length": 5000,
            "duration": 600,
        },
        "scores": None,
        "behaviours": None,
        "hdc": None,
        "route": None,
    }


class _FakeApi:
    """Stub Api.get_trips that pages through `total` synthetic trips.

    Each call is recorded so tests can assert exactly how many pages (and
    with what offsets) were requested - this is what pins down "don't keep
    fetching once limit is satisfied".
    """

    def __init__(self, total: int, page_size: int = PAGE_SIZE) -> None:
        self.total = total
        self.page_size = page_size
        self.calls: list[dict] = []
        self.get_trips = AsyncMock(side_effect=self._get_trips)

    async def _get_trips(self, vin, from_date, to_date, **kwargs):  # noqa: ANN001, ARG002
        self.calls.append(kwargs)
        offset = kwargs["offset"]
        limit = kwargs["limit"]
        ids = list(range(offset, min(offset + limit, self.total)))
        trips = [_TripModel(**_make_trip_dict(i)) for i in ids]
        next_offset = offset + limit if offset + limit < self.total else None
        pagination = SimpleNamespace(next_offset=next_offset)
        metadata = SimpleNamespace(pagination=pagination)
        payload = SimpleNamespace(trips=trips, metadata=metadata)
        return SimpleNamespace(payload=payload)


def _make_vehicle(api: _FakeApi) -> Vehicle:
    v = Vehicle.__new__(Vehicle)
    v._api = api
    v._vehicle_info = SimpleNamespace(vin="VIN1234567890", nickname="RAV4")
    v._metric = True
    v._endpoint_data = {}
    return v


@pytest.mark.asyncio
async def test_get_trips_default_behavior_unchanged_no_limit():
    """No limit/offset -> every trip is returned (previous behaviour)."""
    api = _FakeApi(total=12)
    v = _make_vehicle(api)

    result = await v.get_trips(date.today() - timedelta(days=1), date.today())

    assert len(result) == 12
    assert all(isinstance(t, Trip) for t in result)
    # 12 trips at page size 5 -> 3 pages (5, 5, 2)
    assert len(api.calls) == 3


@pytest.mark.asyncio
async def test_get_trips_limit_smaller_than_one_page():
    """limit within the first page -> only one API call, bounded result."""
    api = _FakeApi(total=20)
    v = _make_vehicle(api)

    result = await v.get_trips(date.today() - timedelta(days=1), date.today(), limit=3)

    assert len(result) == 3
    assert len(api.calls) == 1


@pytest.mark.asyncio
async def test_get_trips_limit_spanning_multiple_pages():
    """limit larger than one page -> fetch just enough pages, no more."""
    api = _FakeApi(total=20, page_size=5)
    v = _make_vehicle(api)

    result = await v.get_trips(date.today() - timedelta(days=1), date.today(), limit=8)

    assert len(result) == 8
    # Needs pages covering offsets 0-4 and 5-9 -> 2 calls, not looping to 20.
    assert len(api.calls) == 2


@pytest.mark.asyncio
async def test_get_trips_offset_without_limit():
    """offset alone -> skip N trips, still return the rest of them all."""
    api = _FakeApi(total=10)
    v = _make_vehicle(api)

    result = await v.get_trips(date.today() - timedelta(days=1), date.today(), offset=4)

    assert len(result) == 6
    assert result[0]._trip.id == uuid.UUID(int=4)


@pytest.mark.asyncio
async def test_get_trips_offset_combined_with_limit():
    """offset + limit -> a bounded window starting at offset."""
    api = _FakeApi(total=20)
    v = _make_vehicle(api)

    result = await v.get_trips(
        date.today() - timedelta(days=1), date.today(), offset=6, limit=3
    )

    assert [t._trip.id for t in result] == [
        uuid.UUID(int=6),
        uuid.UUID(int=7),
        uuid.UUID(int=8),
    ]


@pytest.mark.asyncio
async def test_get_trips_limit_exceeds_available_trips():
    """limit larger than the total available -> just return what exists."""
    api = _FakeApi(total=4)
    v = _make_vehicle(api)

    result = await v.get_trips(date.today() - timedelta(days=1), date.today(), limit=50)

    assert len(result) == 4


@pytest.mark.asyncio
async def test_get_trips_invalid_limit_raises():
    api = _FakeApi(total=4)
    v = _make_vehicle(api)
    with pytest.raises(ValueError, match="limit must be >= 1"):
        await v.get_trips(date.today() - timedelta(days=1), date.today(), limit=0)


@pytest.mark.asyncio
async def test_get_trips_negative_offset_raises():
    api = _FakeApi(total=4)
    v = _make_vehicle(api)
    with pytest.raises(ValueError, match="offset must be >= 0"):
        await v.get_trips(date.today() - timedelta(days=1), date.today(), offset=-1)


@pytest.mark.asyncio
async def test_get_last_trip_returns_most_recent_by_default():
    api = _FakeApi(total=10)
    v = _make_vehicle(api)

    trip = await v.get_last_trip()

    assert trip is not None
    assert trip._trip.id == uuid.UUID(int=0)
    # Bounded to a single page/trip fetch, not the whole history.
    assert len(api.calls) == 1


@pytest.mark.asyncio
async def test_get_last_trip_with_offset_returns_nth_most_recent():
    api = _FakeApi(total=10)
    v = _make_vehicle(api)

    trip = await v.get_last_trip(offset=3)

    assert trip is not None
    assert trip._trip.id == uuid.UUID(int=3)


@pytest.mark.asyncio
async def test_get_last_trip_offset_beyond_history_returns_none():
    api = _FakeApi(total=3)
    v = _make_vehicle(api)

    trip = await v.get_last_trip(offset=10)

    assert trip is None


@pytest.mark.asyncio
async def test_get_last_trip_no_trips_returns_none():
    api = _FakeApi(total=0)
    v = _make_vehicle(api)

    trip = await v.get_last_trip()

    assert trip is None
