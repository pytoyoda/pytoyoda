"""Unit test for Vehicle.set_climate delegation to Api.send_climate_control_command.

The public Vehicle.set_climate wrapper exists so consumers actuate climate without
reaching into the private ``vehicle._api``. It is a thin pass-through: it forwards the
vehicle's VIN and the V2 request body and returns the parsed acknowledgement.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from pytoyoda.models.endpoints.climate import (
    RemoteClimateControlResponseModel,
    V2RemoteClimateControlRequestModel,
)
from pytoyoda.models.vehicle import Vehicle

VIN = "Random0815"


@pytest.mark.asyncio
async def test_vehicle_set_climate_delegates_to_api() -> None:
    """Vehicle.set_climate() forwards vin + request to send_climate_control_command."""
    api = AsyncMock()
    api.send_climate_control_command.return_value = RemoteClimateControlResponseModel(
        status={"messages": []}, payload={"returnCode": "000000"}
    )

    vehicle = Vehicle.__new__(Vehicle)
    vehicle._api = api  # noqa: SLF001
    vehicle._vehicle_info = type(  # type: ignore[attr-defined]
        "_Stub", (), {"vin": VIN}
    )()

    request = V2RemoteClimateControlRequestModel(command="stop")
    result = await vehicle.set_climate(request)

    api.send_climate_control_command.assert_called_once_with(VIN, request)
    assert isinstance(result, RemoteClimateControlResponseModel)
    assert result.payload.return_code == "000000"
