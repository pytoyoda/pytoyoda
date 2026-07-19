"""Test lock_status Model."""

from datetime import datetime, timezone

import pytest

from pytoyoda.models.endpoints.status import (
    ComponentStateModel,
    DoorModel,
    DoorsModel,
    RemoteStatusModel,
    RemoteStatusResponseModel,
    WindowsModel,
)
from pytoyoda.models.lock_status import Door, Doors, LockStatus, Window, Windows


def _door(lock: str | None = None, open_: str | None = None) -> DoorModel:
    return DoorModel(
        lockStatus=ComponentStateModel(status=lock) if lock is not None else None,
        openStatus=ComponentStateModel(status=open_) if open_ is not None else None,
    )


# --- Door.closed ------------------------------------------------------------
@pytest.mark.parametrize(
    "door_model, expected",
    [
        (None, None),
        (_door(open_="close"), True),
        (_door(open_="closed"), True),
        (_door(open_="open"), False),
        (_door(open_="wibble"), None),  # unknown enum -> None
        (_door(lock="locked"), None),  # no open_status -> None
    ],
    ids=["none", "close", "closed", "open", "unknown", "no-open-status"],
)
def test_door_closed(door_model, expected):  # noqa: D103
    assert Door(status=door_model).closed == expected


# --- Door.locked ------------------------------------------------------------
@pytest.mark.parametrize(
    "door_model, expected",
    [
        (None, None),
        (_door(lock="locked"), True),
        (_door(lock="unlocked"), False),
        (_door(lock="wibble"), None),  # unknown enum -> None
        (_door(open_="close"), None),  # no lock_status -> None
    ],
    ids=["none", "locked", "unlocked", "unknown", "no-lock-status"],
)
def test_door_locked(door_model, expected):  # noqa: D103
    assert Door(status=door_model).locked == expected


# --- Doors accessors return Door for each position --------------------------
@pytest.mark.parametrize(
    "property_name",
    ["driver_seat", "driver_rear_seat", "passenger_seat", "passenger_rear_seat", "trunk"],
)
def test_doors_properties(property_name):  # noqa: D103
    status = RemoteStatusModel(
        leftHandDrive=True,
        doors=DoorsModel(
            driver=_door(lock="locked"),
            passenger=_door(lock="unlocked"),
            rearLeft=_door(lock="locked"),
            rearRight=_door(lock="unlocked"),
            rearBack=_door(open_="close"),
            hood=_door(open_="close"),
        ),
    )
    assert isinstance(getattr(Doors(status=status), property_name), Door)


# --- Rear door driver/passenger mapping honours left_hand_drive -------------
@pytest.mark.parametrize(
    "left_hand_drive, driver_rear_locked, passenger_rear_locked",
    [
        (True, True, False),  # LHD: driver=left(rearLeft locked), passenger=right(unlocked)
        (False, False, True),  # RHD: driver=right(rearRight unlocked), passenger=left(locked)
        (None, True, False),  # unknown -> defaults to LHD
    ],
    ids=["lhd", "rhd", "unknown-defaults-lhd"],
)
def test_rear_door_side_mapping(
    left_hand_drive, driver_rear_locked, passenger_rear_locked
):
    status = RemoteStatusModel(
        leftHandDrive=left_hand_drive,
        doors=DoorsModel(
            rearLeft=_door(lock="locked"),
            rearRight=_door(lock="unlocked"),
        ),
    )
    doors = Doors(status=status)
    assert doors.driver_rear_seat.locked is driver_rear_locked
    assert doors.passenger_rear_seat.locked is passenger_rear_locked


# --- Window.closed ----------------------------------------------------------
@pytest.mark.parametrize(
    "window_model, expected",
    [
        (None, None),
        (ComponentStateModel(status="close"), True),
        (ComponentStateModel(status="open"), False),
    ],
    ids=["none", "closed", "open"],
)
def test_window_closed(window_model, expected):  # noqa: D103
    assert Window(status=window_model).closed == expected


@pytest.mark.parametrize(
    "property_name",
    ["driver_seat", "driver_rear_seat", "passenger_seat", "passenger_rear_seat"],
)
def test_windows_properties(property_name):  # noqa: D103
    status = RemoteStatusModel(
        leftHandDrive=True,
        windows=WindowsModel(
            driver=ComponentStateModel(status="close"),
            passenger=ComponentStateModel(status="close"),
            rearLeft=ComponentStateModel(status="close"),
            rearRight=ComponentStateModel(status="open"),
        ),
    )
    assert isinstance(getattr(Windows(status=status), property_name), Window)


# --- LockStatus -------------------------------------------------------------
def _response(ts: datetime) -> RemoteStatusResponseModel:
    return RemoteStatusResponseModel(
        payload=RemoteStatusModel(
            vin="TESTVIN",
            lastUpdateTimestamp=ts,
            leftHandDrive=True,
            doors=DoorsModel(driver=_door(lock="locked", open_="close"), hood=_door(open_="close")),
            windows=WindowsModel(driver=ComponentStateModel(status="close")),
        ),
        status="OK",
        code=200,
        errors=[],
        message=None,
    )


def test_lock_status_none():  # noqa: D103
    lock_status = LockStatus(status=None)
    assert lock_status.last_updated is None
    assert lock_status.doors is None
    assert lock_status.windows is None
    assert lock_status.hood is None


def test_lock_status_populated():  # noqa: D103
    ts = datetime(2026, 6, 30, 20, 29, 7, tzinfo=timezone.utc)
    lock_status = LockStatus(status=_response(ts))
    assert lock_status.last_updated == ts  # occurrence_date alias -> lastUpdateTimestamp
    assert isinstance(lock_status.doors, Doors)
    assert isinstance(lock_status.windows, Windows)
    assert lock_status.doors.driver_seat.locked is True
    assert lock_status.doors.driver_seat.closed is True
    assert lock_status.windows.driver_seat.closed is True
    assert lock_status.hood.closed is True
