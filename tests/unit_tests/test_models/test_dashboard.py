"""Test dashboard Model."""

from types import SimpleNamespace

from pytoyoda.const import KILOMETERS_UNIT
from pytoyoda.models.dashboard import Dashboard
from pytoyoda.utils.models import Distance


def _make_telemetry_stub(**overrides):
    base = {
        "odometer": Distance(value=17148.0, unit=KILOMETERS_UNIT),
        "fuel_level": 52,
        "battery_level": 30.0,
        "distance_to_empty": Distance(value=326.0, unit=KILOMETERS_UNIT),
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _make_electric_stub(**overrides):
    base = {
        "battery_level": 30.0,
        "charging_status": "none",
        "remaining_charge_time": None,
        "fuel_range": Distance(value=326.0, unit=KILOMETERS_UNIT),
        "ev_range": Distance(value=0.0, unit=KILOMETERS_UNIT),
        "ev_range_with_ac": Distance(value=0.0, unit=KILOMETERS_UNIT),
        "can_set_next_charging_event": None,
        "last_update_timestamp": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _make_dashboard(telemetry_stub, electric_stub):
    dash = Dashboard(
        telemetry=None,
        electric=None,
        health=None,
        metric=True,
    )
    dash._telemetry = telemetry_stub  # type: ignore[attr-defined]
    dash._electric = electric_stub  # type: ignore[attr-defined]
    dash._distance_unit = KILOMETERS_UNIT  # type: ignore[attr-defined]
    return dash


def test_battery_range_zero_does_not_fall_back_to_fuel():
    telemetry = _make_telemetry_stub(
        # distance_to_empty is fuel-only range here
        distance_to_empty=Distance(value=326.0, unit=KILOMETERS_UNIT),
    )
    electric = _make_electric_stub(
        ev_range=Distance(value=0.0, unit=KILOMETERS_UNIT),
        ev_range_with_ac=Distance(value=0.0, unit=KILOMETERS_UNIT),
        fuel_range=Distance(value=326.0, unit=KILOMETERS_UNIT),
    )

    dash = _make_dashboard(telemetry, electric)

    # EV-only range should be 0, not 326
    assert dash.battery_range == 0.0
    br_with_unit = dash.battery_range_with_unit
    assert br_with_unit is not None
    assert br_with_unit.value == 0.0
    assert br_with_unit.unit == KILOMETERS_UNIT

    # AC-based EV range should also be 0
    assert dash.battery_range_with_ac == 0.0
    br_ac_with_unit = dash.battery_range_with_ac_with_unit
    assert br_ac_with_unit is not None
    assert br_ac_with_unit.value == 0.0
    assert br_ac_with_unit.unit == KILOMETERS_UNIT

    # Fuel-only range should remain 326
    assert dash.fuel_range == 326.0
    fr_with_unit = dash.fuel_range_with_unit
    assert fr_with_unit is not None
    assert fr_with_unit.value == 326.0
    assert fr_with_unit.unit == KILOMETERS_UNIT

    # Total range (based on telemetry distance_to_empty) is still 326
    assert dash.range == 326.0
    total_with_unit = dash.range_with_unit
    assert total_with_unit is not None
    assert total_with_unit.value == 326.0
    assert total_with_unit.unit == KILOMETERS_UNIT


def test_battery_range_falls_back_to_telemetry_when_ev_missing():
    telemetry = _make_telemetry_stub(
        battery_level=30.0,
        distance_to_empty=Distance(value=200.0, unit=KILOMETERS_UNIT),
    )
    # Simulate a car where ev_range is not provided at all
    electric = _make_electric_stub(ev_range=None, ev_range_with_ac=None)

    dash = _make_dashboard(telemetry, electric)

    # With no EV range from the electric endpoint, we should use telemetry
    assert dash.battery_range == 200.0
    br_with_unit = dash.battery_range_with_unit
    assert br_with_unit is not None
    assert br_with_unit.value == 200.0
    assert br_with_unit.unit == KILOMETERS_UNIT
