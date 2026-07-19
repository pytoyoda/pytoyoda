"""Toyota Connected Services API - Status Models.

Models for the ``/v1/vehicle/status`` endpoint. Toyota retired the previous
``/v1/global/remote/status`` route in mid-2026 (it now sits behind AWS SigV4 and
returns ``APIGW-403``); the live app moved to ``/v1/vehicle/status``, whose payload
is directly typed (per-component lock/open/light state) rather than the old
category/section/value blob.
"""

from datetime import datetime

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class ComponentStateModel(CustomEndpointBaseModel):
    """A single component state plus when it was last observed.

    ``status`` carries the backend enum string, e.g. ``"locked"``/``"unlocked"``
    for locks, ``"open"``/``"close"`` for open state, ``"on"``/``"off"`` for lights.
    """

    status: str | None = None
    last_update_timestamp: datetime | None = Field(
        alias="lastUpdateTimestamp", default=None
    )


class DoorModel(CustomEndpointBaseModel):
    """A door with lock and/or open sub-state (the hood reports open only)."""

    lock_status: ComponentStateModel | None = Field(alias="lockStatus", default=None)
    open_status: ComponentStateModel | None = Field(alias="openStatus", default=None)


class DoorsModel(CustomEndpointBaseModel):
    """The set of doors keyed by physical position (+ hood)."""

    driver: DoorModel | None = None
    passenger: DoorModel | None = None
    rear_left: DoorModel | None = Field(alias="rearLeft", default=None)
    rear_right: DoorModel | None = Field(alias="rearRight", default=None)
    rear_back: DoorModel | None = Field(alias="rearBack", default=None)
    hood: DoorModel | None = None


class WindowsModel(CustomEndpointBaseModel):
    """The set of windows keyed by physical position."""

    driver: ComponentStateModel | None = None
    passenger: ComponentStateModel | None = None
    rear_left: ComponentStateModel | None = Field(alias="rearLeft", default=None)
    rear_right: ComponentStateModel | None = Field(alias="rearRight", default=None)


class RemoteStatusModel(CustomEndpointBaseModel):
    """Model representing the vehicle status payload (``/v1/vehicle/status``).

    Attributes:
        vin: Vehicle Identification Number.
        last_update_timestamp: When the vehicle last reported this status.
        overall_status: Aggregate status string (e.g. ``"ok"``).
        overall_warning_counts: Number of active warnings.
        left_hand_drive: Whether the vehicle is left-hand drive. Nullable; used to
            map physical rear-left/rear-right to driver/passenger rear.
        doors: Per-door lock/open state.
        windows: Per-window open state.

    """

    vin: str | None = None
    last_update_timestamp: datetime | None = Field(
        alias="lastUpdateTimestamp", default=None
    )
    overall_status: str | None = Field(alias="overallStatus", default=None)
    overall_warning_counts: int | None = Field(
        alias="overallWarningCounts", default=None
    )
    left_hand_drive: bool | None = Field(alias="leftHandDrive", default=None)
    doors: DoorsModel | None = None
    windows: WindowsModel | None = None

    @property
    def occurrence_date(self) -> datetime | None:
        """Back-compat alias for the retired ``/v1/global/remote/status`` field.

        Consumers (``LockStatus.last_updated`` and ha_toyota's refresh strategy)
        read ``occurrence_date``; the new endpoint calls it ``lastUpdateTimestamp``.
        """
        return self.last_update_timestamp


class RemoteStatusResponseModel(StatusModel):
    r"""Model representing a vehicle status response.

    Inherits from StatusModel.

    Attributes:
        payload (Optional[RemoteStatusModel], optional): The status payload.
            Defaults to None.

    """

    payload: RemoteStatusModel | None = None
