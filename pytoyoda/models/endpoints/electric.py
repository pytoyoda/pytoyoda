"""Toyota Connected Services API - Electric Models."""

# ruff: noqa: FA100

from datetime import datetime, time, timedelta, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_serializer, field_validator

from pytoyoda.models.endpoints.common import StatusModel, UnitValueModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class NextChargingEvent(BaseModel):
    """Model representing the next charging event.

    Attributes:
        event_type: The Event Type of the charging event.
        timestamp: The calculated timestamp of the charging event.
    """

    event_type: str
    timestamp: datetime


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

    next_charging_event: Optional[NextChargingEvent] = Field(
        alias="nextChargingEvent", default=None
    )

    @field_validator("next_charging_event", mode="before")
    @classmethod
    def deserialize_next_charging_event(
        cls,
        v: dict[str, any],
    ) -> Optional[NextChargingEvent]:
        """Function that deserializes the next charging event.

        Attributes:
            cls: The Current Class
            v: The API Response from the Toyota API
                event can be scheduled.
        Returns: The NextChargingEvent Object or None
        """
        if v is None:
            return None

        week_day = v.get("weekDay")
        start = v.get("startTime")
        end = v.get("endTime")

        if week_day is None or (start is None and end is None):
            return None

        ref = datetime.now(timezone.utc).astimezone()
        # toyotas api only send back start or end time
        event_time = end or start
        event_dt_today = datetime.combine(
            ref.date(),
            time(event_time["hour"], event_time["minute"]),
            tzinfo=ref.tzinfo,
        )
        # Calculate days until the weekday
        days_ahead = ((week_day - 1) - ref.weekday() + 7) % 7
        event_dt = event_dt_today + timedelta(days=days_ahead)

        # If the event is today and the time is over, use next week
        if event_dt <= ref:
            event_dt += timedelta(days=7)

        return NextChargingEvent(event_type=v.get("type"), timestamp=event_dt)


class ElectricResponseModel(StatusModel):
    """Model representing an electric vehicle response.

    Inherits from StatusModel.

    Attributes:
        payload: The electric vehicle status data if request was successful.

    """

    payload: Optional[ElectricStatusModel] = None


class ChargeTime(CustomEndpointBaseModel):
    """Model representing a charging time configuration.

    Attributes:
        hour: Hour when charging starts/ends (0-23), e.g., 14
        minute: Minute when charging starts/ends (0-59), e.g., 30

    """

    hour: int = Field(alias="hour")
    minute: int = Field(alias="minute")


class ReservationCharge(CustomEndpointBaseModel):
    """Model representing a charging reservation configuration.

    Attributes:
        chargeType: Type of charging schedule.
        day: Day of the week when charging starts/ends, e.g., THURSDAY
        startTime: Optional start time for the charging window
        endTime: Optional end time for the charging window

    """

    chargetype: str = Field(alias="chargeType")
    day: str = Field(alias="day")
    starttime: Optional[ChargeTime] = Field(alias="startTime", default=None)
    endtime: Optional[ChargeTime] = Field(alias="endTime", default=None)


class NextChargeSettings(CustomEndpointBaseModel):
    """Model representing the next charge settings configuration.

    Attributes:
        command: The command to control the next charge cycle.
        reservationCharge: Optional details for scheduled charging
        (e.g., charge type, time). Must be a ReservationCharge model.

    """

    command: str = Field(alias="command")
    reservationcharge: Optional[ReservationCharge] = Field(
        alias="reservationCharge", default=None
    )
