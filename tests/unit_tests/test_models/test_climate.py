"""Test climate status/settings models (/v1/vehicle/climate-*)."""

from datetime import timedelta

import pytest

from pytoyoda.models.climate import ClimateSettings, ClimateStatus
from pytoyoda.models.endpoints.climate import (
    ClimateSettingsResponseModel,
    ClimateStatusResponseModel,
)

# --- Fixtures: real off-state capture + synthesized on-state (decompiled shape) ---

STATUS_OFF = {"status": {"messages": []}, "payload": {"status": "stopped"}}

STATUS_ON = {
    "status": {"messages": []},
    "payload": {
        "status": "running",
        "startedAt": "2026-07-01T07:30:00Z",
        "updatedAt": "2026-07-01T07:36:00Z",
        "duration": 20,
        "currentTemperature": {"value": 21.5, "unit": "C"},
        "targetTemperature": {"value": 22.0, "unit": "C"},
        "heatingOptions": {
            "frontDefroster": "on",
            "rearDefogger": "off",
            "steeringHeater": "on",
        },
        "seatOptions": {
            "driverSeat": "high",
            "passengerSeat": "off",
            "rearDriverSeat": "low",
            "rearPassengerSeat": "medium",
        },
    },
}

SETTINGS = {
    "status": {"messages": []},
    "payload": {
        "duration": 20,
        "temperature": {"value": 18.0, "unit": "C"},
        "heatingOptions": {
            "frontDefroster": "off",
            "rearDefogger": "off",
            "steeringHeater": "off",
        },
        "seatOptions": {
            "driverSeat": "off",
            "passengerSeat": "off",
            "rearDriverSeat": "off",
            "rearPassengerSeat": "off",
        },
    },
}


def _status(body: dict) -> ClimateStatus:
    return ClimateStatus(ClimateStatusResponseModel(**body))


def _settings(body: dict) -> ClimateSettings:
    return ClimateSettings(ClimateSettingsResponseModel(**body))


class TestClimateStatus:
    """ClimateStatus wrapper."""

    def test_off_state_minimal_payload(self) -> None:
        """Off-state collapses to just ``status``; everything else is None."""
        st = _status(STATUS_OFF)
        assert st.status == "stopped"
        assert st.is_on is False
        assert st.started_at is None
        assert st.updated_at is None
        assert st.duration is None
        assert st.current_temperature is None
        assert st.target_temperature is None
        assert st.heating_options is None
        assert st.seat_options is None

    def test_on_state_full_payload(self) -> None:
        """On-state exposes the full rich shape without raising."""
        st = _status(STATUS_ON)
        assert st.is_on is True
        assert st.started_at is not None
        assert st.updated_at is not None
        assert st.duration == timedelta(minutes=20)
        assert st.current_temperature.value == 21.5
        assert st.current_temperature.unit == "C"
        assert st.target_temperature.value == 22.0
        assert st.heating_options.front_defroster is True
        assert st.heating_options.rear_defogger is False
        assert st.heating_options.steering_heater is True
        assert st.seat_options.driver_seat == "high"
        assert st.seat_options.passenger_seat == "off"
        assert st.seat_options.rear_driver_seat == "low"
        assert st.seat_options.rear_passenger_seat == "medium"

    @pytest.mark.parametrize(
        ("state", "expected"),
        [
            ("stopped", False),
            ("stopping", False),  # transitional-off
            ("starting", True),  # transitional-on
            ("running", True),
            ("RUNNING", True),  # case-insensitive
            ("weird", None),  # unknown enum -> None, never guessed
            (None, None),
        ],
    )
    def test_is_on_enum_mapping(self, state: str | None, expected: bool | None) -> None:
        """is_on maps the closed enum by intent; unknown/None -> None."""
        payload = {"status": state} if state is not None else {}
        body = {"status": {"messages": []}, "payload": payload}
        assert _status(body).is_on is expected

    def test_null_payload_degrades(self) -> None:
        """A None/absent payload (e.g. 403/500) must not raise."""
        assert _status({"status": {"messages": []}, "payload": None}).status is None
        assert ClimateStatus(None).status is None
        assert ClimateStatus(None).is_on is None

    def test_duration_is_minutes(self) -> None:
        """Duration is interpreted as minutes, not seconds."""
        body = {"status": {"messages": []}, "payload": {"status": "running", "duration": 15}}
        assert _status(body).duration == timedelta(minutes=15)

    def test_serialization_includes_computed_fields(self) -> None:
        """All computed fields serialize (the #268 @computed_field lesson)."""
        dumped = _status(STATUS_ON).model_dump()
        for key in (
            "status",
            "is_on",
            "started_at",
            "updated_at",
            "duration",
            "current_temperature",
            "target_temperature",
            "heating_options",
            "seat_options",
        ):
            assert key in dumped


class TestClimateSettings:
    """ClimateSettings wrapper."""

    def test_new_shape(self) -> None:
        """Temperature/duration/heating/seat come through the new payload."""
        se = _settings(SETTINGS)
        assert se.temperature.value == 18.0
        assert se.temperature.unit == "C"
        assert se.duration == timedelta(minutes=20)
        assert se.heating_options.front_defroster is False
        assert se.seat_options.driver_seat == "off"

    def test_deprecated_accessors_are_inert(self) -> None:
        """Back-compat accessors return None/[] (no data in the new payload)."""
        se = _settings(SETTINGS)
        assert se.settings_on is None
        assert se.min_temp is None
        assert se.max_temp is None
        assert se.temp_interval is None
        assert se.operations == []

    def test_null_payload_degrades(self) -> None:
        """A None/absent payload must not raise."""
        assert _settings({"status": {"messages": []}, "payload": None}).temperature is None
        assert ClimateSettings(None).temperature is None
