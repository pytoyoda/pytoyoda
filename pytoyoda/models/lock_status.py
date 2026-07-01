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

_CLOSED_VALUES = {"close", "closed"}
_OPEN_VALUES = {"open"}


def _is_closed(status: str | None) -> bool | None:
    """Interpret an open-state string: closed=True, open=False, unknown=None."""
    if status is None:
        return None
    lowered = status.lower()
    if lowered in _CLOSED_VALUES:
        return True
    if lowered in _OPEN_VALUES:
        return False
    return None


def _is_locked(status: str | None) -> bool | None:
    """Interpret a lock-state string: locked=True, unlocked=False, unknown=None."""
    if status is None:
        return None
    lowered = status.lower()
    if lowered == "locked":
        return True
    if lowered == "unlocked":
        return False
    return None


def _driver_on_left(status: RemoteStatusModel | None) -> bool:
    """Whether the driver sits on the left (LHD). Defaults to LHD when unknown."""
    if status is None or status.left_hand_drive is None:
        return True
    return status.left_hand_drive


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
        return _is_closed(self._data.open_status.status)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def locked(self) -> bool | None:
        """If the door is locked."""
        if self._data is None or self._data.lock_status is None:
            return None
        return _is_locked(self._data.lock_status.status)


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
        return None if self._data is None else _is_closed(self._data.status)


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
        """Resolve a rear door by driver/passenger side via left_hand_drive.

        The payload keys rear doors physically (rearLeft/rearRight); the driver
        is on the left in an LHD car.
        """
        doors = self._data.doors if self._data else None
        if doors is None:
            return Door(None)
        on_left = _driver_on_left(self._data)
        if driver_side:
            return Door(doors.rear_left if on_left else doors.rear_right)
        return Door(doors.rear_right if on_left else doors.rear_left)

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
        windows = self._data.windows if self._data else None
        if windows is None:
            return Window(None)
        on_left = _driver_on_left(self._data)
        if driver_side:
            return Window(windows.rear_left if on_left else windows.rear_right)
        return Window(windows.rear_right if on_left else windows.rear_left)

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
