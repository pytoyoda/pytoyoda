"""Toyota Connected Services API - Telemetry Models."""

# ruff: noqa: FA100

from datetime import datetime
from typing import Optional

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel, UnitValueModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class TelemetryModel(CustomEndpointBaseModel):
    """Model representing telemetry data.

    Attributes:
        fuel_type (str): The type of fuel.
        odometer (UnitValueModel): The odometer reading.
        fuel_level (Optional[int]): The fuel level.
        battery_level (Optional[int]): The battery level.
        charging_status (Optional[str]): The state of charging.
        distance_to_empty (Optional[UnitValueModel], optional): The estimated distance
            to empty. Defaults to None.
        timestamp (datetime): The timestamp of the telemetry data.

    """

    fuel_type: Optional[str] = Field(alias="fuelType")
    odometer: Optional[UnitValueModel]
    fuel_level: Optional[int] = Field(alias="fuelLevel", default=None)
    battery_level: Optional[int] = Field(alias="batteryLevel", default=None)
    charging_status: Optional[str] = Field(alias="chargingStatus", default=None)
    distance_to_empty: Optional[UnitValueModel] = Field(
        alias="distanceToEmpty", default=None
    )
    timestamp: Optional[datetime]


class TelemetryResponseModel(StatusModel):
    """Model representing a telemetry response.

    Inherits from StatusModel.

    Attributes:
        payload (Optional[TelemetryModel], optional): The telemetry payload.
            Defaults to None.

    """

    payload: Optional[TelemetryModel] = None
