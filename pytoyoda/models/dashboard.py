"""Models for vehicle sensors."""

# ruff: noqa: FA100

from datetime import timedelta
from typing import Any, Optional, TypeVar, Union

from pydantic import computed_field

from pytoyoda.const import KILOMETERS_UNIT, MILES_UNIT
from pytoyoda.models.endpoints.electric import (
    ElectricResponseModel,
    ElectricStatusModel,
)
from pytoyoda.models.endpoints.telemetry import TelemetryModel, TelemetryResponseModel
from pytoyoda.models.endpoints.vehicle_health import (
    VehicleHealthModel,
    VehicleHealthResponseModel,
)
from pytoyoda.utils.conversions import convert_distance
from pytoyoda.utils.models import CustomAPIBaseModel, Distance

T = TypeVar(
    "T",
    bound=Union[
        TelemetryResponseModel, ElectricResponseModel, VehicleHealthResponseModel, bool
    ],
)


class Dashboard(CustomAPIBaseModel[type[T]]):
    """Information that may be found on a vehicles dashboard."""

    def __init__(
        self,
        telemetry: Optional[TelemetryResponseModel] = None,
        electric: Optional[ElectricResponseModel] = None,
        health: Optional[VehicleHealthResponseModel] = None,
        metric: bool = True,  # noqa : FBT001, FBT002
        **kwargs: dict,
    ) -> None:
        """Initialise Dashboard model.

        Args:
            telemetry (Optional[TelemetryResponseModel]): Telemetry response model
            electric (Optional[ElectricResponseModel]): Electric response model
            health (Optional[VehicleHealthResponseModel]): Vehicle health response model
            metric (bool): Report distances in metric(or imperial)
            **kwargs: Additional keyword arguments passed to the parent class

        """
        # Create temporary object for data
        data = {
            "telemetry": telemetry,
            "electric": electric,
            "health": health,
            "metric": metric,
        }
        super().__init__(data=data, **kwargs)  # type: ignore[reportArgumentType, arg-type]

        self._electric: Optional[ElectricStatusModel] = (
            electric.payload if electric else None
        )
        self._telemetry: Optional[TelemetryModel] = (
            telemetry.payload if telemetry else None
        )
        self._health: Optional[VehicleHealthModel] = health.payload if health else None
        self._distance_unit: str = KILOMETERS_UNIT if metric else MILES_UNIT

    @computed_field  # type: ignore[prop-decorator]
    @property
    def odometer(self) -> Optional[float]:
        """Odometer distance.

        Returns:
            float: The latest odometer reading in the current selected units
        """
        if self._telemetry is None:
            return None

        odometer = self._telemetry.odometer
        if odometer is None or odometer.unit is None or odometer.value is None:
            return None

        return convert_distance(
            self._distance_unit,
            odometer.unit,
            odometer.value,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def odometer_with_unit(self) -> Optional[Distance]:
        """Odometer distance with unit.

        Returns:
            Distance: The latest odometer reading with unit
        """
        value = self.odometer
        if value is not None:
            return Distance(value=value, unit=self._distance_unit)
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def fuel_level(self) -> Optional[int]:
        """Fuel level.

        Returns:
            int: A value as percentage

        """
        return self._telemetry.fuel_level if self._telemetry else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def battery_level(self) -> Optional[float]:
        """Shows the battery level if available.

        Returns:
            float: A value as percentage
        """
        if self._electric is not None and self._electric.battery_level is not None:
            return self._electric.battery_level

        if self._telemetry is not None and self._telemetry.battery_level is not None:
            return self._telemetry.battery_level

        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def fuel_range(self) -> Optional[float]:
        """The range using _only_ fuel.

        Returns:
            float: The range in the currently selected unit.
                If vehicle is electric returns 0
                If vehicle doesn't support fuel range returns None
        """
        if self._electric is not None and self._electric.fuel_range is not None:
            fuel_range = self._electric.fuel_range

            if fuel_range.unit is not None and fuel_range.value is not None:
                return convert_distance(
                    self._distance_unit,
                    fuel_range.unit,
                    fuel_range.value,
                )

        if (
            self._telemetry is not None
            and self._telemetry.distance_to_empty is not None
            and self._telemetry.distance_to_empty.unit is not None
            and self._telemetry.distance_to_empty.value is not None
            and self._telemetry.battery_level is None  # fuel-only vehicles only
        ):
            dte = self._telemetry.distance_to_empty
            return convert_distance(
                self._distance_unit,
                dte.unit,
                dte.value,
            )

        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def fuel_range_with_unit(self) -> Optional[Distance]:
        """The range using _only_ fuel with unit.

        Returns:
            Distance: The range with current unit
        """
        value = self.fuel_range
        if value is not None:
            return Distance(value=value, unit=self._distance_unit)
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def battery_range(self) -> Optional[float]:
        """The range using _only_ EV.

        Returns:
            float: The range in the currently selected unit.
                If vehicle is fuel only returns None
                If vehicle doesn't support battery range returns None
        """
        # Prefer explicit EV range from the electric endpoint
        if self._electric is not None and self._electric.ev_range is not None:
            ev_range = self._electric.ev_range

            if ev_range.unit is not None and ev_range.value is not None:
                return convert_distance(
                    self._distance_unit,
                    ev_range.unit,
                    ev_range.value,
                )

        # Fallback to telemetry when EV info is missing
        if (
            self._telemetry is not None
            and self._telemetry.battery_level is not None
            and self._telemetry.distance_to_empty is not None
            and self._telemetry.distance_to_empty.unit is not None
            and self._telemetry.distance_to_empty.value is not None
        ):
            dte = self._telemetry.distance_to_empty
            return convert_distance(
                self._distance_unit,
                dte.unit,
                dte.value,
            )

        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def battery_range_with_unit(self) -> Optional[Distance]:
        """The range using _only_ EV with unit.

        Returns:
            Distance: The range with current unit
        """
        value = self.battery_range
        if value is not None:
            return Distance(value=value, unit=self._distance_unit)
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def battery_range_with_ac(self) -> Optional[float]:
        """The range using _only_ EV when using AC.

        Returns:
            float: The range in the currently selected unit.
                If vehicle is fuel only returns 0
                If vehicle doesn't support battery range returns 0
        """
        if self._electric is None or self._electric.ev_range_with_ac is None:
            return None

        ev_ac = self._electric.ev_range_with_ac
        if ev_ac.unit is None or ev_ac.value is None:
            return None

        return convert_distance(
            self._distance_unit,
            ev_ac.unit,
            ev_ac.value,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def battery_range_with_ac_with_unit(self) -> Optional[Distance]:
        """The range using _only_ EV when using AC with unit.

        Returns:
            Distance: The range with current unit
        """
        value = self.battery_range_with_ac
        if value is not None:
            return Distance(value=value, unit=self._distance_unit)
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def range(self) -> Optional[float]:
        """The range using all available fuel & EV.

        Returns:
            float: The range in the currently selected unit.
                fuel only == fuel_range
                ev only == battery_range_with_ac
                hybrid == fuel_range + battery_range_with_ac
                None if not supported
        """
        if (
            self._telemetry is not None
            and self._telemetry.distance_to_empty is not None
            and self._telemetry.distance_to_empty.unit is not None
            and self._telemetry.distance_to_empty.value is not None
        ):
            dte = self._telemetry.distance_to_empty
            return convert_distance(
                self._distance_unit,
                dte.unit,
                dte.value,
            )

        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def range_with_unit(self) -> Optional[Distance]:
        """The range using all available fuel & EV with unit.

        Returns:
            Distance: The range with current unit
        """
        value = self.range
        if value is not None:
            return Distance(value=value, unit=self._distance_unit)
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def charging_status(self) -> Optional[str]:
        """Current charging status.

        Returns:
            str: A string containing the charging status as reported
                by the vehicle. None if vehicle doesn't support charging

        """
        return self._electric.charging_status if self._electric else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def remaining_charge_time(self) -> Optional[timedelta]:
        """Time left until charge is complete.

        Returns:
            timedelta: The amount of time left
                None if vehicle is not currently charging.
                None if vehicle doesn't support charging
        """
        if self._electric is None:
            return None

        if (rct := self._electric.remaining_charge_time) is None:
            return None

        # 0 minutes is a valid value (e.g. "finishing up now")
        return timedelta(minutes=rct)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def warning_lights(self) -> Optional[list[Any]]:
        """Dashboard Warning Lights.

        Returns:
            list[Any]: List of latest dashboard warning lights
                _Note_ Not fully understood

        """
        return self._health.warning if self._health else None
