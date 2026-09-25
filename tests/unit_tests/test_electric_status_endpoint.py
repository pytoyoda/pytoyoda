"""Unit test pinning the migrated electric-status read endpoint.

The 2026-09 migration moved the electric-status read off the retired
/v1/global/remote/electric/status route (now SigV4-fenced -> APIGW-403) to
/v1/vehicle/electric/status, mirroring the earlier /v1/vehicle/status and
/v1/vehicle/climate-* migrations. Only this GET read route is migrated; the
realtime-status wake and command routes are left untouched.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from pytoyoda.api import Api
from pytoyoda.const import (
    VEHICLE_GLOBAL_REMOTE_ELECTRIC_CONTROL_ENDPOINT,
    VEHICLE_GLOBAL_REMOTE_ELECTRIC_REALTIME_STATUS_ENDPOINT,
    VEHICLE_GLOBAL_REMOTE_ELECTRIC_STATUS_ENDPOINT,
)

VIN = "Random0815"


@pytest.mark.asyncio
async def test_get_vehicle_electric_status_hits_migrated_endpoint() -> None:
    """get_vehicle_electric_status must GET the migrated read route."""
    controller = AsyncMock()
    controller.request_json.return_value = {"status": {"messages": []}, "payload": None}
    api = Api(controller)

    await api.get_vehicle_electric_status(VIN)

    kwargs = controller.request_json.call_args.kwargs
    assert kwargs["method"] == "GET"
    assert kwargs["endpoint"] == VEHICLE_GLOBAL_REMOTE_ELECTRIC_STATUS_ENDPOINT
    assert kwargs["endpoint"] == "/v1/vehicle/electric/status"
    assert kwargs["vin"] == VIN


def test_electric_realtime_and_control_routes_untouched() -> None:
    """The realtime-status wake and command routes stay on the legacy family.

    This migration only repoints the GET read route; there is no evidence the
    realtime-status wake or the electric command endpoint were retired, so
    they must remain unchanged.
    """
    assert (
        VEHICLE_GLOBAL_REMOTE_ELECTRIC_REALTIME_STATUS_ENDPOINT
        == "/v1/global/remote/electric/realtime-status"
    )
    assert (
        VEHICLE_GLOBAL_REMOTE_ELECTRIC_CONTROL_ENDPOINT
        == "/v1/global/remote/electric/command"
    )
