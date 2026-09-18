"""Tests for injecting a custom httpx.AsyncClient into the Controller/MyT."""

from datetime import datetime, timedelta, timezone

import httpx
import pytest

from pytoyoda.client import MyT
from pytoyoda.controller import Controller, TokenInfo

VALID_USERNAME = "user@example.com"
VALID_PASSWORD = "securepassword123"


def _controller_with_valid_token(**kwargs) -> Controller:
    """Build a Controller with a pre-seeded, non-expired token.

    Skips the login/auth flow so tests can focus on `request_raw` behavior.
    """
    controller = Controller(username=VALID_USERNAME, password=VALID_PASSWORD, **kwargs)
    controller._token_info = TokenInfo(
        access_token="access-token",
        refresh_token="refresh-token",
        uuid="test-uuid",
        expiration=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    return controller


@pytest.mark.asyncio
async def test_default_behavior_constructs_and_owns_client():
    """Without an injected client, Controller lazily builds and owns one."""
    controller = _controller_with_valid_token()

    assert controller._client is None
    assert controller._owns_client is True

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    # Simulate what request_raw does internally, but with a mock transport
    # so no real network I/O happens.
    controller._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    response = await controller.request_raw("GET", "/some/endpoint")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    # Controller owns this client, so aclose() should actually close it.
    assert controller._owns_client is True
    await controller.aclose()
    assert controller._client is None


@pytest.mark.asyncio
async def test_injected_client_is_used_for_requests():
    """A caller-supplied httpx.AsyncClient is used to make requests."""
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"from": "custom-client"})

    custom_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    controller = _controller_with_valid_token(http_client=custom_client)

    assert controller._client is custom_client
    assert controller._owns_client is False

    response = await controller.request_raw("GET", "/some/endpoint")

    assert len(calls) == 1
    assert response.json() == {"from": "custom-client"}
    # request_raw must not have replaced the injected client with a new one.
    assert controller._client is custom_client

    await custom_client.aclose()


@pytest.mark.asyncio
async def test_injected_client_is_not_closed_by_controller():
    """Controller must never close a client it did not create."""
    custom_client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={}))
    )
    controller = _controller_with_valid_token(http_client=custom_client)

    await controller.aclose()

    # aclose() is a no-op for an injected client: the reference is kept and
    # the underlying transport must not have been closed.
    assert controller._client is custom_client
    assert not custom_client.is_closed


@pytest.mark.asyncio
async def test_myt_forwards_http_client_to_controller():
    """MyT() forwards the http_client argument down to its Controller."""
    custom_client = httpx.AsyncClient()
    myt = MyT(VALID_USERNAME, VALID_PASSWORD, http_client=custom_client)

    controller = myt._api.controller
    assert controller._client is custom_client
    assert controller._owns_client is False

    await custom_client.aclose()
