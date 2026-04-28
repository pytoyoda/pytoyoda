"""Tests for Vehicle.update() - per-endpoint optional flag handling.

Covers the contract introduced for ha_toyota#291: an endpoint marked
`optional=True` whose call raises is caught, recorded in
Vehicle._endpoint_errors, and does NOT abort the rest of the cycle.
Required endpoints (default) still propagate as before.
"""

from __future__ import annotations

from typing import Any

import pytest

from pytoyoda.models.vehicle import EndpointDefinition, Vehicle


class _FakeApi:
    """Stub Api object that satisfies Vehicle's constructor."""

    pass


class _FakeVehicleInfo:
    """Minimal vehicle info shape: a vin and feature/capability stubs."""

    class _Features:
        pass

    class _ExtCaps:
        pass

    def __init__(self, vin: str = "TESTVIN0000000001") -> None:
        self.vin = vin
        self.features = self._Features()
        self.extended_capabilities = self._ExtCaps()


def _build_vehicle_with_endpoints(endpoints: list[EndpointDefinition]) -> Vehicle:
    """Build a Vehicle and override _api_endpoints / _endpoint_collect.

    Bypasses Vehicle.__init__'s endpoint construction so tests can inject
    arbitrary EndpointDefinition lists with controlled call behaviour.
    """
    v = Vehicle.__new__(Vehicle)
    v._api = _FakeApi()
    v._vehicle_info = _FakeVehicleInfo()
    v._metric = True
    v._endpoint_data = {}
    v._endpoint_errors = {}
    v._api_endpoints = endpoints
    v._endpoint_collect = [
        (e.name, e.function, e.optional) for e in endpoints if e.capable
    ]
    return v


@pytest.mark.asyncio
async def test_required_endpoint_failure_propagates() -> None:
    """A required endpoint that raises causes update() to raise."""
    boom = RuntimeError("required endpoint exploded")

    async def good() -> str:
        return "fresh"

    async def bad() -> Any:
        raise boom

    v = _build_vehicle_with_endpoints(
        [
            EndpointDefinition("a", capable=True, function=good),
            EndpointDefinition("b", capable=True, function=bad),  # required (default)
            EndpointDefinition("c", capable=True, function=good),
        ]
    )

    with pytest.raises(RuntimeError, match="required endpoint exploded"):
        await v.update()
    # 'a' fetched before the failure should be in data; 'c' never ran.
    assert v._endpoint_data.get("a") == "fresh"
    assert "c" not in v._endpoint_data
    assert v._endpoint_errors == {}


@pytest.mark.asyncio
async def test_optional_endpoint_failure_swallowed_and_recorded() -> None:
    """An optional endpoint that raises is caught + recorded; loop continues."""
    boom = RuntimeError("climate 500")

    async def good_a() -> str:
        return "a-value"

    async def bad() -> Any:
        raise boom

    async def good_c() -> str:
        return "c-value"

    v = _build_vehicle_with_endpoints(
        [
            EndpointDefinition("a", capable=True, function=good_a),
            EndpointDefinition("b", capable=True, function=bad, optional=True),
            EndpointDefinition("c", capable=True, function=good_c),
        ]
    )

    # Should not raise.
    await v.update()
    assert v._endpoint_data["a"] == "a-value"
    assert "b" not in v._endpoint_data
    assert v._endpoint_data["c"] == "c-value"
    assert "b" in v._endpoint_errors
    assert v._endpoint_errors["b"] is boom


@pytest.mark.asyncio
async def test_endpoint_errors_resets_each_update() -> None:
    """A successful re-run clears stale entries from _endpoint_errors."""
    state = {"raise": True}

    async def maybe_bad() -> str:
        if state["raise"]:
            raise RuntimeError("transient")
        return "now-fine"

    v = _build_vehicle_with_endpoints(
        [EndpointDefinition("x", capable=True, function=maybe_bad, optional=True)]
    )

    await v.update()
    assert "x" in v._endpoint_errors

    state["raise"] = False
    await v.update()
    assert v._endpoint_data["x"] == "now-fine"
    assert "x" not in v._endpoint_errors  # cleared on the new cycle


@pytest.mark.asyncio
async def test_skip_does_not_record_as_error() -> None:
    """Endpoints filtered via skip= are not called; not in errors."""
    async def good() -> str:
        return "ok"

    async def boom() -> Any:
        raise RuntimeError("would have failed")

    v = _build_vehicle_with_endpoints(
        [
            EndpointDefinition("a", capable=True, function=good),
            EndpointDefinition("b", capable=True, function=boom, optional=True),
        ]
    )

    await v.update(skip=["b"])
    assert v._endpoint_data == {"a": "ok"}
    assert v._endpoint_errors == {}


@pytest.mark.asyncio
async def test_only_filter_works_with_optional_flag() -> None:
    """only= filters endpoints; optional flag still applies for those that run."""
    async def good() -> str:
        return "ok"

    async def boom() -> Any:
        raise RuntimeError("optional boom")

    v = _build_vehicle_with_endpoints(
        [
            EndpointDefinition("a", capable=True, function=good),
            EndpointDefinition("b", capable=True, function=boom, optional=True),
            EndpointDefinition("c", capable=True, function=good),
        ]
    )

    await v.update(only=["b"])
    assert v._endpoint_data == {}  # b raised, a/c filtered out
    assert "b" in v._endpoint_errors
