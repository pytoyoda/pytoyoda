"""Tests for the vehicle_guid endpoint models."""

from __future__ import annotations

import json
from pathlib import Path

from pytoyoda.models.endpoints.vehicle_guid import (
    VehicleGuidModel,
    VehiclesResponseModel,
    _FeaturesModel,
)

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


def test_payload_parses_with_multiple_omitted_fields() -> None:
    """Regressions for #282/#287/#229/#284: several fields Toyota may omit.

    In addition to 'remoteDisplay', accounts without an active subscription
    can be missing 'shopGenuinePartsUrl', 'registrationNumber', 'hwType',
    'emergencyContact' and 'fleetInd'. None of these should collapse the
    vehicle (or the whole payload list) to None.
    """
    with DATA_FILE.open(encoding="utf-8") as file:
        response = json.load(file)
    omitted_fields = (
        "remoteDisplay",
        "shopGenuinePartsUrl",
        "registrationNumber",
        "hwType",
        "emergencyContact",
        "fleetInd",
    )
    for vehicle in response["payload"]:
        for field in omitted_fields:
            vehicle.pop(field, None)

    parsed = VehiclesResponseModel(**response)

    assert parsed.payload is not None
    assert len(parsed.payload) == len(response["payload"])
    vehicle = parsed.payload[0]
    assert vehicle.vin == response["payload"][0]["vin"]
    assert vehicle.remote_display is None
    assert vehicle.shop_genuine_parts_url is None
    assert vehicle.registration_number is None
    assert vehicle.hw_type is None
    assert vehicle.emergency_contact is None
    assert vehicle.fleet_ind is None


def test_features_model_parses_partial_payload() -> None:
    """Regression for #285: Toyota only ever returns a subset of feature keys.

    ``_FeaturesModel`` declares 77 fields. Real API responses have been
    observed with as few as 23 of them; without default=None on every field
    the model failed validation with ~60 "Field required" errors and
    ``invalid_to_none`` silently turned the whole ``features`` object (and,
    for vehicles, the vehicle list) into None.
    """
    partial = {
        "achPayment": 0,
        "chargingStation": 1,
        "dealerAppointment": 1,
        "drivingAnalytics": 1,
        "evChargeStation": 1,
        "homeCharge": 1,
        "lastParked": 1,
        "privacy": 1,
        "remoteService": 1,
        "sendToCar": 1,
        "serviceHistory": 1,
        "shopGenuineParts": 0,
        "smartCharging": 1,
        "telemetry": 1,
        "vehicleDiagnostic": 1,
        "vehicleStatus": 1,
        "whoIsDriving": 0,
    }

    features = _FeaturesModel.model_validate(partial)

    assert features.ach_payment == 0
    assert features.charging_station == 1
    assert features.last_parked == 1
    assert features.telemetry == 1
    assert features.vehicle_status == 1
    # Every key absent from the payload must be None, not reject the model.
    assert features.auto_drive is None
    assert features.cerence is None
    assert features.xcapp is None
    assert features.wifi is None


def test_vehicle_guid_model_parses_with_sparse_features_and_no_subscription() -> None:
    """Full-vehicle regression for #285/#284 combined.

    A vehicle whose subscription has lapsed may be missing 'remoteDisplay'
    *and* only report a handful of 'features' keys. Neither should prevent
    the vehicle itself from parsing.
    """
    with DATA_FILE.open(encoding="utf-8") as file:
        response = json.load(file)
    vehicle_data = response["payload"][0]
    del vehicle_data["remoteDisplay"]
    vehicle_data["features"] = {"lastParked": 1, "telemetry": 1}

    vehicle = VehicleGuidModel(**vehicle_data)

    assert vehicle.remote_display is None
    assert vehicle.features is not None
    assert vehicle.features.last_parked == 1
    assert vehicle.features.telemetry == 1
    assert vehicle.features.privacy is None
