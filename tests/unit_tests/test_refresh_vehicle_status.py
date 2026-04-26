"""Unit tests for the new refresh_vehicle_status() POST flow.

Covers Api.refresh_vehicle_status (body shape + endpoint) and
Vehicle.refresh_status (delegation), keyed off the cache-expiry mechanism
discovery on 2026-04-24 and Track B design (Addendum 4 of the remediation plan).
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from pytoyoda.api import Api
from pytoyoda.const import VEHICLE_GLOBAL_REMOTE_REFRESH_STATUS_ENDPOINT
from pytoyoda.models.endpoints.refresh_status import RefreshStatusResponseModel

VIN = "Random0815"
GUID = "123e4567-e89b-12d3-a456-426614174000"


@pytest.mark.asyncio
async def test_refresh_vehicle_status_sends_correct_body_and_endpoint():
    """The POST must hit /refresh-status with the four-field body shape that
    the gateway requires (deviceId/deviceType/guid/vin). Without these fields
    the gateway returns 500 (the trap PR #302 fell into)."""
    controller = AsyncMock()
    controller._uuid = GUID
    controller.request_json.return_value = {"status": {"messages": []}, "payload": {}}

    api = Api(controller)

    await api.refresh_vehicle_status(VIN)

    controller.request_json.assert_called_once()
    kwargs = controller.request_json.call_args.kwargs
    assert kwargs["method"] == "POST"
    assert kwargs["endpoint"] == VEHICLE_GLOBAL_REMOTE_REFRESH_STATUS_ENDPOINT
    assert kwargs["vin"] == VIN
    body = kwargs["body"]
    assert body == {
        "deviceId": "pytoyoda",
        "deviceType": "Android",
        "guid": GUID,
        "vin": VIN,
    }


@pytest.mark.asyncio
async def test_refresh_vehicle_status_parses_response_with_return_code():
    """The 'returnCode' field on the JSON payload becomes return_code on the
    parsed model (snake_case via Pydantic Field alias)."""
    controller = AsyncMock()
    controller._uuid = GUID
    controller.request_json.return_value = {
        "status": {"messages": []},
        "payload": {"returnCode": "000000"},
    }

    api = Api(controller)
    result = await api.refresh_vehicle_status(VIN)

    assert isinstance(result, RefreshStatusResponseModel)
    assert result.payload is not None
    assert result.payload.return_code == "000000"


@pytest.mark.asyncio
async def test_refresh_vehicle_status_handles_layer1_failure_payload():
    """Non-000000 returnCode (vehicle does not support endpoint) parses as
    a regular response - the caller decides what to do with it."""
    controller = AsyncMock()
    controller._uuid = GUID
    controller.request_json.return_value = {
        "status": {"messages": []},
        "payload": {"returnCode": "010001"},
    }

    api = Api(controller)
    result = await api.refresh_vehicle_status(VIN)

    assert result.payload.return_code == "010001"


@pytest.mark.asyncio
async def test_vehicle_refresh_status_delegates_to_api():
    """Vehicle.refresh_status() is a thin wrapper over Api.refresh_vehicle_status."""
    from pytoyoda.models.vehicle import Vehicle

    api = AsyncMock()
    api.refresh_vehicle_status.return_value = RefreshStatusResponseModel(
        status={"messages": []}, payload={}
    )

    # Build a minimal Vehicle without going through the full bootstrap; tests
    # only exercise the refresh_status delegation.
    vehicle = Vehicle.__new__(Vehicle)
    vehicle._api = api  # noqa: SLF001
    vehicle._vehicle_info = type(  # type: ignore[attr-defined]
        "_Stub", (), {"vin": VIN}
    )()

    result = await vehicle.refresh_status()

    api.refresh_vehicle_status.assert_called_once_with(VIN)
    assert isinstance(result, RefreshStatusResponseModel)
