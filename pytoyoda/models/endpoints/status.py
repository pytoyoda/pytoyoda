"""Toyota Connected Services API - Status Models."""

# ruff: noqa: FA100

from datetime import datetime
from typing import Optional

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel, UnitValueModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class _ValueStatusModel(CustomEndpointBaseModel):
    value: Optional[str]
    status: Optional[int]


class SectionModel(CustomEndpointBaseModel):
    """Model representing the status category of a vehicle.

    Attributes:
        section (str): The section of a vehicle status category.
        values (list[_ValueStatusModel]): A list of values corresponding
            status informations.

    """

    section: Optional[str]
    values: Optional[list[_ValueStatusModel]]


class VehicleStatusModel(CustomEndpointBaseModel):
    """Model representing the status category of a vehicle.

    Attributes:
        category (str): The status category of the vehicle.
        display_order (int): The order in which the status category is displayed
            inside the MyToyota App.
        sections (list[SectionModel]): The different sections belonging to the category.

    """

    category: Optional[str]
    display_order: Optional[int] = Field(alias="displayOrder")
    sections: Optional[list[SectionModel]]


class _TelemetryModel(CustomEndpointBaseModel):
    fugage: Optional[UnitValueModel] = None
    rage: Optional[UnitValueModel] = None
    odo: Optional[UnitValueModel]


class RemoteStatusModel(CustomEndpointBaseModel):
    """Model representing the remote status of a vehicle.

    Attributes:
        vehicle_status (list[_VehicleStatusModel]): The status of the vehicle.
        telemetry (_TelemetryModel): The telemetry data of the vehicle.
        occurrence_date (datetime): The date of the occurrence.
        caution_overall_count (int): The overall count of cautions.
        latitude (float): The latitude of the vehicle's location.
        longitude (float): The longitude of the vehicle's location.
        location_acquisition_datetime (datetime): The datetime of location acquisition.

    """

    vehicle_status: Optional[list[VehicleStatusModel]] = Field(alias="vehicleStatus")
    telemetry: Optional[_TelemetryModel]
    occurrence_date: Optional[datetime] = Field(alias="occurrenceDate")
    caution_overall_count: Optional[int] = Field(alias="cautionOverallCount")
    latitude: Optional[float]
    longitude: Optional[float]
    location_acquisition_datetime: Optional[datetime] = Field(
        alias="locationAcquisitionDatetime"
    )


class RemoteStatusResponseModel(StatusModel):
    r"""Model representing a remote status response.

    Inherits from StatusModel.

    Attributes:
        payload (Optional[RemoteStatusModel], optional): The remote status payload.
            Defaults to None.

    """

    payload: Optional[RemoteStatusModel] = None
