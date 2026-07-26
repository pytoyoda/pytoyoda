"""Test pytoyoda client."""

import pytest

from pytoyoda.client import MyT
from pytoyoda.exceptions import ToyotaInvalidUsernameError

# Constants for tests
VALID_USERNAME = "user@example.com"
VALID_PASSWORD = "securepassword123"
INVALID_USERNAME = "userexample.com"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username, password, expected_exception, test_id",
    [
        (VALID_USERNAME, VALID_PASSWORD, None, "happy_path_valid_credentials"),
        (
            INVALID_USERNAME,
            VALID_PASSWORD,
            ToyotaInvalidUsernameError,
            "error_invalid_username",
        ),
    ],
)
async def test_myt_init(  # noqa : D103
    username,
    password,
    expected_exception,
    test_id,  # noqa : ARG001
):
    # Arrange
    if expected_exception:
        with pytest.raises(expected_exception):
            MyT(username, password)
    else:
        # Act
        client = MyT(username, password)
        # Assert
        assert client._api is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "brand, expected_realm_fragment, test_id",
    [
        ("T", "/realms/tme/", "toyota_uses_tme_realm"),
        ("L", "/realms/tme/", "lexus_uses_tme_realm"),
        ("S", "/realms/alliance-subaru/", "subaru_uses_alliance_subaru_realm"),
    ],
)
async def test_myt_brand_urls(  # noqa : D103
    brand,
    expected_realm_fragment,
    test_id,  # noqa : ARG001
):
    client = MyT(VALID_USERNAME, VALID_PASSWORD, brand=brand)
    controller = client._api.controller
    assert expected_realm_fragment in str(controller._authenticate_url)
    assert expected_realm_fragment in str(controller._authorize_url)
    assert expected_realm_fragment in str(controller._access_token_url)
