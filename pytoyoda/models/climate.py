"""Climate Settings Models."""

# ruff: noqa: FA100

from datetime import datetime, timedelta
from typing import Optional

from pydantic import computed_field

from pytoyoda.models.endpoints.climate import (
    ACOperations,
    ACParameters,
    ClimateOptions,
    ClimateSettingsModel,
    ClimateSettingsResponseModel,
    ClimateStatusModel,
)
from pytoyoda.utils.models import CustomAPIBaseModel, Temperature


class ClimateOptionStatus(CustomAPIBaseModel[ClimateOptions]):
    """Climate option status."""

    def __init__(self, options: ClimateOptions, **kwargs: dict) -> None:
        """Initialize climate option status.

        Args:
            options (ClimateOptions): Contains all additional options for climate
            **kwargs: Additional keyword arguments passed to the parent class

        """
        super().__init__(data=options, **kwargs)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def front_defogger(self) -> bool:
        """The front defogger status.

        Returns:
            bool: The status of front defogger

        """
        return self._data.front_defogger

    @computed_field  # type: ignore[prop-decorator]
    @property
    def rear_defogger(self) -> bool:
        """The rear defogger status.

        Returns:
            bool: The status of rear defogger

        """
        return self._data.rear_defogger


class ClimateStatus(CustomAPIBaseModel[ClimateStatusModel]):
    """Climate status."""

    def __init__(self, climate_status: ClimateStatusModel, **kwargs: dict) -> None:
        """Initialize climate status.

        Args:
            climate_status (ClimateStatusModel): Contains all information
              regarding the climate status
            **kwargs: Additional keyword arguments passed to the parent class

        """
        super().__init__(data=climate_status, **kwargs)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def type(self) -> Optional[str]:
        """The type.

        Returns:
            Optional[str]: The type, or None if unavailable

        """
        return self._data.type if self._data else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def status(self) -> bool:
        """The status.

        Returns:
            bool: The status

        """
        return self._data.status

    @computed_field  # type: ignore[prop-decorator]
    @property
    def start_time(self) -> Optional[datetime]:
        """Start time.

        Returns:
            datetime: Start time

        """
        return self._data.started_at

    @computed_field  # type: ignore[prop-decorator]
    @property
    def duration(self) -> Optional[timedelta]:
        """The duration.

        Returns:
            timedelta: The duration

        """
        if self._data.duration is None:
            return None

        return timedelta(seconds=self._data.duration)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def current_temperature(self) -> Optional[Temperature]:
        """The current temperature.

        Returns:
            Temperature: The current temperature with unit

        """
        if self._data.current_temperature is None:
            return None

        return Temperature(
            value=self._data.current_temperature.value,
            unit=self._data.current_temperature.unit,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def target_temperature(self) -> Optional[Temperature]:
        """The target temperature.

        Returns:
            Temperature: The target temperature with unit

        """
        if self._data.target_temperature is None:
            return None

        return Temperature(
            value=self._data.target_temperature.value,
            unit=self._data.target_temperature.unit,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def options(self) -> Optional[ClimateOptionStatus]:
        """The status of climate options.

        Returns:
            ClimateOptionsStatus: The statuses of climate options

        """
        if self._data.options is None:
            return None

        return ClimateOptionStatus(options=self._data.options)


class ClimateSettingsParameter(CustomAPIBaseModel[ACParameters]):
    """Climate settings parameter."""

    def __init__(self, parameter: ACParameters, **kwargs: dict) -> None:
        """Initialize climate settings parameter.

        Args:
            parameter (ACParameters): Contains all parameters
            **kwargs: Additional keyword arguments passed to the parent class

        """
        super().__init__(data=parameter, **kwargs)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def available(self) -> Optional[bool]:
        """The parameter availability.

        Returns:
            bool: The parameter availability value

        """
        return self._data.available

    @computed_field  # type: ignore[prop-decorator]
    @property
    def enabled(self) -> bool:
        """The parameter enable.

        Returns:
            bool: The parameter enable value

        """
        return self._data.enabled

    @computed_field  # type: ignore[prop-decorator]
    @property
    def display_name(self) -> Optional[str]:
        """The parameter display name.

        Returns:
            str: The parameter display name

        """
        return self._data.display_name

    @computed_field  # type: ignore[prop-decorator]
    @property
    def name(self) -> str:
        """The parameter name.

        Returns:
            str: The parameter name

        """
        return self._data.name

    @computed_field  # type: ignore[prop-decorator]
    @property
    def icon_url(self) -> Optional[str]:
        """The parameter icon url.

        Returns:
            str: The parameter icon url

        """
        return self._data.icon_url


class ClimateSettingsOperation(CustomAPIBaseModel[ACOperations]):
    """Climate settings operation."""

    def __init__(self, operations: ACOperations, **kwargs: dict) -> None:
        """Initialize climate settings operation.

        Args:
            operations (ACOperations): Contains all options for climate
            **kwargs: Additional keyword arguments passed to the parent class

        """
        super().__init__(data=operations, **kwargs)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def available(self) -> Optional[bool]:
        """The operation availability.

        Returns:
            bool: The operation availability value

        """
        return self._data.available

    @computed_field  # type: ignore[prop-decorator]
    @property
    def category_name(self) -> str:
        """The operation category name.

        Returns:
            str: The operation category name

        """
        return self._data.category_name

    @computed_field  # type: ignore[prop-decorator]
    @property
    def category_display_name(self) -> Optional[str]:
        """The operation category display name.

        Returns:
            str: The operation category display name

        """
        return self._data.category_display_name

    @computed_field  # type: ignore[prop-decorator]
    @property
    def parameters(self) -> Optional[list[ClimateSettingsParameter]]:
        """The operation parameter.

        Returns:
            list[ClimateSettingsParameter]: The operation parameter

        """
        if self._data.ac_parameters is None:
            return None

        return [ClimateSettingsParameter(parameter=p) for p in self._data.ac_parameters]


class ClimateSettings(CustomAPIBaseModel[ClimateSettingsResponseModel]):
    """Climate settings."""

    def __init__(
        self, climate_settings: ClimateSettingsResponseModel, **kwargs: dict
    ) -> None:
        """Initialize climate settings.

        Args:
            climate_settings (ClimateSettingsResponseModel): Contains all information
                regarding the climate settings
            **kwargs: Additional keyword arguments passed to the parent class

        """
        super().__init__(data=climate_settings, **kwargs)
        self._climate_settings: Optional[ClimateSettingsModel] = (
            self._data.payload if self._data else None
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def settings_on(self) -> Optional[bool]:
        """The settings on value.

        Returns:
            bool: The value of settings on

        """
        return self._climate_settings.settings_on if self._climate_settings else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def temp_interval(self) -> Optional[float]:
        """The temperature interval.

        Returns:
            float: The value of temperature interval

        """
        return self._climate_settings.temp_interval if self._climate_settings else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def min_temp(self) -> Optional[float]:
        """The min temperature.

        Returns:
            float: The value of min temperature

        """
        return self._climate_settings.min_temp if self._climate_settings else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def max_temp(self) -> Optional[float]:
        """The max temperature.

        Returns:
            float: The value of max temperature

        """
        return self._climate_settings.max_temp if self._climate_settings else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def temperature(self) -> Optional[Temperature]:
        """The temperature.

        Returns:
            Temperature: The temperature with unit

        """
        if self._climate_settings:
            return Temperature(
                value=self._climate_settings.temperature,
                unit=self._climate_settings.temperature_unit,
            )
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def operations(self) -> Optional[list[ClimateSettingsOperation]]:
        """The climate operation settings.

        Returns:
            list[ClimateSettingsOperation]: The settings of climate operation

        """
        if (
            self._climate_settings is None
            or self._climate_settings.ac_operations is None
        ):
            return None

        return [
            ClimateSettingsOperation(operations=p)
            for p in self._climate_settings.ac_operations
        ]
