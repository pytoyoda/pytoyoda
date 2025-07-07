"""Toyota Connected Services API - Location Models."""

# ruff: noqa: FA100

from datetime import datetime
from typing import Optional

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class _VehicleLocationModel(CustomEndpointBaseModel):
    """Model representing detailed vehicle location information.

    Attributes:
        display_name: Human-readable location name (e.g., street address)
        latitude: Geographic latitude coordinate
        longitude: Geographic longitude coordinate
        location_acquisition_datetime: When the location data was acquired
            from the vehicle

    """

    display_name: Optional[str] = Field(alias="displayName", default=None)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_acquisition_datetime: Optional[datetime] = Field(
        alias="locationAcquisitionDatetime", default=None
    )


class LocationModel(CustomEndpointBaseModel):
    """Model representing the location of a vehicle.

    Attributes:
        last_timestamp: When any location data was last updated
        vehicle_location: Detailed location information including coordinates
        vin: The Vehicle Identification Number of the vehicle

    """

    last_timestamp: Optional[datetime] = Field(alias="lastTimestamp", default=None)
    vehicle_location: Optional[_VehicleLocationModel] = Field(
        alias="vehicleLocation", default=None
    )
    vin: Optional[str] = None


class LocationResponseModel(StatusModel):
    """Model representing a location response from the API.

    Inherits from StatusModel.

    Attributes:
        payload: The location data if request was successful

    """

    payload: Optional[LocationModel] = None
