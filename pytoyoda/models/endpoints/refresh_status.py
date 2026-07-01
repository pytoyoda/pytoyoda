"""Toyota Connected Services API - POST /v1/remote/status.

Sent before reading /v1/vehicle/status to wake the vehicle's cellular modem so
the gateway populates the cache that GET reads. The old
/v1/global/remote/refresh-status route required a deviceId/deviceType/guid/vin
body and is now SigV4-fenced (APIGW-403); the migrated /v1/remote/* route takes
the vin as a header only (no body). Contract confirmed against a live car
2026-07-01:

    POST /v1/remote/status   (vin header, no body)
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
    """Payload of the POST /v1/remote/status response."""

    app_request_no: str | None = Field(alias="appRequestNo", default=None)
    return_code: str | None = Field(alias="returnCode", default=None)


class RefreshStatusResponseModel(StatusModel):
    """Full response wrapper for POST /v1/remote/status."""

    payload: RefreshStatusPayloadModel | None = None
