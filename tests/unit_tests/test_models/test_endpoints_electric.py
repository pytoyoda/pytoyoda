"""Test electric endpoint models."""

from pytoyoda.models.endpoints.electric import ElectricStatusModel


def test_electric_status_model_parses_phev_usable_battery_level():
    """PhevUsableBatteryLevel should be parsed as a distinct field from batteryLevel."""
    model = ElectricStatusModel.model_validate(
        {
            "batteryLevel": 93,
            "phevUsableBatteryLevel": 87,
        }
    )

    assert model.battery_level == 93
    assert model.phev_usable_battery_level == 87


def test_electric_status_model_phev_usable_battery_level_absent():
    """phevUsableBatteryLevel is optional; existing responses without it parse fine."""
    model = ElectricStatusModel.model_validate(
        {
            "batteryLevel": 79,
            "canSetNextChargingEvent": True,
            "chargingStatus": "none",
        }
    )

    assert model.battery_level == 79
    assert model.phev_usable_battery_level is None
