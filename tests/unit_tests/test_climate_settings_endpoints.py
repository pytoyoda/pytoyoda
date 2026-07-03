"""Unit tests pinning the climate-settings read/write endpoint split.

The 2026-07 migration moved the climate-settings *read* to the plain-Bearer
``/v1/vehicle/climate-settings`` route while the *write* stays on the retired
``/v1/global/remote/climate-settings`` route (already SigV4-fenced; removed with the
actuation migration). These tests lock the split so a future edit cannot silently
repoint the write at the read route (or vice-versa).
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from pytoyoda.api import Api
from pytoyoda.const import (
    VEHICLE_CLIMATE_SETTINGS_ENDPOINT,
    VEHICLE_CLIMATE_SETTINGS_WRITE_ENDPOINT,
)
from pytoyoda.models.endpoints.climate import ClimateSettingsRequestModel

VIN = "Random0815"


def test_read_and_write_consts_differ() -> None:
    """The read (migrated) and write (legacy) settings routes must be distinct."""
    assert VEHICLE_CLIMATE_SETTINGS_ENDPOINT == "/v1/vehicle/climate-settings"
    assert (
        VEHICLE_CLIMATE_SETTINGS_WRITE_ENDPOINT
        == "/v1/global/remote/climate-settings"
    )
    assert VEHICLE_CLIMATE_SETTINGS_ENDPOINT != VEHICLE_CLIMATE_SETTINGS_WRITE_ENDPOINT


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
    assert kwargs["vin"] == VIN


@pytest.mark.asyncio
async def test_update_climate_settings_hits_write_endpoint() -> None:
    """update_climate_settings must PUT the legacy write route, NOT the read route."""
    controller = AsyncMock()
    controller.request_json.return_value = {"status": {"messages": []}}
    api = Api(controller)

    await api.update_climate_settings(
        VIN, ClimateSettingsRequestModel(temperature=21.0)
    )

    kwargs = controller.request_json.call_args.kwargs
    assert kwargs["method"] == "PUT"
    assert kwargs["endpoint"] == VEHICLE_CLIMATE_SETTINGS_WRITE_ENDPOINT
    assert kwargs["endpoint"] != VEHICLE_CLIMATE_SETTINGS_ENDPOINT
    assert kwargs["vin"] == VIN
