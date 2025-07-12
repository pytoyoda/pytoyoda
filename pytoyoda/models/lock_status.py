"""Models for vehicle sensors."""

from __future__ import annotations

from datetime import datetime  # noqa : TC003
from typing import Optional

from pydantic import computed_field

from pytoyoda.models.endpoints.status import (
    RemoteStatusModel,
    RemoteStatusResponseModel,
    SectionModel,
    VehicleStatusModel,
)
from pytoyoda.utils.models import CustomAPIBaseModel


class StatusHelper:
    """Helper class for status operations."""

    @staticmethod
    def get_category(
        data: RemoteStatusModel | None, category: str
    ) -> VehicleStatusModel | None:
        """Search for a category in Vehicle Status."""
        if data and data.vehicle_status:
            return next(
                (item for item in data.vehicle_status if item.category == category),
                None,
            )
        return None

    @staticmethod
    def get_section(
        data: VehicleStatusModel | None, section: str
    ) -> SectionModel | None:
        """Search for a section in the category."""
        if data and data.sections:
            return next(
                (item for item in data.sections if item.section == section),
                None,
            )
        return None

    @staticmethod
    def get_status(data: SectionModel | None, status: str) -> bool | None:
        """Determine the status of a value in the section."""
        if data and data.values:
            item_status = next(
                (item.status for item in data.values if item.value == status),
                None,
            )
            return item_status if item_status is None else not bool(item_status)
        return None

    @classmethod
    def get_component_section(
        cls, status: RemoteStatusModel | None, category: str, section: str
    ) -> SectionModel | None:
        """Retrieve component section from a given category."""
        category_data = cls.get_category(status, category=category)
        return cls.get_section(category_data, section=section)


class Door(CustomAPIBaseModel[Optional[SectionModel]]):
    """Door/hood data model."""

    def __init__(
        self,
        status: SectionModel | None = None,
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
        return StatusHelper.get_status(self._data, status="carstatus_closed")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def locked(self) -> bool | None:
        """If the door is locked."""
        if StatusHelper.get_status(self._data, status="carstatus_locked") is True:
            return True
        if StatusHelper.get_status(self._data, status="carstatus_unlocked") is False:
            return False
        return None


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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def driver_seat(self) -> Door | None:
        """Driver seat door."""
        section = StatusHelper.get_component_section(
            self._data,
            category="carstatus_category_driver",
            section="carstatus_item_driver_door",
        )
        return Door(section)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def driver_rear_seat(self) -> Door | None:
        """Right rearseat door."""
        section = StatusHelper.get_component_section(
            self._data,
            category="carstatus_category_driver",
            section="carstatus_item_driver_rear_door",
        )
        return Door(section)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def passenger_seat(self) -> Door | None:
        """Passenger seat door."""
        section = StatusHelper.get_component_section(
            self._data,
            category="carstatus_category_passenger",
            section="carstatus_item_passenger_door",
        )
        return Door(section)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def passenger_rear_seat(self) -> Door | None:
        """Left rearseat door."""
        section = StatusHelper.get_component_section(
            self._data,
            category="carstatus_category_passenger",
            section="carstatus_item_passenger_rear_door",
        )
        return Door(section)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def trunk(self) -> Door | None:
        """Trunk."""
        section = StatusHelper.get_component_section(
            self._data,
            category="carstatus_category_other",
            section="carstatus_item_rear_hatch",
        )
        return Door(section)


class Window(CustomAPIBaseModel[Optional[SectionModel]]):
    """Window data model."""

    def __init__(
        self,
        status: SectionModel | None = None,
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
        return StatusHelper.get_status(self._data, status="carstatus_closed")


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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def driver_seat(self) -> Window | None:
        """Driver seat window."""
        section = StatusHelper.get_component_section(
            self._data,
            category="carstatus_category_driver",
            section="carstatus_item_driver_window",
        )
        return Window(section)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def driver_rear_seat(self) -> Window | None:
        """Right rearseat window."""
        section = StatusHelper.get_component_section(
            self._data,
            category="carstatus_category_driver",
            section="carstatus_item_driver_rear_window",
        )
        return Window(section)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def passenger_seat(self) -> Window | None:
        """Passenger seat window."""
        section = StatusHelper.get_component_section(
            self._data,
            category="carstatus_category_passenger",
            section="carstatus_item_passenger_window",
        )
        return Window(section)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def passenger_rear_seat(self) -> Window | None:
        """Left rearseat window."""
        section = StatusHelper.get_component_section(
            self._data,
            category="carstatus_category_passenger",
            section="carstatus_item_passenger_rear_window",
        )
        return Window(section)


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
        """Last time data was recieved from the car."""
        return self._status if self._status is None else self._status.occurrence_date

    @computed_field  # type: ignore[prop-decorator]
    @property
    def doors(self) -> Doors | None:
        """Doors."""
        return self._status if self._status is None else Doors(self._status)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def windows(self) -> Windows | None:
        """Windows."""
        return self._status if self._status is None else Windows(self._status)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def hood(self) -> Door | None:
        """Hood."""
        if self._status is None:
            return None
        section = StatusHelper.get_component_section(
            self._status,
            category="carstatus_category_other",
            section="carstatus_item_hood",
        )
        return Door(section)
