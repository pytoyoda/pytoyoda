"""Climate Status and Settings Models.

Public wrappers over the ``/v1/vehicle/climate-status`` and
``/v1/vehicle/climate-settings`` read endpoints.
"""

from datetime import datetime, timedelta

from pydantic import computed_field

from pytoyoda.models.endpoints.climate import (
    ClimateSettingsModel,
    ClimateSettingsResponseModel,
    ClimateStatusResponseModel,
    HeatingOptionsModel,
    SeatOptionsModel,
)
from pytoyoda.utils.models import CustomAPIBaseModel, Temperature

# Backend climate-status enum (RemoteClimateStatus$Status backendKeys). ``starting``
# and ``stopping`` are transitional; on/off is decided by intent, and an unrecognised
# value maps to None rather than being guessed.
_CLIMATE_ON_STATES = frozenset({"starting", "running"})
_CLIMATE_OFF_STATES = frozenset({"stopped", "stopping"})

# Simple on/off heating toggles (front defroster, rear defogger, steering heater).
_TOGGLE_ON_STATES = frozenset({"on"})
_TOGGLE_OFF_STATES = frozenset({"off"})


def _tristate(
    value: str | None,
    true_values: frozenset[str],
    false_values: frozenset[str],
) -> bool | None:
    """Map a backend enum string to a tri-state bool (case-insensitive).

    ``value`` in ``true_values`` -> True, in ``false_values`` -> False; ``None``, a
    non-string, or an unrecognised value -> None (never guessed).
    """
    if not isinstance(value, str):
        return None
    lowered = value.lower()
    if lowered in true_values:
        return True
    if lowered in false_values:
        return False
    return None


class HeatingOptions(CustomAPIBaseModel[HeatingOptionsModel]):
    """Defroster / defogger / steering-heater states."""

    def __init__(self, options: HeatingOptionsModel, **kwargs: dict) -> None:
        """Initialize heating options.

        Args:
            options (HeatingOptionsModel): The heating option states.
            **kwargs: Additional keyword arguments passed to the parent class.

        """
        super().__init__(data=options, **kwargs)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def front_defroster(self) -> bool | None:
        """Whether the front defroster is on."""
        return _tristate(
            self._data.front_defroster, _TOGGLE_ON_STATES, _TOGGLE_OFF_STATES
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def rear_defogger(self) -> bool | None:
        """Whether the rear defogger is on."""
        return _tristate(
            self._data.rear_defogger, _TOGGLE_ON_STATES, _TOGGLE_OFF_STATES
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def steering_heater(self) -> bool | None:
        """Whether the steering-wheel heater is on."""
        return _tristate(
            self._data.steering_heater, _TOGGLE_ON_STATES, _TOGGLE_OFF_STATES
        )


class SeatOptions(CustomAPIBaseModel[SeatOptionsModel]):
    """Per-seat heater levels.

    Values are the raw backend level strings (``"off"``/``"low"``/``"medium"``/
    ``"high"``) — kept as-is rather than coerced to bool because seat heaters are
    multi-level.
    """

    def __init__(self, options: SeatOptionsModel, **kwargs: dict) -> None:
        """Initialize seat options.

        Args:
            options (SeatOptionsModel): The per-seat heater levels.
            **kwargs: Additional keyword arguments passed to the parent class.

        """
        super().__init__(data=options, **kwargs)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def driver_seat(self) -> str | None:
        """Driver seat heater level."""
        return self._data.driver_seat

    @computed_field  # type: ignore[prop-decorator]
    @property
    def passenger_seat(self) -> str | None:
        """Front passenger seat heater level."""
        return self._data.passenger_seat

    @computed_field  # type: ignore[prop-decorator]
    @property
    def rear_driver_seat(self) -> str | None:
        """Rear driver-side seat heater level."""
        return self._data.rear_driver_seat

    @computed_field  # type: ignore[prop-decorator]
    @property
    def rear_passenger_seat(self) -> str | None:
        """Rear passenger-side seat heater level."""
        return self._data.rear_passenger_seat


class ClimateStatus(CustomAPIBaseModel[ClimateStatusResponseModel]):
    """Climate status."""

    def __init__(
        self, climate_status: ClimateStatusResponseModel, **kwargs: dict
    ) -> None:
        """Initialize climate status.

        Args:
            climate_status (ClimateStatusResponseModel): The climate-status response
                envelope; the typed payload is unwrapped here.
            **kwargs: Additional keyword arguments passed to the parent class.

        """
        super().__init__(data=climate_status, **kwargs)
        self._status = self._data.payload if self._data else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def status(self) -> str | None:
        """Raw backend state (``stopped``/``starting``/``stopping``/``running``)."""
        return self._status.status if self._status else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_on(self) -> bool | None:
        """Whether climate is engaged.

        ``starting``/``running`` -> True, ``stopped``/``stopping`` -> False, and an
        unknown or missing state -> None.
        """
        status = self._status.status if self._status else None
        return _tristate(status, _CLIMATE_ON_STATES, _CLIMATE_OFF_STATES)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def started_at(self) -> datetime | None:
        """When the current climate run started."""
        return self._status.started_at if self._status else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def updated_at(self) -> datetime | None:
        """When the backend last refreshed this state."""
        return self._status.updated_at if self._status else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def duration(self) -> timedelta | None:
        """Programmed run duration."""
        if self._status is None or self._status.duration is None:
            return None
        return timedelta(minutes=self._status.duration)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def current_temperature(self) -> Temperature | None:
        """Measured cabin temperature."""
        temp = self._status.current_temperature if self._status else None
        if temp is None:
            return None
        return Temperature(value=temp.value, unit=temp.unit)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def target_temperature(self) -> Temperature | None:
        """Target temperature."""
        temp = self._status.target_temperature if self._status else None
        if temp is None:
            return None
        return Temperature(value=temp.value, unit=temp.unit)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def heating_options(self) -> HeatingOptions | None:
        """Defroster / defogger / steering-heater states."""
        options = self._status.heating_options if self._status else None
        return HeatingOptions(options) if options is not None else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def seat_options(self) -> SeatOptions | None:
        """Per-seat heater levels."""
        options = self._status.seat_options if self._status else None
        return SeatOptions(options) if options is not None else None


class ClimateSettings(CustomAPIBaseModel[ClimateSettingsResponseModel]):
    """Climate settings."""

    def __init__(
        self, climate_settings: ClimateSettingsResponseModel, **kwargs: dict
    ) -> None:
        """Initialize climate settings.

        Args:
            climate_settings (ClimateSettingsResponseModel): The climate-settings
                response envelope; the typed payload is unwrapped here.
            **kwargs: Additional keyword arguments passed to the parent class.

        """
        super().__init__(data=climate_settings, **kwargs)
        self._settings: ClimateSettingsModel | None = (
            self._data.payload if self._data else None
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def temperature(self) -> Temperature | None:
        """Target temperature."""
        temp = self._settings.temperature if self._settings else None
        if temp is None:
            return None
        return Temperature(value=temp.value, unit=temp.unit)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def duration(self) -> timedelta | None:
        """Programmed run duration."""
        if self._settings is None or self._settings.duration is None:
            return None
        return timedelta(minutes=self._settings.duration)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def heating_options(self) -> HeatingOptions | None:
        """Defroster / defogger / steering-heater settings."""
        options = self._settings.heating_options if self._settings else None
        return HeatingOptions(options) if options is not None else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def seat_options(self) -> SeatOptions | None:
        """Per-seat heater level settings."""
        options = self._settings.seat_options if self._settings else None
        return SeatOptions(options) if options is not None else None

    # --- Deprecated back-compat accessors -----------------------------------
    # The new /v1/vehicle/climate-settings payload no longer carries these. They
    # are kept (returning None/[]) so external consumers of the old shape do not
    # break; new code should read temperature/duration/heating_options/seat_options.

    @computed_field  # type: ignore[prop-decorator]
    @property
    def settings_on(self) -> None:
        """Deprecated: removed from the new climate-settings payload."""
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def min_temp(self) -> None:
        """Deprecated: removed from the new climate-settings payload."""
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def max_temp(self) -> None:
        """Deprecated: removed from the new climate-settings payload."""
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def temp_interval(self) -> None:
        """Deprecated: removed from the new climate-settings payload."""
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def operations(self) -> list:
        """Deprecated: acOperations no longer exist in the new payload."""
        return []
