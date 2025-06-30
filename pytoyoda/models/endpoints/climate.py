"""Toyota Connected Services API - Climate Models."""

# ruff: noqa: FA100

from datetime import datetime
from typing import Optional

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel, UnitValueModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class ACParameters(CustomEndpointBaseModel):
    """Model representing parameters for AC.

    Attributes:
        available: Whether the AC parameter is available
        display_name: User-friendly name to display in UI
        enabled: Whether the AC parameter is enabled
        icon_url: URL to icon representing the parameter
        name: Internal identifier for the parameter

    """

    available: Optional[bool] = None
    display_name: Optional[str] = Field(alias="displayName", default=None)
    enabled: bool = False
    icon_url: Optional[str] = Field(alias="iconUrl", default=None)
    name: str


class ACOperations(CustomEndpointBaseModel):
    """Model representing AC operations.

    Attributes:
        available: Whether the operation is available
        category_display_name: User-friendly category name
        category_name: Internal category identifier
        ac_parameters: List of AC parameters for this operation

    """

    available: Optional[bool] = None
    category_display_name: Optional[str] = Field(
        alias="categoryDisplayName", default=None
    )
    category_name: str = Field(alias="categoryName")
    ac_parameters: list[ACParameters] = Field(
        alias="acParameters", default_factory=list
    )


class ClimateSettingsModel(CustomEndpointBaseModel):
    """Model representing climate settings.

    Attributes:
        ac_operations: List of available AC operations
        max_temp: Maximum allowable temperature
        min_temp: Minimum allowable temperature
        settings_on: Whether climate settings are active
        temp_interval: Temperature increment for controls
        temperature: Current target temperature
        temperature_unit: Unit of temperature (C or F)

    """

    ac_operations: Optional[list[ACOperations]] = Field(
        alias="acOperations", default=None
    )
    max_temp: Optional[float] = Field(alias="maxTemp", default=None)
    min_temp: Optional[float] = Field(alias="minTemp", default=None)
    settings_on: bool = Field(alias="settingsOn")
    temp_interval: Optional[float] = Field(alias="tempInterval", default=None)
    temperature: float
    temperature_unit: str = Field(alias="temperatureUnit")


class CurrentTemperature(UnitValueModel):
    """Model representing current temperature.

    Attributes:
        timestamp: When the temperature was recorded

    """

    timestamp: datetime


class ClimateOptions(CustomEndpointBaseModel):
    """Model representing climate options.

    Attributes:
        front_defogger: Whether front defogger is active
        rear_defogger: Whether rear defogger is active

    """

    front_defogger: bool = Field(alias="frontDefogger")
    rear_defogger: bool = Field(alias="rearDefogger")


class ClimateStatusModel(CustomEndpointBaseModel):
    """Model representing climate status.

    Attributes:
        current_temperature: Currently measured temperature
        duration: Duration in minutes for operation
        options: Additional climate options
        started_at: When climate control was started
        status: Whether climate control is active
        target_temperature: Desired temperature
        type: Type of climate control mode

    """

    current_temperature: Optional[CurrentTemperature] = Field(
        alias="currentTemperature", default=None
    )
    duration: Optional[int] = None
    options: Optional[ClimateOptions] = None
    started_at: Optional[datetime] = Field(alias="startedAt", default=None)
    status: bool
    target_temperature: Optional[UnitValueModel] = Field(
        alias="targetTemperature", default=None
    )
    type: str


class RemoteHVACModel(CustomEndpointBaseModel):
    """Model representing remote HVAC settings.

    Attributes:
        engine_start_time: Time in minutes for engine to run

    """

    engine_start_time: int = Field(alias="engineStartTime")


class ClimateControlModel(CustomEndpointBaseModel):
    """Model representing climate control commands.

    Attributes:
        command: Command to execute (e.g., "start", "stop")
        remote_hvac: Additional HVAC settings if applicable

    """

    command: str
    remote_hvac: Optional[RemoteHVACModel] = Field(alias="remoteHvac", default=None)


class ClimateSettingsResponseModel(StatusModel):
    """Model representing climate settings response.

    Attributes:
        payload: The climate settings data if successful

    """

    payload: Optional[ClimateSettingsModel] = None


class ClimateStatusResponseModel(StatusModel):
    """Model representing climate status response.

    Attributes:
        payload: The climate status data if successful

    """

    payload: Optional[ClimateStatusModel] = None
