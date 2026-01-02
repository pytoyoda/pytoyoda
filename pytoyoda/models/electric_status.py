"""Models for vehicle electric status."""

# ruff: noqa: FA100

from datetime import datetime
from typing import Optional, TypeVar, Union

from pydantic import computed_field

from pytoyoda.const import KILOMETERS_UNIT, MILES_UNIT
from pytoyoda.models.endpoints.electric import (
    ElectricResponseModel,
    ElectricStatusModel,
    NextChargingEvent,
)
from pytoyoda.utils.conversions import convert_distance
from pytoyoda.utils.models import CustomAPIBaseModel, Distance

T = TypeVar(
    "T",
    bound=Union[ElectricResponseModel, bool],
)


class ElectricStatus(CustomAPIBaseModel[type[T]]):
    """ElectricStatus."""

    def __init__(
        self,
        electric_status: Optional[ElectricResponseModel] = None,
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
        self._electric_status: Optional[ElectricStatusModel] = (
            electric_status.payload if electric_status else None
        )
        self._distance_unit: str = KILOMETERS_UNIT if metric else MILES_UNIT

    @computed_field  # type: ignore[prop-decorator]
    @property
    def battery_level(self) -> Optional[float]:
        """Battery level of the vehicle.

        Returns:
            float: Battery level of the vehicle in percentage.

        """
        return self._electric_status.battery_level if self._electric_status else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def charging_status(self) -> Optional[str]:
        """Charging status of the vehicle.

        Returns:
            str: Charging status of the vehicle.

        """
        return self._electric_status.charging_status if self._electric_status else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def remaining_charge_time(self) -> Optional[int]:
        """Remaining time to full charge in minutes.

        Returns:
            int: Remaining time to full charge in minutes.

        """
        return (
            self._electric_status.remaining_charge_time
            if self._electric_status
            else None
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ev_range(self) -> Optional[float]:
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
    def ev_range_with_unit(self) -> Optional[Distance]:
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
    def ev_range_with_ac(self) -> Optional[float]:
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
    def ev_range_with_ac_with_unit(self) -> Optional[Distance]:
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
    def can_set_next_charging_event(self) -> Optional[bool]:
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
    def last_update_timestamp(self) -> Optional[datetime]:
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
    def next_charging_event(self) -> Optional[NextChargingEvent]:
        """Next scheduled charging event.

        Returns:
            NextChargingEvent: The current active next charging event

        """
        return (
            self._electric_status.next_charging_event if self._electric_status else None
        )
