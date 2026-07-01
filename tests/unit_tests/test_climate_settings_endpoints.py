"""Unit test pinning the migrated climate-settings read endpoint.

The 2026-07 migration moved the climate-settings read to the plain-Bearer
``/v1/vehicle/climate-settings`` route. (The old settings *write* was removed with
the actuation migration to ``POST /v2/remote/climate-control``.)
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from pytoyoda.api import Api
from pytoyoda.const import VEHICLE_CLIMATE_SETTINGS_ENDPOINT

VIN = "Random0815"


@pytest.mark.asyncio
async def test_get_climate_settings_hits_read_endpoint() -> None:
    """get_climate_settings must GET the migrated read route."""
    controller = AsyncMock()
    controller.request_json.return_value = {"status": {"messages": []}, "payload": None}
    api = Api(controller)

    await api.get_climate_settings(VIN)

    kwargs = controller.request_json.call_args.kwargs
    assert kwargs["method"] == "GET"
    assert kwargs["endpoint"] == VEHICLE_CLIMATE_SETTINGS_ENDPOINT
    assert kwargs["endpoint"] == "/v1/vehicle/climate-settings"
    assert kwargs["vin"] == VIN
