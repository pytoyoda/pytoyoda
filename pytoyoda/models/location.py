"""Models for vehicle location."""

# ruff: noqa: FA100

from datetime import datetime
from typing import Optional

from pydantic import computed_field

from pytoyoda.models.endpoints.location import (
    LocationResponseModel,
    _VehicleLocationModel,
)
from pytoyoda.utils.models import CustomAPIBaseModel


class Location(CustomAPIBaseModel[LocationResponseModel]):
    """Latest Location of car."""

    def __init__(self, location: LocationResponseModel, **kwargs: dict) -> None:
        """Initialize Location model.

        Args:
            location (LocationResponseModel): Contains information about
                vehicle location
            **kwargs: Additional keyword arguments passed to the parent class

        """
        super().__init__(
            data=location,
            **kwargs,
        )
        self._location: Optional[_VehicleLocationModel] = (
            self._data.payload.vehicle_location
            if self._data and self._data.payload
            else None
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def latitude(self) -> Optional[float]:
        """Latitude.

        Returns:
            float: Latest latitude or None. _Not always available_.

        """
        return self._location.latitude if self._location else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def longitude(self) -> Optional[float]:
        """Longitude.

        Returns:
            float: Latest longitude or None. _Not always available_.

        """
        return self._location.longitude if self._location else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def timestamp(self) -> Optional[datetime]:
        """Timestamp.

        Returns:
            datetime: Position aquired timestamp or None.
                _Not always available_.

        """
        return self._location.location_acquisition_datetime if self._location else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def state(self) -> Optional[str]:
        """State.

        Returns:
            str: The state of the position or None. _Not always available_.

        """
        return self._location.display_name if self._location else None
