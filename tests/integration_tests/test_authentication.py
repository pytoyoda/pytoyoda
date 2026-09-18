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
from pytoyoda.exceptions import ToyotaInvalidUsernameError, ToyotaLoginError

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
    with pytest.raises(ToyotaLoginError):
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
