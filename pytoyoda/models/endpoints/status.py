"""Toyota Connected Services API - Status Models."""

from datetime import datetime

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel, UnitValueModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class _ValueStatusModel(CustomEndpointBaseModel):
    value: str | None
    status: int | None


class SectionModel(CustomEndpointBaseModel):
    """Model representing the status category of a vehicle.

    Attributes:
        section (str): The section of a vehicle status category.
        values (list[_ValueStatusModel]): A list of values corresponding
            status informations.

    """

    section: str | None
    values: list[_ValueStatusModel] | None


class VehicleStatusModel(CustomEndpointBaseModel):
    """Model representing the status category of a vehicle.

    Attributes:
        category (str): The status category of the vehicle.
        display_order (int): The order in which the status category is displayed
            inside the MyToyota App.
        sections (list[SectionModel]): The different sections belonging to the category.

    """

    category: str | None
    display_order: int | None = Field(alias="displayOrder")
    sections: list[SectionModel] | None


class _TelemetryModel(CustomEndpointBaseModel):
    fugage: UnitValueModel | None = None
    rage: UnitValueModel | None = None
    odo: UnitValueModel | None


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

    vehicle_status: list[VehicleStatusModel] | None = Field(alias="vehicleStatus")
    telemetry: _TelemetryModel | None
    occurrence_date: datetime | None = Field(alias="occurrenceDate")
    caution_overall_count: int | None = Field(alias="cautionOverallCount")
    latitude: float | None
    longitude: float | None
    location_acquisition_datetime: datetime | None = Field(
        alias="locationAcquisitionDatetime"
    )


class RemoteStatusResponseModel(StatusModel):
    r"""Model representing a remote status response.

    Inherits from StatusModel.

    Attributes:
        payload (Optional[RemoteStatusModel], optional): The remote status payload.
            Defaults to None.

    """

    payload: RemoteStatusModel | None = None
