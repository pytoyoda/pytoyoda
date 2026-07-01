"""Toyota Connected Services API - Climate Models.

Read models for the ``/v1/vehicle/climate-status`` and ``/v1/vehicle/climate-settings``
endpoints. Toyota retired the previous ``/v1/global/remote/climate-*`` read routes in
mid-2026 (they now sit behind AWS SigV4 and return ``APIGW-403``); the live app moved to
the plain-Bearer ``/v1/vehicle/*`` namespace, whose payloads are directly typed and much
smaller than the old ``acOperations``/min-max settings blob.

Every field is optional: the off-state climate-status payload collapses to just
``{"status": "stopped"}``, and the remaining fields populate only while climate is
starting/running.

``ClimateSettingsRequestModel`` and ``ClimateControlModel`` remain the *legacy write
bodies* used by the not-yet-migrated actuation path (settings PUT / control POST). The
read models below no longer share their shape — actuation is moving to
``POST /v2/remote/climate-control`` (``V2RemoteClimateControlRequest``) in a follow-up.
"""

from datetime import datetime

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel, UnitValueModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class HeatingOptionsModel(CustomEndpointBaseModel):
    """Heating toggles (each ``"off"``/``"on"``).

    Attributes:
        front_defroster: Front windscreen defroster state.
        rear_defogger: Rear window defogger state.
        steering_heater: Steering-wheel heater state.

    """

    front_defroster: str | None = Field(alias="frontDefroster", default=None)
    rear_defogger: str | None = Field(alias="rearDefogger", default=None)
    steering_heater: str | None = Field(alias="steeringHeater", default=None)


class SeatOptionsModel(CustomEndpointBaseModel):
    """Seat-heater levels (each ``"off"``/``"low"``/``"medium"``/``"high"``).

    Attributes:
        driver_seat: Driver seat heater level.
        passenger_seat: Front passenger seat heater level.
        rear_driver_seat: Rear driver-side seat heater level.
        rear_passenger_seat: Rear passenger-side seat heater level.

    """

    driver_seat: str | None = Field(alias="driverSeat", default=None)
    passenger_seat: str | None = Field(alias="passengerSeat", default=None)
    rear_driver_seat: str | None = Field(alias="rearDriverSeat", default=None)
    rear_passenger_seat: str | None = Field(alias="rearPassengerSeat", default=None)


class ClimateStatusModel(CustomEndpointBaseModel):
    """``/v1/vehicle/climate-status`` payload.

    Off-state collapses to just ``status`` (e.g. ``"stopped"``); the remaining fields
    populate while climate is starting/running.

    Attributes:
        status: Backend state enum ``stopped``/``starting``/``stopping``/``running``.
        started_at: When the current climate run started.
        updated_at: When the backend last refreshed this state.
        duration: Programmed run duration, in minutes.
        current_temperature: Measured cabin temperature (value + unit).
        target_temperature: Target temperature (value + unit).
        heating_options: Defroster/defogger/steering-heater states.
        seat_options: Per-seat heater levels.

    """

    status: str | None = None
    started_at: datetime | None = Field(alias="startedAt", default=None)
    updated_at: datetime | None = Field(alias="updatedAt", default=None)
    duration: int | None = None
    current_temperature: UnitValueModel | None = Field(
        alias="currentTemperature", default=None
    )
    target_temperature: UnitValueModel | None = Field(
        alias="targetTemperature", default=None
    )
    heating_options: HeatingOptionsModel | None = Field(
        alias="heatingOptions", default=None
    )
    seat_options: SeatOptionsModel | None = Field(alias="seatOptions", default=None)


class ClimateSettingsModel(CustomEndpointBaseModel):
    """``/v1/vehicle/climate-settings`` payload.

    Attributes:
        duration: Programmed run duration, in minutes.
        temperature: Target temperature (value + unit).
        heating_options: Defroster/defogger/steering-heater settings.
        seat_options: Per-seat heater level settings.

    """

    duration: int | None = None
    temperature: UnitValueModel | None = None
    heating_options: HeatingOptionsModel | None = Field(
        alias="heatingOptions", default=None
    )
    seat_options: SeatOptionsModel | None = Field(alias="seatOptions", default=None)


# --- Legacy write bodies (actuation not yet migrated to /v2/remote/climate-control) ---


class ACParameters(CustomEndpointBaseModel):
    """Legacy AC parameter (write body).

    Attributes:
        available: Whether the AC parameter is available
        display_name: User-friendly name to display in UI
        enabled: Whether the AC parameter is enabled
        icon_url: URL to icon representing the parameter
        name: Internal identifier for the parameter

    """

    available: bool | None = None
    display_name: str | None = Field(alias="displayName", default=None)
    enabled: bool = False
    icon_url: str | None = Field(alias="iconUrl", default=None)
    name: str


class ACOperations(CustomEndpointBaseModel):
    """Legacy AC operation (write body).

    Attributes:
        available: Whether the operation is available
        category_display_name: User-friendly category name
        category_name: Internal category identifier
        ac_parameters: List of AC parameters for this operation

    """

    available: bool | None = None
    category_display_name: str | None = Field(alias="categoryDisplayName", default=None)
    category_name: str = Field(alias="categoryName")
    ac_parameters: list[ACParameters] = Field(
        alias="acParameters", default_factory=list
    )


class ClimateSettingsRequestModel(CustomEndpointBaseModel):
    """Legacy climate-settings write body (``PUT`` climate-settings).

    Superseded by the unified ``POST /v2/remote/climate-control`` request; kept so the
    not-yet-migrated actuation path continues to type-check.

    Attributes:
        ac_operations: List of AC operations to apply
        settings_on: Whether climate settings are active
        temperature: Target temperature
        temperature_unit: Unit of temperature (C or F)

    """

    ac_operations: list[ACOperations] | None = Field(alias="acOperations", default=None)
    settings_on: bool | None = Field(alias="settingsOn", default=None)
    temperature: float | None = None
    temperature_unit: str | None = Field(alias="temperatureUnit", default=None)


class RemoteHVACModel(CustomEndpointBaseModel):
    """Model representing remote HVAC settings.

    Attributes:
        engine_start_time: Time in minutes for engine to run

    """

    engine_start_time: int = Field(alias="engineStartTime")


class ClimateControlModel(CustomEndpointBaseModel):
    """Legacy climate control command body.

    Attributes:
        command: Command to execute (e.g., "engine-start", "engine-stop")
        remote_hvac: Additional HVAC settings if applicable

    """

    command: str
    remote_hvac: RemoteHVACModel | None = Field(alias="remoteHvac", default=None)


class ClimateSettingsResponseModel(StatusModel):
    """Model representing climate settings response.

    Attributes:
        payload: The climate settings data if successful

    """

    payload: ClimateSettingsModel | None = None


class ClimateStatusResponseModel(StatusModel):
    """Model representing climate status response.

    Attributes:
        payload: The climate status data if successful

    """

    payload: ClimateStatusModel | None = None
