"""Tests for electric charging command payloads and vehicle delegation."""

import json
from unittest.mock import AsyncMock

import pytest

from pytoyoda.api import Api
from pytoyoda.const import VEHICLE_GLOBAL_REMOTE_ELECTRIC_CONTROL_ENDPOINT
from pytoyoda.models.endpoints.electric import (
    ChargeCommandType,
    ChargeTime,
    ElectricCommandResponseModel,
    NextChargeSettings,
    ReservationCharge,
    ReservationChargeType,
)
from pytoyoda.models.vehicle import Vehicle

VIN = "Random0815"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("command_request", "expected_body"),
    [
        (
            NextChargeSettings(command=ChargeCommandType.CHARGE_NOW),
            {"command": "CHARGE_NOW"},
        ),
        (
            NextChargeSettings(
                command=ChargeCommandType.RESERVE_CHARGE,
                reservationcharge=ReservationCharge(
                    chargetype=ReservationChargeType.SET_CHARGING_START_TIME,
                    day="SUNDAY",
                    starttime=ChargeTime(hour=12, minute=0),
                ),
            ),
            {
                "command": "RESERVE_CHARGE",
                "reservationCharge": {
                    "chargeType": "SET_CHARGING_START_TIME",
                    "day": "SUNDAY",
                    "startTime": {"hour": 12, "minute": 0},
                },
            },
        ),
        (
            NextChargeSettings(
                command=ChargeCommandType.RESERVE_CHARGE,
                reservationCharge={
                    "chargeType": "SET_CHARGING_END_TIME",
                    "day": "MONDAY",
                    "endTime": {"hour": 5, "minute": 30},
                },
            ),
            {
                "command": "RESERVE_CHARGE",
                "reservationCharge": {
                    "chargeType": "SET_CHARGING_END_TIME",
                    "day": "MONDAY",
                    "endTime": {"hour": 5, "minute": 30},
                },
            },
        ),
        (
            NextChargeSettings(
                command=ChargeCommandType.SET_CHARGING_TIME,
                charging_time=ChargeTime(hour=12, minute=0),
            ),
            {
                "command": "SET_CHARGING_TIME",
                "chargingTime": {"hour": 12, "minute": 0},
            },
        ),
        (
            NextChargeSettings(
                command=ChargeCommandType.SET_CHARGING_TIME,
                chargingTime={"hour": 5, "minute": 30},
            ),
            {
                "command": "SET_CHARGING_TIME",
                "chargingTime": {"hour": 5, "minute": 30},
            },
        ),
    ],
    ids=["charge-now", "start-event", "end-event", "charging-time", "time-alias"],
)
async def test_charging_command_request(command_request, expected_body):
    """Commands use the app's endpoint, VIN and exact JSON payload."""
    controller = AsyncMock()
    controller.request_json.return_value = {"payload": {"returnCode": "000000"}}
    api = Api(controller)

    response = await api.send_next_charging_command(VIN, command_request)

    controller.request_json.assert_awaited_once()
    kwargs = controller.request_json.await_args.kwargs
    assert kwargs["method"] == "POST"
    assert kwargs["endpoint"] == VEHICLE_GLOBAL_REMOTE_ELECTRIC_CONTROL_ENDPOINT
    assert kwargs["endpoint"] == "/v1/global/remote/electric/command"
    assert kwargs["vin"] == VIN
    assert json.loads(json.dumps(kwargs["body"])) == expected_body
    assert response.payload.return_code == "000000"


@pytest.mark.asyncio
async def test_vehicle_charging_command_delegates_to_api():
    """The public vehicle method forwards the command and acknowledgement."""
    api = AsyncMock()
    api.send_next_charging_command.return_value = ElectricCommandResponseModel(
        payload={"returnCode": "000000"}
    )
    vehicle = Vehicle.__new__(Vehicle)
    vehicle._api = api
    vehicle._vehicle_info = type("_Stub", (), {"vin": VIN})()
    request = NextChargeSettings(
        command=ChargeCommandType.SET_CHARGING_TIME,
        charging_time=ChargeTime(hour=5, minute=30),
    )

    result = await vehicle.send_next_charging_command(request)

    api.send_next_charging_command.assert_awaited_once_with(VIN, command=request)
    assert result is api.send_next_charging_command.return_value
