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

from pydantic import ConfigDict, Field

from pytoyoda.models.endpoints.common import StatusModel, UnitValueModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class HeatingOptionsModel(CustomEndpointBaseModel):
    """Heating toggles (each ``"off"``/``"on"``).

    Attributes:
        front_defroster: Front windscreen defroster state.
        rear_defogger: Rear window defogger state.
        steering_heater: Steering-wheel heater state.

    """

    # Also constructed in Python (the climate-control write body), so accept both the
    # snake_case field names and the camelCase wire aliases.
    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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


# --- Climate control (actuation) — POST /v2/remote/climate-control ---


class V2RemoteClimateControlRequestModel(CustomEndpointBaseModel):
    """Unified climate-control request body (``POST /v2/remote/climate-control``).

    Replaces the old settings-PUT + control-POST. A ``start`` carries the full desired
    settings; a ``stop`` is just ``command`` (the rest serialize away via
    ``exclude_none``). Reuses the shared ``HeatingOptionsModel``/``SeatOptionsModel``
    read shapes, so the model already supports future writable seat/steering surfaces.

    Attributes:
        command: ``"start"`` or ``"stop"`` (RemoteClimateControl backend values).
        duration: Run duration in minutes; ``None`` = car's saved/default.
        temperature: Target temperature (value + unit).
        heating_options: Front defroster / rear defogger / steering heater (on/off).
        seat_options: Per-seat heater levels.
        save_settings: Persist these settings as the car's defaults.

    """

    # Built in Python by the consumer; accept snake_case field names too.
    model_config = ConfigDict(populate_by_name=True)

    command: str
    duration: int | None = None
    temperature: UnitValueModel | None = None
    heating_options: HeatingOptionsModel | None = Field(
        alias="heatingOptions", default=None
    )
    seat_options: SeatOptionsModel | None = Field(alias="seatOptions", default=None)
    save_settings: bool | None = Field(alias="saveSettings", default=None)


class RemoteClimateControlPayloadModel(CustomEndpointBaseModel):
    """Climate-control command acknowledgement payload.

    Attributes:
        app_request_no: Backend request id for the async command.
        return_code: Command result; ``"000000"`` = accepted/success. Other codes
            (e.g. ``118003``/``600000``/``200000``) are precondition failures
            (car unlocked, door open, key inside, already started).

    """

    app_request_no: str | None = Field(alias="appRequestNo", default=None)
    return_code: str | None = Field(alias="returnCode", default=None)


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


class RemoteClimateControlResponseModel(StatusModel):
    """Model representing a climate-control command response.

    The command result lives in ``payload.return_code`` (``"000000"`` = success),
    a distinct layer from the envelope's ``status.messages[].response_code``.

    Attributes:
        payload: The command acknowledgement (request id + return code).

    """

    payload: RemoteClimateControlPayloadModel | None = None
