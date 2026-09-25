"""Test electric_status Model."""

from types import SimpleNamespace

from pytoyoda.const import KILOMETERS_UNIT
from pytoyoda.models.electric_status import ElectricStatus
from pytoyoda.utils.models import Distance


def _make_electric_status_stub(**overrides):
    """Create a minimal stub for _electric_status with sensible defaults."""
    base = {
        "battery_level": 30.0,
        "phev_usable_battery_level": None,
        "charging_status": "none",
        "remaining_charge_time": None,
        "ev_range": None,
        "ev_range_with_ac": None,
        "can_set_next_charging_event": None,
        "last_update_timestamp": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _make_electric_status(ev_stub):
    """Create an ElectricStatus instance wired to our stub."""
    es = ElectricStatus(electric_status=None, metric=True)
    es._electric_status = ev_stub  # type: ignore[attr-defined]
    es._distance_unit = KILOMETERS_UNIT  # type: ignore[attr-defined]
    return es


def test_ev_range_zero_is_preserved():
    ev_stub = _make_electric_status_stub(
        ev_range=Distance(value=0.0, unit=KILOMETERS_UNIT),
        ev_range_with_ac=Distance(value=0.0, unit=KILOMETERS_UNIT),
    )
    status = _make_electric_status(ev_stub)

    # core numeric values
    assert status.ev_range == 0.0
    assert status.ev_range_with_ac == 0.0

    # with unit wrappers
    ev_with_unit = status.ev_range_with_unit
    assert ev_with_unit is not None
    assert ev_with_unit.value == 0.0
    assert ev_with_unit.unit == KILOMETERS_UNIT

    ev_ac_with_unit = status.ev_range_with_ac_with_unit
    assert ev_ac_with_unit is not None
    assert ev_ac_with_unit.value == 0.0
    assert ev_ac_with_unit.unit == KILOMETERS_UNIT


def test_phev_usable_battery_level_is_exposed_separately_from_battery_level():
    ev_stub = _make_electric_status_stub(
        battery_level=93.0,
        phev_usable_battery_level=87.0,
    )
    status = _make_electric_status(ev_stub)

    assert status.battery_level == 93.0
    assert status.phev_usable_battery_level == 87.0


def test_phev_usable_battery_level_defaults_to_none_when_absent():
    ev_stub = _make_electric_status_stub(battery_level=93.0)
    status = _make_electric_status(ev_stub)

    assert status.battery_level == 93.0
    assert status.phev_usable_battery_level is None


def test_phev_usable_battery_level_none_when_no_electric_status():
    status = ElectricStatus(electric_status=None, metric=True)

    assert status.phev_usable_battery_level is None


def test_ev_range_none_is_treated_as_missing():
    ev_stub = _make_electric_status_stub(ev_range=None, ev_range_with_ac=None)
    status = _make_electric_status(ev_stub)

    assert status.ev_range is None
    assert status.ev_range_with_unit is None
    assert status.ev_range_with_ac is None
    assert status.ev_range_with_ac_with_unit is None


def test_remaining_charge_time_plausible_value_is_preserved():
    ev_stub = _make_electric_status_stub(
        charging_status="charging",
        remaining_charge_time=120,
    )
    status = _make_electric_status(ev_stub)

    assert status.remaining_charge_time == 120


def test_remaining_charge_time_sentinel_is_filtered_when_not_charging():
    for sentinel in (65535, 65335):
        ev_stub = _make_electric_status_stub(
            charging_status="none",
            remaining_charge_time=sentinel,
        )
        status = _make_electric_status(ev_stub)

        assert status.remaining_charge_time is None


def test_remaining_charge_time_high_value_preserved_while_charging():
    # If the vehicle really is charging, we have no way to disambiguate a
    # slow/trickle-charge estimate from a sentinel, so the raw value should
    # be passed through unchanged.
    ev_stub = _make_electric_status_stub(
        charging_status="charging",
        remaining_charge_time=65535,
    )
    status = _make_electric_status(ev_stub)

    assert status.remaining_charge_time == 65535


def test_remaining_charge_time_none_is_preserved():
    ev_stub = _make_electric_status_stub(
        charging_status="none",
        remaining_charge_time=None,
    )
    status = _make_electric_status(ev_stub)

    assert status.remaining_charge_time is None
