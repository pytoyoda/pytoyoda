"""Models for vehicle sensors."""

from __future__ import annotations

from datetime import datetime  # noqa : TC003
from typing import Optional

from pydantic import computed_field

from pytoyoda.models.endpoints.status import (
    ComponentStateModel,
    DoorModel,
    RemoteStatusModel,
    RemoteStatusResponseModel,
)
from pytoyoda.utils.models import CustomAPIBaseModel

_CLOSED_VALUES = frozenset({"close", "closed"})
_OPEN_VALUES = frozenset({"open"})
_LOCKED_VALUES = frozenset({"locked"})
_UNLOCKED_VALUES = frozenset({"unlocked"})


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


def _driver_on_left(status: RemoteStatusModel | None) -> bool:
    """Whether the driver sits on the left (LHD). Defaults to LHD when unknown."""
    if status is None or status.left_hand_drive is None:
        return True
    return status.left_hand_drive


def _rear_is_left(*, on_left: bool, driver_side: bool) -> bool:
    """Whether a driver/passenger rear position maps to the physical rear-left slot.

    The payload keys rear positions physically; the driver is on the left in an LHD
    car. Shared by ``Doors`` and ``Windows`` so this left/right mapping — the
    error-prone part — lives in one place.
    """
    return on_left if driver_side else not on_left


class Door(CustomAPIBaseModel[Optional[DoorModel]]):
    """Door/hood data model."""

    def __init__(
        self,
        status: DoorModel | None = None,
        **kwargs: dict,
    ) -> None:
        """Initialise Door Model."""
        super().__init__(
            data=status,
            **kwargs,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def closed(self) -> bool | None:
        """If the door is closed."""
        if self._data is None or self._data.open_status is None:
            return None
        return _tristate(self._data.open_status.status, _CLOSED_VALUES, _OPEN_VALUES)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def locked(self) -> bool | None:
        """If the door is locked."""
        if self._data is None or self._data.lock_status is None:
            return None
        return _tristate(
            self._data.lock_status.status, _LOCKED_VALUES, _UNLOCKED_VALUES
        )


class Window(CustomAPIBaseModel[Optional[ComponentStateModel]]):
    """Window data model."""

    def __init__(
        self,
        status: ComponentStateModel | None = None,
        **kwargs: dict,
    ) -> None:
        """Initialise Window Model."""
        super().__init__(
            data=status,
            **kwargs,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def closed(self) -> bool | None:
        """Window closed state."""
        if self._data is None:
            return None
        return _tristate(self._data.status, _CLOSED_VALUES, _OPEN_VALUES)


class Doors(CustomAPIBaseModel[Optional[RemoteStatusModel]]):
    """Trunk/doors/hood data model."""

    def __init__(
        self,
        status: RemoteStatusModel | None = None,
        **kwargs: dict,
    ) -> None:
        """Initialise Doors Model."""
        super().__init__(
            data=status,
            **kwargs,
        )

    def _rear(self, *, driver_side: bool) -> Door:
        """Resolve a rear door by driver/passenger side via left_hand_drive."""
        doors = self._data.doors if self._data else None
        if doors is None:
            return Door(None)
        left = _rear_is_left(
            on_left=_driver_on_left(self._data), driver_side=driver_side
        )
        return Door(doors.rear_left if left else doors.rear_right)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def driver_seat(self) -> Door | None:
        """Driver seat door."""
        doors = self._data.doors if self._data else None
        return Door(doors.driver if doors else None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def driver_rear_seat(self) -> Door | None:
        """Driver-side rear door."""
        return self._rear(driver_side=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def passenger_seat(self) -> Door | None:
        """Passenger seat door."""
        doors = self._data.doors if self._data else None
        return Door(doors.passenger if doors else None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def passenger_rear_seat(self) -> Door | None:
        """Passenger-side rear door."""
        return self._rear(driver_side=False)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def trunk(self) -> Door | None:
        """Trunk (rear hatch)."""
        doors = self._data.doors if self._data else None
        return Door(doors.rear_back if doors else None)


class Windows(CustomAPIBaseModel[Optional[RemoteStatusModel]]):
    """Windows data model."""

    def __init__(
        self,
        status: RemoteStatusModel | None = None,
        **kwargs: dict,
    ) -> None:
        """Initialise Windows Model."""
        super().__init__(
            data=status,
            **kwargs,
        )

    def _rear(self, *, driver_side: bool) -> Window:
        """Resolve a rear window by driver/passenger side via left_hand_drive."""
        windows = self._data.windows if self._data else None
        if windows is None:
            return Window(None)
        left = _rear_is_left(
            on_left=_driver_on_left(self._data), driver_side=driver_side
        )
        return Window(windows.rear_left if left else windows.rear_right)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def driver_seat(self) -> Window | None:
        """Driver seat window."""
        windows = self._data.windows if self._data else None
        return Window(windows.driver if windows else None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def driver_rear_seat(self) -> Window | None:
        """Driver-side rear window."""
        return self._rear(driver_side=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def passenger_seat(self) -> Window | None:
        """Passenger seat window."""
        windows = self._data.windows if self._data else None
        return Window(windows.passenger if windows else None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def passenger_rear_seat(self) -> Window | None:
        """Passenger-side rear window."""
        return self._rear(driver_side=False)


class LockStatus(CustomAPIBaseModel[Optional[RemoteStatusResponseModel]]):
    """Vehicle lock status data model."""

    def __init__(
        self,
        status: RemoteStatusResponseModel | None = None,
        **kwargs: dict,
    ) -> None:
        """Initialise LockStatus."""
        super().__init__(
            data=status,
            **kwargs,
        )
        self._status: RemoteStatusModel | None = (
            self._data.payload if self._data else None
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def last_updated(self) -> datetime | None:
        """Last time data was received from the car."""
        return None if self._status is None else self._status.occurrence_date

    @computed_field  # type: ignore[prop-decorator]
    @property
    def doors(self) -> Doors | None:
        """Doors."""
        return None if self._status is None else Doors(self._status)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def windows(self) -> Windows | None:
        """Windows."""
        return None if self._status is None else Windows(self._status)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def hood(self) -> Door | None:
        """Hood."""
        if self._status is None:
            return None
        doors = self._status.doors
        return Door(doors.hood if doors else None)
