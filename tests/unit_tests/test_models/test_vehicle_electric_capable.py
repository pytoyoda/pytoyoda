"""Tests for Vehicle._electric_capable() and the electric_status endpoint gate.

Regression coverage for ha_toyota#302: some vehicles (rebadged Suzuki
DCM24-backend BEVs, e.g. the Urban Cruiser) report
`econnect_vehicle_status_capable=False` in `extended_capabilities` even
though they are genuine electric vehicles, leaving every EV sensor stuck on
`unknown` because the electric_status endpoint was never even attempted.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from pytoyoda.models.endpoints.vehicle_guid import VehicleGuidModel
from pytoyoda.models.vehicle import Vehicle


def _vehicle_guid_payload(
    *,
    vin: str = "SB1TESTVIN00000001",
    ev_vehicle: bool = False,
    fuel_type: str = "P",
    econnect_vehicle_status_capable: bool = False,
) -> dict[str, Any]:
    """Return a minimal raw `/v2/vehicle/guid` payload."""
    return {
        "alerts": [],
        "brand": "T",
        "capabilities": [],
        "evVehicle": ev_vehicle,
        "extendedCapabilities": {
            "econnectVehicleStatusCapable": econnect_vehicle_status_capable,
        },
        "features": {},
        "fuelType": fuel_type,
        "nickName": "Test Toyota",
        "services": [],
        "subscriptions": [],
        "vin": vin,
    }


def _fake_api():
    """Return an API stub with the callables Vehicle.__init__ expects."""

    async def _noop(*_args, **_kwargs):
        return None

    return SimpleNamespace(
        get_climate_settings=_noop,
        get_climate_status=_noop,
        get_location=_noop,
        get_notifications=_noop,
        get_remote_status=_noop,
        get_service_history=_noop,
        get_telemetry=_noop,
        get_trips=_noop,
        get_vehicle_electric_status=_noop,
        get_vehicle_health_status=_noop,
    )


def _build_vehicle(payload: dict[str, Any]) -> Vehicle:
    return Vehicle(_fake_api(), VehicleGuidModel.model_validate(payload), metric=True)


def _electric_status_endpoint(vehicle: Vehicle):
    return next(e for e in vehicle._api_endpoints if e.name == "electric_status")  # noqa: SLF001


def test_econnect_flag_true_is_still_capable() -> None:
    """The original signal (flag=True) keeps working unchanged."""
    vehicle = _build_vehicle(
        _vehicle_guid_payload(econnect_vehicle_status_capable=True, fuel_type="P")
    )
    assert _electric_status_endpoint(vehicle).capable is True


def test_fuel_type_e_is_capable_even_when_flag_is_false() -> None:
    """Regression for #302: fuelType == 'E' should widen detection.

    Toyota's registry reports econnect_vehicle_status_capable=False and
    evVehicle=False for some Suzuki DCM24-backend BEVs (e.g. the Urban
    Cruiser), yet fuelType correctly says "E". Falling back to fuel_type
    must pick these up.
    """
    vehicle = _build_vehicle(
        _vehicle_guid_payload(
            econnect_vehicle_status_capable=False, ev_vehicle=False, fuel_type="E"
        )
    )
    assert _electric_status_endpoint(vehicle).capable is True


def test_ev_vehicle_flag_true_is_capable_even_when_econnect_flag_is_false() -> None:
    """The evVehicle flag alone should also widen detection."""
    vehicle = _build_vehicle(
        _vehicle_guid_payload(
            econnect_vehicle_status_capable=False, ev_vehicle=True, fuel_type="P"
        )
    )
    assert _electric_status_endpoint(vehicle).capable is True


def test_ice_vehicle_stays_not_capable() -> None:
    """A regular petrol vehicle must not gain a false-positive EV gate."""
    vehicle = _build_vehicle(
        _vehicle_guid_payload(
            econnect_vehicle_status_capable=False, ev_vehicle=False, fuel_type="P"
        )
    )
    assert _electric_status_endpoint(vehicle).capable is False


def test_electric_status_endpoint_is_optional() -> None:
    """electric_status must not abort update() for the whole vehicle.

    Even with the widened heuristic, a false-positive gate (or an account
    provisioning gap) failing this endpoint should not cost the vehicle
    its other fresh data for the cycle. See ha_toyota#302.
    """
    vehicle = _build_vehicle(_vehicle_guid_payload(fuel_type="E"))
    assert _electric_status_endpoint(vehicle).optional is True
