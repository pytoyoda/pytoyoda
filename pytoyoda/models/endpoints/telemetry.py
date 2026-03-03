"""Toyota Connected Services API - Telemetry Models."""

from datetime import datetime

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

    fuel_type: str | None = Field(alias="fuelType")
    odometer: UnitValueModel | None
    fuel_level: int | None = Field(alias="fuelLevel", default=None)
    battery_level: int | None = Field(alias="batteryLevel", default=None)
    charging_status: str | None = Field(alias="chargingStatus", default=None)
    distance_to_empty: UnitValueModel | None = Field(
        alias="distanceToEmpty", default=None
    )
    timestamp: datetime | None


class TelemetryResponseModel(StatusModel):
    """Model representing a telemetry response.

    Inherits from StatusModel.

    Attributes:
        payload (Optional[TelemetryModel], optional): The telemetry payload.
            Defaults to None.

    """

    payload: TelemetryModel | None = None
