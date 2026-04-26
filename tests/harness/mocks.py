"""Respx mocks for every Toyota endpoint pytoyoda hits during a full poll.

Uses the project's existing unit-test JSON fixtures for API responses so that
pytoyoda's pydantic models parse successfully. We are NOT testing API correctness
here; we are exercising the httpx.AsyncClient + asyncio.new_event_loop lifecycle
to reproduce (or rule out) the memory leak.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
import jwt as pyjwt
import respx


TOKEN_EXPIRY_SECONDS = 1800

# Test fixtures ship with the repo at tests/unit_tests/data/
FIXTURES = Path(__file__).resolve().parent.parent / "unit_tests" / "data"


def _load_fixture(name: str) -> Any:
    p = FIXTURES / name
    return json.loads(p.read_text())


def _fake_jwt() -> str:
    """Return a JWT with a uuid claim (pytoyoda decodes id_token and reads .uuid)."""
    return pyjwt.encode(
        {"uuid": "harness-uuid-0001", "sub": "harness", "exp": 9999999999},
        "harness-secret-not-verified",
        algorithm="HS256",
    )


def _response_bodies() -> dict[str, Any]:
    vin = "HARNESSVIN0000001"
    return {
        # pytoyoda's _perform_authentication loops until it sees "tokenId" in the
        # response body. We short-circuit to one round-trip by returning tokenId on
        # the very first POST.
        "authenticate": {
            "tokenId": "harness-token-id-0001",
            "successUrl": "/",
            "realm": "/",
        },
        "authorize": "code=harness-auth-code",
        "tokens": {
            "access_token": _fake_jwt(),
            "refresh_token": _fake_jwt(),
            "id_token": _fake_jwt(),
            "token_type": "Bearer",
            "expires_in": TOKEN_EXPIRY_SECONDS,
        },
        "vehicles": _load_fixture("v2_vehicleguid.json"),
        "location": _load_fixture("v1_location_ok.json"),
        "health": _load_fixture("v1_vehicle_health_ok.json"),
        "remote": _load_fixture("v1_global_remote_status.json"),
        "electric": _load_fixture("v1_global_remote_electric_status.json"),
        "telemetry": _load_fixture("v3_telemetry.json"),
        "notifications": _load_fixture("v2_notification.json"),
        "service_history": _load_fixture("v1_service_history.json"),
        "climate_status": {"payload": None, "status": {"messages": []}},
        "climate_settings": {"payload": None, "status": {"messages": []}},
        "trips": _load_fixture("v1_trips.json"),
    }


def register_all(router: respx.Router) -> None:
    """Register mock routes covering pytoyoda's full poll flow."""
    bodies = _response_bodies()

    # OAuth / auth dance
    router.post(url__regex=r".*/authenticate.*").mock(
        return_value=httpx.Response(200, json=bodies["authenticate"])
    )
    router.get(url__regex=r".*/authorize.*").mock(
        return_value=httpx.Response(
            302,
            headers={"location": f"com.toyota.oneapp:/oauth2Callback?{bodies['authorize']}"},
        )
    )
    router.post(url__regex=r".*/access_token.*").mock(
        return_value=httpx.Response(200, json=bodies["tokens"])
    )

    # API data endpoints. Order matters for respx - first match wins. Paths
    # taken from pytoyoda/const.py VEHICLE_*_ENDPOINT constants.
    router.get(url__regex=r".*/v2/vehicle/guid.*").mock(
        return_value=httpx.Response(200, json=bodies["vehicles"])
    )
    router.get(url__regex=r".*/v1/location.*").mock(
        return_value=httpx.Response(200, json=bodies["location"])
    )
    router.get(url__regex=r".*/v1/vehiclehealth/status.*").mock(
        return_value=httpx.Response(200, json=bodies["health"])
    )
    router.get(url__regex=r".*/v1/global/remote/electric/status.*").mock(
        return_value=httpx.Response(200, json=bodies["electric"])
    )
    router.get(url__regex=r".*/v1/global/remote/climate-status.*").mock(
        return_value=httpx.Response(200, json=bodies["climate_status"])
    )
    router.get(url__regex=r".*/v1/global/remote/climate-settings.*").mock(
        return_value=httpx.Response(200, json=bodies["climate_settings"])
    )
    router.get(url__regex=r".*/v1/global/remote/status.*").mock(
        return_value=httpx.Response(200, json=bodies["remote"])
    )
    router.get(url__regex=r".*/v3/telemetry.*").mock(
        return_value=httpx.Response(200, json=bodies["telemetry"])
    )
    router.get(url__regex=r".*/v2/notification/history.*").mock(
        return_value=httpx.Response(200, json=bodies["notifications"])
    )
    router.get(url__regex=r".*/v1/servicehistory.*").mock(
        return_value=httpx.Response(200, json=bodies["service_history"])
    )
    router.get(url__regex=r".*/v1/trips.*").mock(
        return_value=httpx.Response(200, json=bodies["trips"])
    )

    # Catch-all for any endpoint we missed, so we hit 404 loudly rather than passing
    # through to real Toyota. Keep this LAST.
    router.route(name="fallback_404").mock(
        return_value=httpx.Response(404, json={"error": "harness: unmocked endpoint"})
    )


def make_router() -> respx.Router:
    """Build a configured Router. Caller is responsible for start/stop."""
    router = respx.mock(assert_all_called=False, assert_all_mocked=True, base_url=None)
    register_all(router)
    return router
