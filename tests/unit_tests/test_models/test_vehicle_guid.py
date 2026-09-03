"""Tests for the vehicle_guid endpoint models."""

from __future__ import annotations

import json
from pathlib import Path

from pytoyoda.models.endpoints.vehicle_guid import VehiclesResponseModel

DATA_FILE = Path(__file__).parents[1] / "data" / "v2_vehicleguid.json"


def test_payload_parses_without_remote_display() -> None:
    """Regression for #277: 'remoteDisplay' is absent for some accounts.

    Without default=None the required field failed validation and
    ``invalid_to_none`` turned the whole payload list into None, so
    ``get_vehicles()`` reported "No vehicles found".
    """
    with DATA_FILE.open(encoding="utf-8") as file:
        response = json.load(file)
    for vehicle in response["payload"]:
        del vehicle["remoteDisplay"]

    parsed = VehiclesResponseModel(**response)

    assert parsed.payload is not None
    assert len(parsed.payload) == len(response["payload"])
    assert parsed.payload[0].vin == response["payload"][0]["vin"]
    assert parsed.payload[0].remote_display is None
