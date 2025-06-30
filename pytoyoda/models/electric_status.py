"""Models for vehicle electric status."""

# ruff: noqa: FA100

from datetime import date
from typing import Optional, TypeVar, Union

from pydantic import computed_field

from pytoyoda.const import KILOMETERS_UNIT, MILES_UNIT
from pytoyoda.models.endpoints.electric import (
    ElectricResponseModel,
    ElectricStatusModel,
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
        if (
            self._electric_status
            and self._electric_status.ev_range
            and (
                self._electric_status.ev_range.unit
                and self._electric_status.ev_range.value
            )
        ):
            return convert_distance(
                self._distance_unit,
                self._electric_status.ev_range.unit,
                self._electric_status.ev_range.value,
            )
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ev_range_with_unit(self) -> Optional[Distance]:
        """Electric vehicle range with unit.

        Returns:
            Distance: The range with current unit

        """
        if value := self.ev_range:
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
        if (
            self._electric_status
            and self._electric_status.ev_range_with_ac
            and (
                self._electric_status.ev_range_with_ac.unit
                and self._electric_status.ev_range_with_ac.value
            )
        ):
            return convert_distance(
                self._distance_unit,
                self._electric_status.ev_range_with_ac.unit,
                self._electric_status.ev_range_with_ac.value,
            )
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ev_range_with_ac_with_unit(self) -> Optional[Distance]:
        """Electric vehicle range with ac with unit.

        Returns:
            Distance: The range with current unit

        """
        if value := self.ev_range_with_ac:
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
    def last_update_timestamp(self) -> Optional[date]:
        """Last update timestamp.

        Returns:
            date: Last update timestamp.

        """
        return (
            self._electric_status.last_update_timestamp
            if self._electric_status
            else None
        )
