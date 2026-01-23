"""Toyota Connected Services API - Electric Models."""

# ruff: noqa: FA100

from dataclasses import dataclass
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
        charging_schedules: List of charging schedules configured in the vehicle.

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
    charging_schedules: Optional[list["ChargingSchedule"]] = Field(
        alias="chargingSchedules", default=None
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


class Days(BaseModel):
    """Model representing enabled days for a schedule.

    Attributes:
        mon..sun: 1 when enabled, 0 otherwise.
    """

    mon: Optional[int] = Field(alias="mon", default=0)
    tue: Optional[int] = Field(alias="tue", default=0)
    wed: Optional[int] = Field(alias="wed", default=0)
    thu: Optional[int] = Field(alias="thu", default=0)
    fri: Optional[int] = Field(alias="fri", default=0)
    sat: Optional[int] = Field(alias="sat", default=0)
    sun: Optional[int] = Field(alias="sun", default=0)


class ChargingSchedule(CustomEndpointBaseModel):
    """Model representing a charging schedule returned by the API.

    Attributes:
        id: Schedule identifier
        enabled: Whether the schedule is enabled
        type: Type of schedule (startEnd, startOnly)
        start_time: Mandatory start time object
        end_time: Optional end time object
        days: Days object with enabled weekdays
    """

    id: int = Field(alias="id")
    enabled: bool = Field(alias="enabled")
    type: str = Field(alias="type")
    start_time: "ChargeTime" = Field(alias="startTime")
    end_time: Optional["ChargeTime"] = Field(alias="endTime", default=None)
    days: Days = Field(alias="days")

    @field_validator("days", mode="after")
    @classmethod
    def _validate_days(cls, v: Days) -> Days:
        if v is None:
            error_message = (
                "`days` must be present and contain at least one enabled day"
            )
            raise ValueError(error_message)

        if not any(
            bool(getattr(v, d, None))
            for d in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
        ):
            error_message = "At least one day must be enabled in `days`"
            raise ValueError(error_message)

        return v

    def _next_start(self, ref: datetime) -> Optional[datetime]:
        """Compute the next start datetime for this schedule after `ref`.

        Returns the earliest candidate datetime or None if no weekdays enabled.
        """
        names = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
        enabled_wd = [i for i, n in enumerate(names) if bool(getattr(self.days, n, 0))]
        if not enabled_wd:
            return None

        tz = ref.tzinfo

        def _candidate_for_weekday(wd: int) -> datetime:
            days_ahead = (wd - ref.weekday() + 7) % 7
            candidate_date = ref.date() + timedelta(days=days_ahead)
            candidate_dt = datetime.combine(
                candidate_date,
                time(self.start_time.hour, self.start_time.minute),
                tzinfo=tz,
            )
            if candidate_dt <= ref:
                candidate_dt += timedelta(days=7)
            return candidate_dt

        candidates = [_candidate_for_weekday(wd) for wd in enabled_wd]
        return min(candidates) if candidates else None

    def _end_and_duration(self, start_dt: datetime) -> tuple[Optional[datetime], Optional[timedelta]]:
        """Compute end datetime and duration given a start datetime.

        Returns (end_dt, duration) where either may be None.
        """
        if self.end_time is None:
            return None, None

        end_dt = datetime.combine(
            start_dt.date(),
            time(self.end_time.hour, self.end_time.minute),
            tzinfo=start_dt.tzinfo,
        )
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)
        return end_dt, end_dt - start_dt

    def next_occurrence(
        self, ref: Optional[datetime] = None
    ) -> Optional["ScheduledChargeWindow"]:
        """Return the next scheduled charge window for this schedule after `ref`.

        Returns a `ScheduledChargeWindow` containing start, optional end and duration.
        """
        if not self.enabled:
            return None

        ref = ref or datetime.now(timezone.utc).astimezone()

        start_dt = self._next_start(ref)
        if start_dt is None:
            return None

        end_dt, duration = self._end_and_duration(start_dt)

        return ScheduledChargeWindow(start=start_dt, end=end_dt, duration=duration)


@dataclass
class ScheduledChargeWindow:
    """Represents the next scheduled charge window.

    Attributes:
        start: Start timestamp of the scheduled charge (aware datetime).
        end: Optional end timestamp of the scheduled charge (aware datetime).
        duration: Optional duration (timedelta) if end is provided.
    """

    start: datetime
    end: Optional[datetime] = None
    duration: Optional[timedelta] = None


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
        chargeType: Type of charging schedule (startOnly, startEnd).
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


# Resolve forward references for Pydantic models that reference each other
ChargingSchedule.update_forward_refs()
ReservationCharge.update_forward_refs()
ElectricStatusModel.update_forward_refs()
