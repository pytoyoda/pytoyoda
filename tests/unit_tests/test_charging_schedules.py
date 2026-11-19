"""Tests for charging schedule management."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import ValidationError

from pytoyoda.api import Api
from pytoyoda.const import VEHICLE_GLOBAL_REMOTE_ELECTRIC_SCHEDULE_ENDPOINT
from pytoyoda.controller import Controller, TokenInfo
from pytoyoda.exceptions import ToyotaApiError
from pytoyoda.models.endpoints.electric import (
    ChargeTime,
    ChargingSchedule,
    ChargingScheduleRequest,
    Days,
    ElectricCommandResponseModel,
)
from pytoyoda.models.vehicle import Vehicle

VIN = "Random0815"


@pytest.fixture
def schedule():
    return ChargingScheduleRequest(
        enabled=True,
        type="startEnd",
        start_time=ChargeTime(hour=12, minute=0),
        end_time=ChargeTime(hour=13, minute=0),
        days=Days(sun=1),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["create", "update", "delete"])
@pytest.mark.parametrize(
    "payload",
    [
        {"returnCode": "000000", "appRequestNo": "abc"},
        {"ReturnCode": "000000", "AppRequestNo": "abc"},
    ],
)
async def test_schedule_api_requests(schedule, operation, payload):
    controller = AsyncMock()
    controller.request_json.return_value = {"payload": payload}
    api = Api(controller)
    if operation == "create":
        response = await api.create_charging_schedule(VIN, schedule)
    elif operation == "update":
        response = await api.update_charging_schedule(VIN, 2, schedule)
    else:
        response = await api.delete_charging_schedule(VIN, 2)

    kwargs = controller.request_json.await_args.kwargs
    expected_body = {
        "enabled": True,
        "type": "startEnd",
        "startTime": {"hour": 12, "minute": 0},
        "endTime": {"hour": 13, "minute": 0},
        "days": {"mon": 0, "tue": 0, "wed": 0, "thu": 0, "fri": 0, "sat": 0, "sun": 1},
    }
    assert kwargs["method"] == {"create": "POST", "update": "PUT", "delete": "DELETE"}[operation]
    endpoint = "/v1/global/remote/electric/charging-schedule"
    assert VEHICLE_GLOBAL_REMOTE_ELECTRIC_SCHEDULE_ENDPOINT == endpoint
    assert kwargs["endpoint"] == (endpoint if operation == "create" else f"{endpoint}/2")
    assert kwargs["vin"] == VIN
    assert kwargs["retry_transient"] is False
    if operation == "update":
        expected_body["id"] = 2
    if operation == "delete":
        assert "body" not in kwargs
    else:
        assert kwargs["body"] == expected_body
    assert response.payload.return_code == "000000"
    assert response.payload.app_request_no == "abc"


@pytest.mark.asyncio
async def test_start_only_schedule_omits_end_time():
    controller = AsyncMock()
    controller.request_json.return_value = {"payload": {"returnCode": "000000"}}
    schedule = ChargingScheduleRequest(
        enabled=False,
        type="startOnly",
        startTime={"hour": 7, "minute": 30},
        days={"mon": 1},
    )
    await Api(controller).create_charging_schedule(VIN, schedule)
    assert "endTime" not in controller.request_json.await_args.kwargs["body"]


def test_request_can_be_built_from_existing_schedule():
    existing = ChargingSchedule.model_validate(
        {
            "id": 3,
            "enabled": True,
            "type": "startEnd",
            "startTime": {"hour": 3, "minute": 45},
            "endTime": {"hour": 4, "minute": 45},
            "days": {"wed": 1},
        }
    )
    request = ChargingScheduleRequest.model_validate(existing, from_attributes=True)
    assert request.start_time.hour == 3
    assert request.days.wed == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"days": {}},
        {"days": {"sun": 2}},
        {"days": {"sun": None}},
        {"startTime": {"hour": 24, "minute": 0}},
        {"startTime": {"hour": 12, "minute": 60}},
        {"startTime": {"hour": "invalid", "minute": 0}},
        {"type": "startEnd", "endTime": None},
        {"type": "startOnly", "endTime": {"hour": 13, "minute": 0}},
        {"type": "unknown"},
    ],
)
def test_invalid_schedule_is_rejected(changes):
    data = {
        "enabled": True,
        "type": "startEnd",
        "startTime": {"hour": 12, "minute": 0},
        "endTime": {"hour": 13, "minute": 0},
        "days": {"sun": 1},
    }
    data.update(changes)
    with pytest.raises(ValidationError):
        ChargingScheduleRequest.model_validate(data)


@pytest.mark.asyncio
async def test_mutated_schedule_is_revalidated_before_sending(schedule):
    schedule.days.sun = 0
    controller = AsyncMock()
    with pytest.raises(ValidationError):
        await Api(controller).create_charging_schedule(VIN, schedule)
    controller.request_json.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("schedule_id", [-1, "1/other", True])
async def test_invalid_schedule_id_is_rejected(schedule_id, schedule):
    controller = AsyncMock()
    api = Api(controller)
    with pytest.raises((TypeError, ValueError)):
        await api.update_charging_schedule(VIN, schedule_id, schedule)
    with pytest.raises((TypeError, ValueError)):
        await api.delete_charging_schedule(VIN, schedule_id)
    controller.request_json.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["create", "update", "delete"])
async def test_vehicle_delegates_schedule_operations(schedule, operation):
    api = AsyncMock()
    result = ElectricCommandResponseModel(payload={"returnCode": "000000"})
    method = getattr(api, f"{operation}_charging_schedule")
    method.return_value = result
    car = Vehicle.__new__(Vehicle)
    car._api = api
    car._vehicle_info = type("_Stub", (), {"vin": VIN})()
    args = {"create": (schedule,), "update": (2, schedule), "delete": (2,)}[operation]

    assert await getattr(car, f"{operation}_charging_schedule")(*args) is result
    method.assert_awaited_once_with(VIN, *args)


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["create", "update", "delete"])
@pytest.mark.parametrize("status_code", [429, 500])
async def test_schedule_writes_do_not_retry_errors(schedule, operation, status_code):
    attempts = []

    def handler(request):
        attempts.append(request)
        return httpx.Response(status_code, json={"error": "failed"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        controller = Controller(username="user@example.com", password="test", http_client=client)
        controller._token_info = TokenInfo(
            access_token="token",
            refresh_token="refresh",
            uuid="test",
            expiration=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        with pytest.raises(ToyotaApiError):
            api = Api(controller)
            if operation == "create":
                await api.create_charging_schedule(VIN, schedule)
            elif operation == "update":
                await api.update_charging_schedule(VIN, 2, schedule)
            else:
                await api.delete_charging_schedule(VIN, 2)
    assert len(attempts) == 1


@pytest.mark.asyncio
async def test_controller_still_retries_transient_errors_by_default(monkeypatch):
    attempts = []

    def handler(request):
        attempts.append(request)
        if len(attempts) == 1:
            return httpx.Response(500, json={"error": "failed"})
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr("pytoyoda.controller.asyncio.sleep", AsyncMock())
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        controller = Controller(username="user@example.com", password="test", http_client=client)
        controller._token_info = TokenInfo(
            access_token="token",
            refresh_token="refresh",
            uuid="test",
            expiration=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        result = await controller.request_json("GET", "/test")
    assert result == {"ok": True}
    assert len(attempts) == 2
