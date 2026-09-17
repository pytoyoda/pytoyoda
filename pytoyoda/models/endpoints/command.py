"""Toyota Connected Services API - Remote Commands Models."""

from enum import Enum

from pydantic import ConfigDict, Field

from pytoyoda.utils.models import CustomEndpointBaseModel


class CommandType(str, Enum):
    """List of possible remote commands.

    Each value represents a specific command that can be sent to the vehicle.
    """

    DOOR_LOCK = "door-lock"
    DOOR_UNLOCK = "door-unlock"
    ENGINE_START = "engine-start"
    ENGINE_STOP = "engine-stop"
    HAZARD_ON = "hazard-on"
    HAZARD_OFF = "hazard-off"
    # NOTE: WINDOW_ON, WINDOW_OFF and FIND_VEHICLE are kept for
    # compatibility with vehicles/regions where they are accepted, but some
    # backends (e.g. EU, some vehicle classes) reject them with
    # "CTP-REMOTE-40006". See https://github.com/pytoyoda/pytoyoda/issues/274.
    WINDOW_ON = "power-window-on"
    WINDOW_OFF = "power-window-off"
    WINDOW_CLOSE = "power-window-close"
    AC_SETTINGS_ON = "ac-settings-on"
    SOUND_HORN = "sound-horn"
    BUZZER_WARNING = "buzzer-warning"
    FIND_VEHICLE = "find-vehicle"
    VENTILATION_ON = "ventilation-on"
    TRUNK_LOCK = "trunk-lock"
    TRUNK_UNLOCK = "trunk-unlock"
    HEADLIGHT_ON = "headlight-on"
    HEADLIGHT_OFF = "headlight-off"


class RemoteCommandModel(CustomEndpointBaseModel):
    """Model representing a remote command to be sent to a vehicle.

    Attributes:
        command: The specific command to execute
        beep_count: Optional number of beeps for certain commands

    """

    command: CommandType
    beep_count: int | None = Field(alias="beepCount", default=None)

    model_config = ConfigDict(use_enum_values=True)
