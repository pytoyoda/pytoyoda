"""Toyota Connected Services API - POST /v1/global/remote/refresh-status.

Sent before reading /v1/global/remote/status to wake the vehicle's cellular
modem so the gateway populates the cache that GET reads. The empirical
contract was reverse-engineered from the Toyota Android app and confirmed
on 2026-04-24:

    POST /v1/global/remote/refresh-status
    body: {"deviceId": str, "deviceType": "Android", "guid": str, "vin": str}
    -> 200 OK
       payload.returnCode == "000000"  -> wake accepted
       payload.returnCode != "000000"  -> vehicle does not support endpoint
       (returnCode also surfaces partial-failures for transient backend issues
       but those are rare; treating non-000000 as "not supported" is safe.)
"""

from __future__ import annotations

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class RefreshStatusPayloadModel(CustomEndpointBaseModel):
    """Payload of the POST /v1/global/remote/refresh-status response."""

    return_code: str | None = Field(alias="returnCode", default=None)


class RefreshStatusResponseModel(StatusModel):
    """Full response wrapper for POST /v1/global/remote/refresh-status."""

    payload: RefreshStatusPayloadModel | None = None
