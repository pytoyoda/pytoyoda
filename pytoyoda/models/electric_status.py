"""Models for vehicle electric status."""

from datetime import datetime
from typing import TypeVar

from pydantic import computed_field

from pytoyoda.const import KILOMETERS_UNIT, MILES_UNIT
from pytoyoda.models.endpoints.electric import (
    ChargingSchedule,
    ElectricResponseModel,
    ElectricStatusModel,
    NextChargingEvent,
    ScheduledChargeWindow,
)
from pytoyoda.utils.conversions import convert_distance
from pytoyoda.utils.models import CustomAPIBaseModel, Distance

# Toyota's backend has been observed to return sentinel/placeholder values
# (e.g. 65535 / 0xFFFF, or close variants like 65335) for `remainingChargeTime`
# when the vehicle is not actively charging, instead of omitting the field.
# Anything beyond a full day of charging is not a plausible countdown, so we
# treat implausibly large values as "not reported" (None) rather than
# surfacing the raw sentinel to consumers.
MAX_PLAUSIBLE_REMAINING_CHARGE_TIME_MINUTES = 1440  # 24 hours

T = TypeVar(
    "T",
    bound=ElectricResponseModel | bool,
)


class ElectricStatus(CustomAPIBaseModel[type[T]]):
    """ElectricStatus."""

    def __init__(
        self,
        electric_status: ElectricResponseModel | None = None,
        metric: bool = True,  # noqa : FBT001, FBT002
        **kwargs: dict,
    ) -> None:
        """Initialise ElectricStatus model.

        Args:
            electric_status: Electric status model
            metric: Report distances in metric (or imperial)
            **kwargs: Additional keyword arguments passed to the parent class

        """
        # Create temporary object for data
        data = {
            "electric_status": electric_status,
            "metric": metric,
        }
        super().__init__(data=data, **kwargs)  # type: ignore[reportArgumentType, arg-type]

        # Get payload data from models
        self._electric_status: ElectricStatusModel | None = (
            electric_status.payload if electric_status else None
        )
        self._distance_unit: str = KILOMETERS_UNIT if metric else MILES_UNIT

    @computed_field  # type: ignore[prop-decorator]
    @property
    def battery_level(self) -> float | None:
        """Battery level of the vehicle.

        Returns:
            float: Battery level of the vehicle in percentage.

        """
        return self._electric_status.battery_level if self._electric_status else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def phev_usable_battery_level(self) -> float | None:
        """Usable battery level of a plug-in hybrid electric vehicle.

        This is separate from `battery_level` and may reflect only the
        portion of the battery usable for EV driving.

        Returns:
            float: Usable PHEV battery level in percentage, or None if not
                reported by the vehicle.

        """
        return (
            self._electric_status.phev_usable_battery_level
            if self._electric_status
            else None
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def charging_status(self) -> str | None:
        """Charging status of the vehicle.

        Returns:
            str: Charging status of the vehicle.

        """
        return self._electric_status.charging_status if self._electric_status else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def remaining_charge_time(self) -> int | None:
        """Remaining time to full charge in minutes.

        Returns:
            int: Remaining time to full charge in minutes.

        """
        if not self._electric_status:
            return None

        value = self._electric_status.remaining_charge_time
        if value is None:
            return None

        if (
            value > MAX_PLAUSIBLE_REMAINING_CHARGE_TIME_MINUTES
            and self.charging_status != "charging"
        ):
            # Toyota's backend has been observed to send a sentinel value
            # (e.g. 65535/65335) for this field when the vehicle is not
            # actively charging. If we're actively charging, trust the raw
            # value even if it's unusually high (e.g. a very slow/trickle
            # charge), since we have no other way to disambiguate a real
            # estimate from a sentinel in that case.
            return None

        return value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ev_range(self) -> float | None:
        """Electric vehicle range.

        Returns:
            float: Electric vehicle range in the current selected units.
        """
        if not self._electric_status:
            return None

        ev = self._electric_status.ev_range
        if ev is None:
            return None

        # Treat 0 as a valid value — only None means "missing"
        if ev.value is None or ev.unit is None:
            return None

        return convert_distance(
            self._distance_unit,
            ev.unit,
            ev.value,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ev_range_with_unit(self) -> Distance | None:
        """Electric vehicle range with unit.

        Returns:
            Distance: The range with current unit
        """
        value = self.ev_range
        if value is not None:
            # 0 is a perfectly valid value and must NOT be treated as "no EV range"
            return Distance(value=value, unit=self._distance_unit)
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ev_range_with_ac(self) -> float | None:
        """Electric vehicle range with AC.

        Returns:
            float: Electric vehicle range with AC in the
                current selected units.
        """
        if self._electric_status is None:
            return None

        if (ev_ac := self._electric_status.ev_range_with_ac) is None:
            return None

        # Only None means "missing"; 0.0 is valid
        if ev_ac.unit is None or ev_ac.value is None:
            return None

        return convert_distance(
            self._distance_unit,
            ev_ac.unit,
            ev_ac.value,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ev_range_with_ac_with_unit(self) -> Distance | None:
        """Electric vehicle range with AC with unit.

        Returns:
            Distance: The range with current unit.
        """
        value = self.ev_range_with_ac
        if value is not None:
            # 0 is a valid value; only None means "no data"
            return Distance(value=value, unit=self._distance_unit)
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def can_set_next_charging_event(self) -> bool | None:
        """Can set next charging event.

        Returns:
            bool: Can set next charging event.

        """
        return (
            self._electric_status.can_set_next_charging_event
            if self._electric_status
            else None
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def last_update_timestamp(self) -> datetime | None:
        """Last update timestamp.

        Returns:
            datetime: Last update timestamp.
        """
        return (
            self._electric_status.last_update_timestamp
            if self._electric_status
            else None
        )

    @computed_field
    @property
    def next_charging_event(self) -> NextChargingEvent | None:
        """Next scheduled charging event.

        Returns:
            NextChargingEvent: The current active next charging event

        """
        return (
            self._electric_status.next_charging_event if self._electric_status else None
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def charging_schedules(self) -> list[ChargingSchedule] | None:
        """Charging schedules returned by the API.

        Returns:
            list[ChargingSchedule]: List of charging schedules or None
        """
        return (
            self._electric_status.charging_schedules if self._electric_status else None
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_active_charging_schedule(self) -> bool:
        """Whether there is at least one active charging schedule.

        Returns:
            bool: True if there is at least one active charging schedule, False
              otherwise.
        """
        if self.charging_schedules is None:
            return False
        return any(schedule.enabled for schedule in self.charging_schedules)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def active_scheduled_charging(self) -> ScheduledChargeWindow | None:
        """Get the active scheduled charging event, if any.

        Returns:
            ScheduledChargeWindow: The active scheduled charging event, or None
              if there is none.
        """
        if not self.has_active_charging_schedule:
            return None

        now = datetime.now().astimezone()

        def _next_window_for_schedule(
            sched: ChargingSchedule,
        ) -> ScheduledChargeWindow | None:
            if not sched.enabled:
                return None
            try:
                return sched.next_occurrence(ref=now)
            except (ValueError, TypeError, AttributeError):
                return None

        windows = [
            w
            for s in (self.charging_schedules or [])
            for w in (_next_window_for_schedule(s),)
            if w
        ]
        if not windows:
            return None

        return min(windows, key=lambda w: w.start)
