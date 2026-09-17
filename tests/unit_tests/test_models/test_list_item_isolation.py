"""Tests for CustomEndpointBaseModel's per-item list validation tolerance.

See #284: a single malformed item in a ``list[CustomEndpointBaseModel]``
field used to null out the *entire* list (e.g. one bad vehicle erased every
vehicle on the account), because ``invalid_to_none`` wrapped the whole list
field rather than each item. ``make_invalid_items_to_none`` fixes this by
validating each item independently and dropping only the offending ones.
"""

from __future__ import annotations

import json
from pathlib import Path

from pytoyoda.models.endpoints.vehicle_guid import VehiclesResponseModel

DATA_FILE = Path(__file__).parents[1] / "data" / "v2_vehicleguid.json"


def test_one_malformed_vehicle_does_not_erase_the_whole_list() -> None:
    """A garbage entry in payload must not collapse the other, valid vehicles."""
    with DATA_FILE.open(encoding="utf-8") as file:
        response = json.load(file)
    good_vehicle = response["payload"][0]
    second_good_vehicle = {**good_vehicle, "vin": "SECONDVIN000000"}
    # A completely malformed entry: not even a mapping, so it can never be
    # coerced into a VehicleGuidModel no matter how lenient the field
    # defaults are.
    garbage_entry = "not-a-vehicle-object"
    response["payload"] = [good_vehicle, garbage_entry, second_good_vehicle]

    parsed = VehiclesResponseModel(**response)

    assert parsed.payload is not None
    assert len(parsed.payload) == 2
    assert {v.vin for v in parsed.payload} == {
        good_vehicle["vin"],
        "SECONDVIN000000",
    }


def test_all_malformed_items_still_degrade_gracefully() -> None:
    """If every item is malformed, the list becomes empty, not an exception."""
    response = {
        "status": {"messages": []},
        "payload": ["garbage-one", "garbage-two"],
    }

    parsed = VehiclesResponseModel(**response)

    assert parsed.payload == []
