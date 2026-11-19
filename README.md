[![License](https://img.shields.io/github/license/pytoyoda/pytoyoda)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/pytoyoda?logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/pytoyoda/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytoyoda?logo=python&logoColor=white&label=Python)](https://pypi.org/project/pytoyoda/)
[![Github Actions Build](https://img.shields.io/github/actions/workflow/status/zyf722/poetry-plugin-migrate/build.yml?logo=github)](https://github.com/zyf722/poetry-plugin-migrate/actions/workflows/build.yml)
[![Code Coverage](https://img.shields.io/codecov/c/github/pytoyoda/pytoyoda?logo=codecov&logoColor=white)](https://app.codecov.io/github/pytoyoda/pytoyoda/)
[![CodeQL](https://github.com/pytoyoda/pytoyoda/actions/workflows/codeql.yml/badge.svg)](https://github.com/pytoyoda/pytoyoda/actions/workflows/codeql.yml)

# Toyota Connected Services Europe Python module

⚠️ _This is still in beta_
⚠️ _Only EU is supported, other regions are not possible so far._

## Summary

- [Toyota Connected Services Europe Python module](#toyota-connected-services-europe-python-module)
  - [Description](#description)
  - [Installation](#installation)
  - [Docs](#docs)
  - [Usage](#usage)
  - [Known issues](#known-issues)
  - [Contributing](#contributing)
  - [Note](#note)
  - [Credits](#credits)

## Description

Python 3 package to communicate with [Toyota Connected Europe](https://www.toyota-europe.com/about-us/toyota-in-europe/toyota-connected-europe) Services.
This is an unofficial package and Toyota can change their API at any point without warning.

## Installation

This package can be installed through `pip`.

```bash
pip install pytoyoda
```

## Docs

https://pytoyoda.github.io/pytoyoda/pytoyoda.html

## Usage

For a quick start on how to use the package take a look at the `simple_client_example.py` file contained in the report. You can also use and execute this file directly by using the following commands:

```bash
python -m venv pytoyoda
source pytoyoda/bin/activate
python -m pip install "pytoyoda@git+https://github.com/pytoyoda/pytoyoda@main"
curl -LO https://raw.githubusercontent.com/pytoyoda/pytoyoda/main/sandbox/simple_client_example.py
# Create a credentials.json file with {"username":"your@mail.tld","password":"yourpassword"}
python simple_client_example.py
```

Please note that the `simple_client_example.py` file is only to be regarded as a playground and is intended to provide an initial insight into the possibilities. It is not an officially supported interface of the pytoyoda API!
For an overview of the current official interfaces, please take a look at our [documentation](https://pytoyoda.github.io/pytoyoda/pytoyoda/models/vehicle.html).

### Charging commands

For vehicles that support these commands, `Vehicle.send_next_charging_command`
can request a temporary next charging event or set a daily charging time. The
following examples are alternatives; choose the command you intend to send.

Set the next charging start event to Sunday at 12:00:

```python
from pytoyoda.models.endpoints.electric import (
    ChargeCommandType,
    ChargeTime,
    NextChargeSettings,
    ReservationCharge,
    ReservationChargeType,
)

request = NextChargeSettings(
    command=ChargeCommandType.RESERVE_CHARGE,
    reservationcharge=ReservationCharge(
        chargetype=ReservationChargeType.SET_CHARGING_START_TIME,
        day="SUNDAY",
        starttime=ChargeTime(hour=12, minute=0),
    ),
)
response = await car.send_next_charging_command(request)
```

Alternatively, set the next departure/end event to Sunday at 12:00:

```python
request = NextChargeSettings(
    command=ChargeCommandType.RESERVE_CHARGE,
    reservationcharge=ReservationCharge(
        chargetype=ReservationChargeType.SET_CHARGING_END_TIME,
        day="SUNDAY",
        endtime=ChargeTime(hour=12, minute=0),
    ),
)
response = await car.send_next_charging_command(request)
```

Alternatively, set a daily charging start time of 12:00:

```python
request = NextChargeSettings(
    command=ChargeCommandType.SET_CHARGING_TIME,
    charging_time=ChargeTime(hour=12, minute=0),
)
response = await car.send_next_charging_command(request)
```

These commands are separate from the recurring schedule endpoints. A next
charging event temporarily affects the schedule; a daily charging time sets a
recurring start time. An end/departure event may indicate a desired completion
time rather than an immediate stop, but its precise behavior is unverified.
Support and behavior can vary by vehicle.

Relevant vehicle capability flags include:

| Feature | Vehicle capability |
|---|---|
| Next charging event (`RESERVE_CHARGE`) | `nextCharge` |
| Daily charging time (`SET_CHARGING_TIME`) | `dailyCharge` |
| Weekly charging schedules | `weeklyCharge` |

The electric-status field `canSetNextChargingEvent` may also indicate whether a
next event can be set. Capability flags do not guarantee that Toyota will accept
a request or that the vehicle will apply it. The library does not gate these
methods on the flags.

### Charging schedules

Read schedules with `await car.update(only=["electric_status"])` followed by
`car.electric_status.charging_schedules`. The list can be unavailable (`None`).
For supported vehicles, create a weekly schedule using the same API version as
the charging commands:

```python
from pytoyoda.models.endpoints.electric import (
    ChargeTime,
    ChargingScheduleRequest,
    Days,
)

schedule = ChargingScheduleRequest(
    enabled=True,
    type="startEnd",
    start_time=ChargeTime(hour=12, minute=0),
    end_time=ChargeTime(hour=13, minute=0),
    days=Days(sun=1),
)
response = await car.create_charging_schedule(schedule)
```

For a start-only schedule, use `type="startOnly"` and omit `end_time`. To
update an existing schedule, pass its ID and a complete request to
`await car.update_charging_schedule(schedule_id, schedule)`. To delete it, use
`await car.delete_charging_schedule(schedule_id)`. To base an update on a
schedule obtained from the status, use
`ChargingScheduleRequest.model_validate(existing_schedule, from_attributes=True)`.

Toyota may normalize schedule times to five-minute steps; the rounding rule is
unconfirmed.

Schedule changes are asynchronous; an acknowledgement does not guarantee that
the vehicle applied the change, and status or notifications can be delayed.
Schedule writes are not automatically retried; check the current status and
notifications before retrying a failed or uncertain request.

## Known issues

- Statistical endpoint will return `None` if no trip have been performed in the requested timeframe. This problem will often happen at the start of each week, month or year. Also daily stats will of course also be unavailable if no trip have been performed.
- Currently, it is only possible to get various vehicle information. Functions for controlling and setting vehicle properties have not yet been implemented.
- `GET /v1/global/remote/status` (used by `Vehicle.lock_status`) returns `429 APIGW-403 "Unauthorized"` frequently, often without obvious correlation to call rate. Empirically, issuing `POST /v1/global/remote/refresh-status` first - the same wake the Toyota Android app uses - improves the success rate of subsequent GETs and gives fresher `occurrence_date` payloads, suggesting at least some of the 429s come from a stale or empty server-side cache rather than rate-limiting. Other 429s appear to be unrelated to cache state and happen seemingly at random; pytoyoda retries those with exponential backoff. Call `Vehicle.refresh_status()` first, then poll `Vehicle.update(only=["status"])` until `lock_status.last_updated` advances.
- **Trip history retention.** Toyota's trips API (used by `get_trips()`/`get_summary()`) only serves roughly the last 12 months of trips, regardless of the `from_date` you request. This is a limitation of Toyota's backend, not of pytoyoda: trips older than the retention window are permanently deleted on Toyota's side and cannot be recovered through this library, the MyToyota app, the [data export portal](https://eda.toyota-europe.com), or a GDPR data request (Toyota has confirmed this in writing - see [#273](https://github.com/pytoyoda/pytoyoda/issues/273)). If you want to keep a longer history, periodically fetch and store `get_trips()` results locally (e.g. keyed on the trip's stable `id`) before the retention window rolls past them.

## Contributing

This python module uses poetry (>= 2.0.0) and pre-commit.

To start contributing, fork this repository and run `poetry install`. Then create a new branch. Before making a PR, please run pre-commit `poetry run pre-commit run --all-files` and make sure that all tests passes locally first by running `pytest tests/`.

## Note

This is a friendly community fork of the original project by [@DurgNomis-drol](https://github.com/DurgNomis-drol),
to ease up on maintenance and the [bus factor](https://en.wikipedia.org/wiki/Bus_factor) for this project.

## Credits

Special thanks go [@DurgNomis-drol](https://github.com/DurgNomis-drol) for starting this project!
A huge thanks go to [@calmjm](https://github.com/calmjm) for making [tojota](https://github.com/calmjm/tojota).
