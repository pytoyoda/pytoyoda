"""Tests for Controller._prepare_headers()."""

from datetime import datetime, timedelta, timezone

from pytoyoda.controller import Controller, TokenInfo

VALID_USERNAME = "user@example.com"
VALID_PASSWORD = "securepassword123"


def _controller_with_valid_token(**kwargs) -> Controller:
    controller = Controller(username=VALID_USERNAME, password=VALID_PASSWORD, **kwargs)
    controller._token_info = TokenInfo(
        access_token="access-token",
        refresh_token="refresh-token",
        uuid="test-uuid",
        expiration=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    return controller


def test_prepare_headers_includes_x_user_region():
    """x-user-region must mirror x-region on every request.

    Suzuki-badged DCM24 vehicles (Urban Cruiser BEV) reject remote-service
    calls (e.g. POST /v2/remote/climate-control) with CTP-GENERIC-40017
    "Missing header x-user-region" unless this header is present. See
    https://github.com/pytoyoda/ha_toyota/issues/355.
    """
    controller = _controller_with_valid_token()

    headers = controller._prepare_headers()

    assert "x-user-region" in headers
    assert headers["x-user-region"] == headers["x-region"]


def test_prepare_headers_x_user_region_present_with_vin_and_extra_headers():
    controller = _controller_with_valid_token()

    headers = controller._prepare_headers(
        vin="TESTVIN1234567890", additional_headers={"x-foo": "bar"}
    )

    assert headers["x-user-region"] == headers["x-region"]
    assert headers["vin"] == "TESTVIN1234567890"
    assert headers["x-foo"] == "bar"
