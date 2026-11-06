"""Pytest tests for pytoyoda using httpx mocking."""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import List

import pytest
from conftest import TEST_PASSWORD, TEST_TOKEN, TEST_USER, TEST_UUID
from pytest_httpx import HTTPXMock

from pytoyoda import MyT
from pytoyoda.controller import Controller, TokenInfo
from pytoyoda.exceptions import (
    ToyotaInvalidUsernameError,
    ToyotaLoginError,
    ToyotaLoginServerError,
)

_TOKEN_CACHE = Controller._TOKEN_CACHE  # pylint: disable=W0212


def build_routes(httpx_mock: HTTPXMock, filenames: List[str]) -> None:  # noqa: D103
    for filename in filenames:
        # TODO: Move to fixture once I know how to use a fixture from a fixture
        path: str = f"{Path(__file__).parent}/data/"

        with open(
            f"{path}/{filename}", encoding="utf-8"
        ) as f:  # I cant see a problem for the tests
            routes = json.load(f)

        for route in routes:
            fixed_url = route["request"]["url"]
            fixed_url = fixed_url.replace(
                "{trip_date_from}", str(date.today() - timedelta(days=90))
            )
            fixed_url = fixed_url.replace("{trip_date_to}", str(date.today()))

            httpx_mock.add_response(
                method=route["request"]["method"],
                url=fixed_url,
                status_code=route["response"]["status"],
                content=route["response"]["content"]
                if isinstance(route["response"]["content"], str)
                else json.dumps(route["response"]["content"]),
                headers=route["response"]["headers"],
            )


@pytest.mark.asyncio
@pytest.mark.usefixtures("remove_cache")
async def test_authenticate(httpx_mock):  # noqa: D103
    build_routes(httpx_mock, ["authenticate_working.json"])

    client = MyT(TEST_USER, TEST_PASSWORD)
    # Nothing validates this is correct,
    # just replays a "correct" authentication sequence
    await client.login()


@pytest.mark.asyncio
@pytest.mark.usefixtures("remove_cache")
async def test_authenticate_subaru(httpx_mock):  # noqa: D103
    build_routes(httpx_mock, ["authenticate_working_subaru.json"])

    client = MyT(TEST_USER, TEST_PASSWORD, brand="S")
    # Replays a Subaru authentication sequence using
    # the alliance-subaru realm and Subaru client credentials
    await client.login()


@pytest.mark.asyncio
@pytest.mark.usefixtures("remove_cache")
async def test_authenticate_invalid_username(httpx_mock: HTTPXMock):  # noqa: D103
    build_routes(httpx_mock, ["authenticate_invalid_username.json"])

    client = MyT(TEST_USER, TEST_PASSWORD)
    # Nothing validates this is correct,
    # just replays an invalid username authentication sequence
    with pytest.raises(ToyotaInvalidUsernameError):
        await client.login()


@pytest.mark.asyncio
@pytest.mark.usefixtures("remove_cache")
async def test_authenticate_invalid_password(httpx_mock: HTTPXMock):  # noqa: D103
    build_routes(httpx_mock, ["authenticate_invalid_password.json"])

    client = MyT(TEST_USER, TEST_PASSWORD)
    # Nothing validates this is correct,
    # just replays an invalid username authentication sequence
    with pytest.raises(ToyotaLoginError) as exc_info:
        await client.login()
    # A rejected password is a real credential failure, not a server outage.
    assert not isinstance(exc_info.value, ToyotaLoginServerError)


def _load_routes(filename: str) -> list[dict]:
    path = Path(__file__).parent / "data" / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _add_route(httpx_mock: HTTPXMock, route: dict, status: int | None = None) -> None:
    content = route["response"]["content"]
    httpx_mock.add_response(
        method=route["request"]["method"],
        url=route["request"]["url"],
        status_code=status or route["response"]["status"],
        content=content if isinstance(content, str) else json.dumps(content),
        headers=route["response"]["headers"],
    )


def _add_gateway_error(httpx_mock: HTTPXMock, route: dict, status: int) -> None:
    httpx_mock.add_response(
        method=route["request"]["method"],
        url=route["request"]["url"],
        status_code=status,
        text="<html><body><h1>502 Bad Gateway</h1></body></html>",
    )


@pytest.mark.asyncio
@pytest.mark.usefixtures("remove_cache")
@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
async def test_authenticate_server_error(httpx_mock: HTTPXMock, status: int) -> None:
    """A login gateway outage is reported as a transient server error."""
    first_post = _load_routes("authenticate_working.json")[0]
    _add_gateway_error(httpx_mock, first_post, status)

    client = MyT(TEST_USER, TEST_PASSWORD)
    with pytest.raises(ToyotaLoginServerError) as exc_info:
        await client.login()

    assert exc_info.value.status_code == status
    # Callers catching the old exception keep working.
    assert isinstance(exc_info.value, ToyotaLoginError)
    assert str(exc_info.value).startswith(f"Authentication Failed. {status},")


@pytest.mark.asyncio
@pytest.mark.usefixtures("remove_cache")
async def test_authorize_server_error(httpx_mock: HTTPXMock) -> None:
    """A 5xx from the authorize step is a server error, not a bad login."""
    routes = _load_routes("authenticate_working.json")
    for route in routes[:4]:
        _add_route(httpx_mock, route)
    _add_gateway_error(httpx_mock, routes[4], 503)

    client = MyT(TEST_USER, TEST_PASSWORD)
    with pytest.raises(ToyotaLoginServerError) as exc_info:
        await client.login()
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
@pytest.mark.usefixtures("remove_cache")
async def test_token_retrieval_server_error(httpx_mock: HTTPXMock) -> None:
    """A 5xx from the access-token step is a server error, not a bad login."""
    routes = _load_routes("authenticate_working.json")
    for route in routes[:5]:
        _add_route(httpx_mock, route)
    _add_gateway_error(httpx_mock, routes[5], 504)

    client = MyT(TEST_USER, TEST_PASSWORD)
    with pytest.raises(ToyotaLoginServerError) as exc_info:
        await client.login()
    assert exc_info.value.status_code == 504


@pytest.mark.asyncio
@pytest.mark.usefixtures("remove_cache")
async def test_token_retrieval_client_error_stays_login_error(
    httpx_mock: HTTPXMock,
) -> None:
    """A 4xx from the access-token step remains a plain login error."""
    routes = _load_routes("authenticate_working.json")
    for route in routes[:5]:
        _add_route(httpx_mock, route)
    _add_route(httpx_mock, routes[5], status=400)

    client = MyT(TEST_USER, TEST_PASSWORD)
    with pytest.raises(ToyotaLoginError) as exc_info:
        await client.login()
    assert not isinstance(exc_info.value, ToyotaLoginServerError)


def _cache_expired_token() -> None:
    _TOKEN_CACHE[TEST_USER] = TokenInfo(
        access_token=TEST_TOKEN,
        refresh_token=TEST_TOKEN,
        uuid=TEST_UUID,
        expiration=datetime(2024, 1, 1, 16, 20, 20, 316881, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
@pytest.mark.usefixtures("remove_cache")
async def test_refresh_and_authenticate_server_error(httpx_mock: HTTPXMock) -> None:
    """Refresh and the fallback full login both hitting 502 is a server error."""
    _cache_expired_token()
    refresh = _load_routes("authenticate_refresh_token.json")[0]
    _add_gateway_error(httpx_mock, refresh, 502)
    _add_gateway_error(httpx_mock, _load_routes("authenticate_working.json")[0], 502)

    client = MyT(TEST_USER, TEST_PASSWORD)
    with pytest.raises(ToyotaLoginServerError) as exc_info:
        await client.login()
    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
@pytest.mark.usefixtures("remove_cache")
async def test_refresh_server_error_falls_back_to_login(httpx_mock: HTTPXMock) -> None:
    """A 5xx on token refresh still falls back to a full login."""
    _cache_expired_token()
    refresh = _load_routes("authenticate_refresh_token.json")[0]
    _add_gateway_error(httpx_mock, refresh, 502)
    for route in _load_routes("authenticate_working.json"):
        _add_route(httpx_mock, route)

    client = MyT(TEST_USER, TEST_PASSWORD)
    await client.login()


@pytest.mark.asyncio
async def test_authenticate_refresh_token(httpx_mock: HTTPXMock):  # noqa: D103
    #  Create token with expired 'expiration' datetime.
    _TOKEN_CACHE[TEST_USER] = TokenInfo(
        access_token=TEST_TOKEN,
        refresh_token=TEST_TOKEN,
        uuid=TEST_UUID,
        expiration=datetime(2024, 1, 1, 16, 20, 20, 316881, tzinfo=timezone.utc),
    )

    build_routes(httpx_mock, ["authenticate_refresh_token.json"])

    client = MyT(TEST_USER, TEST_PASSWORD)
    # Nothing validates this is correct,
    # just replays a refresh token sequence
    await client.login()


@pytest.mark.asyncio
async def test_get_static_data(httpx_mock: HTTPXMock):  # noqa: D103
    #  Create valid token => Means no authentication requests
    _TOKEN_CACHE[TEST_USER] = TokenInfo(
        access_token=TEST_TOKEN,
        refresh_token=TEST_TOKEN,
        uuid=TEST_UUID,
        expiration=datetime.now(timezone.utc) + timedelta(hours=4),
    )

    # Ensure expired cache file.
    build_routes(httpx_mock, ["get_static_data.json"])

    client = MyT(TEST_USER, TEST_PASSWORD, use_metric=True)
    # Nothing validates this is correct,
    # just replays a refresh token sequence
    await client.login()
    cars = await client.get_vehicles()
    car = cars[0]
    await car.update()

    # Check VIN
    assert car.vin == "12345678912345678"

    # Check alias
    assert car.alias == "RAV4"

    # Check Dashboard
    assert car.dashboard.odometer == 9999.975
    assert car.dashboard.fuel_level == 10
    assert car.dashboard.battery_level == 22
    assert car.dashboard.fuel_range == 112.654
    assert car.dashboard.battery_range == 33.0
    assert car.dashboard.battery_range_with_ac == 30
    assert car.dashboard.range == 100
    assert len(car.dashboard.warning_lights) == 0

    # Check location
    assert car.location.latitude == 50.0
    assert car.location.longitude == 0.0

    # Check Notifications
    assert len(car.notifications) == 3
    assert (
        car.notifications[0].message
        == "2020 RAV4 PHEV: Climate control was interrupted (Door open) [1]"
    )
    assert car.notifications[0].type == "alert"
    assert car.notifications[0].category == "RemoteCommand"
    assert (
        car.notifications[1].message
        == "2020 RAV4 PHEV: Climate was started and will automatically shut off."
    )
    assert car.notifications[2].message == "2020 RAV4 PHEV: Charging Interrupted [4]."

    # Check last trip
    assert car.last_trip is not None
    assert car.last_trip.distance == 15.215
    assert car.last_trip.ev_duration == timedelta(minutes=10, seconds=53)
    assert car.last_trip.average_fuel_consumed == 1.485
    assert car.last_trip.score == 65
