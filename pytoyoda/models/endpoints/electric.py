"""Toyota Connected Services API - Electric Models."""

# ruff: noqa: FA100

from datetime import datetime, timedelta
from typing import Optional

from pydantic import Field, field_serializer

from pytoyoda.models.endpoints.common import StatusModel, UnitValueModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class ElectricStatusModel(CustomEndpointBaseModel):
    """Model representing the status of an electric vehicle.

    Attributes:
        battery_level: The battery level of the electric vehicle
            as a percentage (0-100).
        can_set_next_charging_event: Indicates whether the next charging
            event can be scheduled.
        charging_status: The current charging status of the electric vehicle.
        ev_range: The estimated driving range with current battery charge.
        ev_range_with_ac: The estimated driving range with AC running.
        fuel_level: The fuel level for hybrid vehicles as a percentage (0-100).
        fuel_range: The estimated driving range on current fuel (for hybrid vehicles).
        last_update_timestamp: When the data was last updated from the vehicle.
        remaining_charge_time: Minutes remaining until battery is fully charged.

    """

    battery_level: Optional[int] = Field(
        alias="batteryLevel",
        default=None,
    )
    can_set_next_charging_event: Optional[bool] = Field(
        alias="canSetNextChargingEvent", default=None
    )
    charging_status: Optional[str] = Field(alias="chargingStatus", default=None)
    ev_range: Optional[UnitValueModel] = Field(alias="evRange", default=None)
    ev_range_with_ac: Optional[UnitValueModel] = Field(
        alias="evRangeWithAc", default=None
    )
    fuel_level: Optional[int] = Field(
        alias="fuelLevel",
        default=None,
    )
    fuel_range: Optional[UnitValueModel] = Field(alias="fuelRange", default=None)
    last_update_timestamp: Optional[datetime] = Field(
        alias="lastUpdateTimestamp", default=None
    )
    remaining_charge_time: Optional[int] = Field(
        alias="remainingChargeTime",
        default=None,
        description="Time remaining in minutes until fully charged",
    )

    @field_serializer("remaining_charge_time")
    def serialize_remaining_time(
        self, remaining_time: Optional[int]
    ) -> Optional[timedelta]:
        """Convert minutes to timedelta for better usability."""
        return None if remaining_time is None else timedelta(minutes=remaining_time)


class ElectricResponseModel(StatusModel):
    """Model representing an electric vehicle response.

    Inherits from StatusModel.

    Attributes:
        payload: The electric vehicle status data if request was successful.

    """

    payload: Optional[ElectricStatusModel] = None
