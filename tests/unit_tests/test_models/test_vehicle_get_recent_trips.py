"""Tests for Vehicle.get_recent_trips."""

from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from pytoyoda.models.endpoints.trips import _TripModel
from pytoyoda.models.trips import Trip
from pytoyoda.models.vehicle import Vehicle


def _make_trip_dict(trip_id: str = "abc-123") -> dict:
    """Minimum-viable _TripModel-shaped dict for round-tripping through Trip()."""
    return {
        "id": trip_id,
        "category": 0,
        "summary": {
            "startTs": "2026-04-26T07:06:45Z",
            "endTs": "2026-04-26T07:15:54Z",
            "startLat": 47.1652,
            "startLon": 20.2178,
            "endLat": 47.1927,
            "endLon": 20.1938,
            "length": 4943,
            "duration": 549,
        },
        "scores": None,
        "behaviours": None,
        "hdc": None,
        "route": None,
    }


def _make_vehicle_with_mock_api(trips_payload_factory) -> Vehicle:
    """Build a Vehicle with a stub Api.get_trips that returns the payload built
    by trips_payload_factory(call_args). The factory receives the same kwargs
    that get_trips() was called with, so each test can assert on them."""
    captured: dict = {}

    async def fake_get_trips(vin, from_date, to_date, **kwargs):
        captured.update(
            vin=vin, from_date=from_date, to_date=to_date, **kwargs
        )
        payload = trips_payload_factory(captured)
        return SimpleNamespace(payload=payload)

    api = MagicMock()
    api.get_trips = AsyncMock(side_effect=fake_get_trips)

    vehicle_info = SimpleNamespace(
        vin="VIN1234567890",
        nickname="RAV4",
    )
    # Vehicle.__init__ does some work that depends on having both api and
    # vehicle_info present. We bypass via __new__ to avoid the
    # CustomAPIBaseModel pydantic init machinery; the methods we test only
    # need _api, _vehicle_info, _metric set.
    v = Vehicle.__new__(Vehicle)
    v._api = api
    v._vehicle_info = vehicle_info
    v._metric = True
    v._endpoint_data = {}
    # expose for tests that want to assert on call args
    v._fake_captured = captured  # type: ignore[attr-defined]
    return v


def _payload_with_trips(trip_count: int):
    """Factory: returns N _TripModel-shaped dicts wrapped as a payload."""
    def factory(_call_args):
        trip_dicts = [
            _make_trip_dict(trip_id=f"trip-{i}") for i in range(trip_count)
        ]
        # _TripModel construction via pydantic; shape matches the API response.
        trips = [_TripModel(**d) for d in trip_dicts]
        return SimpleNamespace(trips=trips)
    return factory


@pytest.mark.asyncio
async def test_returns_list_of_trips():
    v = _make_vehicle_with_mock_api(_payload_with_trips(3))
    result = await v.get_recent_trips(limit=3)
    assert len(result) == 3
    assert all(isinstance(t, Trip) for t in result)


@pytest.mark.asyncio
async def test_passes_limit_and_route_through():
    v = _make_vehicle_with_mock_api(_payload_with_trips(5))
    await v.get_recent_trips(limit=5, with_route=True)
    captured = v._fake_captured  # type: ignore[attr-defined]
    assert captured["limit"] == 5
    assert captured["route"] is True
    assert captured["summary"] is False
    assert captured["offset"] == 0


@pytest.mark.asyncio
async def test_default_dates_are_today_minus_90_to_today():
    v = _make_vehicle_with_mock_api(_payload_with_trips(1))
    await v.get_recent_trips()
    captured = v._fake_captured  # type: ignore[attr-defined]
    today = date.today()
    assert captured["to_date"] == today
    assert captured["from_date"] == today - timedelta(days=90)


@pytest.mark.asyncio
async def test_explicit_dates_override_defaults():
    v = _make_vehicle_with_mock_api(_payload_with_trips(1))
    fd, td = date(2026, 4, 1), date(2026, 4, 15)
    await v.get_recent_trips(from_date=fd, to_date=td)
    captured = v._fake_captured  # type: ignore[attr-defined]
    assert captured["from_date"] == fd
    assert captured["to_date"] == td


@pytest.mark.asyncio
async def test_empty_payload_returns_empty_list():
    async def fake_get_trips(*_a, **_kw):
        return SimpleNamespace(payload=None)

    api = MagicMock()
    api.get_trips = AsyncMock(side_effect=fake_get_trips)

    v = Vehicle.__new__(Vehicle)
    v._api = api
    v._vehicle_info = SimpleNamespace(vin="VINX", nickname="X")
    v._metric = True
    v._endpoint_data = {}

    result = await v.get_recent_trips()
    assert result == []


@pytest.mark.asyncio
async def test_payload_with_none_trips_returns_empty_list():
    """Toyota has been observed returning payloads where trips is None
    (separate from payload itself being None). Defensive check ensures
    we don't crash trying to iterate None."""
    async def fake_get_trips(*_a, **_kw):
        return SimpleNamespace(payload=SimpleNamespace(trips=None))

    api = MagicMock()
    api.get_trips = AsyncMock(side_effect=fake_get_trips)

    v = Vehicle.__new__(Vehicle)
    v._api = api
    v._vehicle_info = SimpleNamespace(vin="VINX", nickname="X")
    v._metric = True
    v._endpoint_data = {}

    result = await v.get_recent_trips()
    assert result == []


@pytest.mark.asyncio
async def test_zero_trips_returns_empty_list():
    v = _make_vehicle_with_mock_api(_payload_with_trips(0))
    result = await v.get_recent_trips(limit=5)
    assert result == []


@pytest.mark.asyncio
async def test_limit_below_one_raises():
    v = _make_vehicle_with_mock_api(_payload_with_trips(1))
    with pytest.raises(ValueError, match="limit must be between 1 and 50"):
        await v.get_recent_trips(limit=0)


@pytest.mark.asyncio
async def test_limit_above_fifty_raises():
    v = _make_vehicle_with_mock_api(_payload_with_trips(1))
    with pytest.raises(ValueError, match="limit must be between 1 and 50"):
        await v.get_recent_trips(limit=51)


@pytest.mark.asyncio
async def test_with_route_false_by_default():
    v = _make_vehicle_with_mock_api(_payload_with_trips(2))
    await v.get_recent_trips(limit=2)
    captured = v._fake_captured  # type: ignore[attr-defined]
    assert captured["route"] is False


@pytest.mark.asyncio
async def test_offset_passes_through_to_api():
    """Non-zero offset reaches Api.get_trips for paginated fetches."""
    v = _make_vehicle_with_mock_api(_payload_with_trips(3))
    await v.get_recent_trips(limit=3, offset=10)
    captured = v._fake_captured  # type: ignore[attr-defined]
    assert captured["offset"] == 10
    assert captured["limit"] == 3


@pytest.mark.asyncio
async def test_offset_negative_raises():
    """Negative offset is rejected before any API call."""
    v = _make_vehicle_with_mock_api(_payload_with_trips(1))
    with pytest.raises(ValueError, match="offset must be >= 0"):
        await v.get_recent_trips(limit=5, offset=-1)
