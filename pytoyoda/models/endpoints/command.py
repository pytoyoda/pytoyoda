"""Toyota Connected Services API - Remote Commands Models."""

# ruff: noqa: FA100

from enum import Enum
from typing import Optional

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
    WINDOW_ON = "power-window-on"
    WINDOW_OFF = "power-window-off"
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
    beep_count: Optional[int] = Field(alias="beepCount", default=None)

    model_config = ConfigDict(use_enum_values=True)
