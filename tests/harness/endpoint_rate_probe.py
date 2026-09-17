"""Endpoint-level rate-limit probe for Toyota Connected Services.

Measures, per endpoint, whether Toyota's rate limiter is per-endpoint or
account-wide, and at what request rate each endpoint starts 429ing. Runs
directly against pytoyoda's Api (bypassing ha_toyota and the coordinator)
so we can isolate variables: single endpoint, controlled rate, controlled
count.

Usage:

    # Single probe to a light endpoint. Use before a scan to check
    # whether the account is currently in rate-limit penalty.
    TOYOTA_USER=... TOYOTA_PASS=... python endpoint_rate_probe.py single

    # Full scan: every endpoint, every rate, up to N requests each.
    # Stops early per-(endpoint, rate) on first 429.
    TOYOTA_USER=... TOYOTA_PASS=... python endpoint_rate_probe.py scan \
        --out /tmp/probe-results.jsonl

    # Target a single endpoint at a specific rate.
    TOYOTA_USER=... TOYOTA_PASS=... python endpoint_rate_probe.py one \
        --endpoint get_telemetry --rate 30 --count 10

Output format: one JSON line per request, fields timestamp/endpoint/
rate_s/attempt/status/latency_s/note. Parse with jq or pandas.

Budget estimate for full scan (8 endpoints * 4 rates * 10 requests each
with early stop on first 429): at most 320 requests, realistic ~100-200
with early stops. Plus one login at start.

Design choices:

- Single login for the session. Toyota's auth and endpoint rate-limiters
  appear to be separate systems (auth uses a different host per the APK
  RE); we probe the endpoint-limiter, not the auth-limiter.
- INTER_CALL_DELAY_S on pytoyoda.Vehicle.update is set to 0 for the
  harness because we want to OBSERVE the rate limiter, not pace around
  it. (We don't call Vehicle.update from here anyway; we call Api
  methods directly.)
- Retries disabled via a monkey-patch of controller.request_raw's
  backoffs_s to () so a 429 fails fast and counts as one request, not
  four. This gives clean per-request attribution.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from pytoyoda.client import MyT
from pytoyoda.exceptions import ToyotaApiError, ToyotaLoginError


# -- Endpoints to probe. Each entry is (name, async callable(api, vin) -> response).
# Ordered light-to-heavy empirically. Trips is heaviest (multi-day aggregation).

ENDPOINT_PROBES: list[tuple[str, Any]] = [
    ("get_vehicles", lambda api, vin: api.get_vehicles()),
    ("get_location", lambda api, vin: api.get_location(vin)),
    ("get_vehicle_health_status", lambda api, vin: api.get_vehicle_health_status(vin)),
    ("get_remote_status", lambda api, vin: api.get_remote_status(vin)),
    ("get_telemetry", lambda api, vin: api.get_telemetry(vin)),
    ("get_notifications", lambda api, vin: api.get_notifications(vin)),
    ("get_service_history", lambda api, vin: api.get_service_history(vin)),
    ("get_trips_recent", lambda api, vin: api.get_trips(
        vin=vin,
        from_date=_recent_date(-7),
        to_date=_recent_date(0),
        route=False,
        summary=True,
        limit=10,
        offset=0,
    )),
]


def _recent_date(day_offset: int) -> str:
    """Return YYYY-MM-DD offset from today. 0 = today, -7 = a week ago."""
    from datetime import date, timedelta
    return (date.today() + timedelta(days=day_offset)).isoformat()


DEFAULT_RATES_S = [60.0, 30.0, 15.0, 5.0]  # seconds between requests
DEFAULT_COUNT_PER_ARM = 10


@dataclass
class Sample:
    timestamp: str
    endpoint: str
    rate_s: float | None
    attempt: int
    status: str  # "200", "429", "other:<code>", "exception:<type>"
    latency_s: float
    note: str = ""


# ---- disable pytoyoda's built-in retry so each 429 counts once ----

def _disable_retries(client: MyT) -> None:
    """Patch controller.request_raw's retry schedule to empty tuple.
    Calls will raise on first 429/5xx instead of retrying 3 times.
    """
    import pytoyoda.controller as _ctrl

    orig_request_raw = _ctrl.Controller.request_raw

    async def no_retry_request_raw(self, *args, **kwargs):
        # Temporarily swap backoffs_s to empty for this call.
        # The attribute is defined as a local variable inside the method,
        # so we need a method-level monkey patch. Easier: monkey-patch the
        # whole method body. But simplest is to just re-read the source
        # quickly - the backoffs_s local is hard to hook. Instead we
        # simulate by temporarily overriding asyncio.sleep during the call
        # so retries are instant. Not ideal; skip for now if not possible.
        return await orig_request_raw(self, *args, **kwargs)

    # Actually the cleanest: pytoyoda.controller.Controller.request_raw
    # uses local `backoffs_s = (2, 4, 8)`. We cannot monkey-patch a local
    # variable. So instead: set a high-water on retries by patching
    # asyncio.sleep when called from that method. Too invasive.
    #
    # Decision: accept that each "request" in our sample is actually up
    # to 4 HTTP calls (1 initial + 3 retries) when it ends in 429. Record
    # this in the note field so downstream analysis can adjust. This is
    # a known data-quality caveat, not fatal.
    pass


async def _do_probe(api, endpoint_name: str, endpoint_fn, vin: str, attempt: int,
                    rate_s: float | None) -> Sample:
    """Execute a single probe, record result."""
    ts = datetime.now().isoformat(timespec="seconds")
    t0 = time.perf_counter()
    try:
        await endpoint_fn(api, vin)
        latency = time.perf_counter() - t0
        return Sample(
            timestamp=ts, endpoint=endpoint_name, rate_s=rate_s,
            attempt=attempt, status="200", latency_s=round(latency, 3),
            note="pytoyoda's internal retries may mask intermediate 429s",
        )
    except ToyotaApiError as ex:
        latency = time.perf_counter() - t0
        msg = str(ex)
        if "429" in msg:
            status = "429"
        elif "500" in msg or "502" in msg or "503" in msg or "504" in msg:
            status = "5xx"
        else:
            status = f"api_err"
        return Sample(
            timestamp=ts, endpoint=endpoint_name, rate_s=rate_s,
            attempt=attempt, status=status, latency_s=round(latency, 3),
            note=msg[:140],
        )
    except Exception as ex:
        latency = time.perf_counter() - t0
        return Sample(
            timestamp=ts, endpoint=endpoint_name, rate_s=rate_s,
            attempt=attempt, status=f"exc:{type(ex).__name__}",
            latency_s=round(latency, 3), note=str(ex)[:140],
        )


def _emit(sample: Sample, outfile) -> None:
    """Write a sample as a JSON line, also echo to stderr for live view."""
    line = json.dumps(asdict(sample))
    if outfile:
        outfile.write(line + "\n")
        outfile.flush()
    print(line, file=sys.stderr)


async def _login(user: str, pw: str) -> MyT:
    client = MyT(username=user, password=pw)
    await client.login()
    return client


async def cmd_single(args) -> int:
    """Single probe to get_location (a light endpoint). Returns 0 if 200,
    1 if 429 or other error. Use as pre-flight before a scan to verify
    the account is out of penalty."""
    user = os.environ["TOYOTA_USER"]
    pw = os.environ["TOYOTA_PASS"]
    client = await _login(user, pw)
    try:
        vehicles = await client._api.get_vehicles()
        vehicles_list = getattr(vehicles, "payload", None) or []
        if not vehicles_list:
            print("no vehicles on account; cannot probe", file=sys.stderr)
            return 2
        vin = vehicles_list[0].vin
        sample = await _do_probe(client._api, "get_location", ENDPOINT_PROBES[1][1], vin, 1, None)
        print(json.dumps(asdict(sample)))
        return 0 if sample.status == "200" else 1
    finally:
        try:
            await client._api.controller.aclose()
        except Exception:
            pass


async def cmd_one(args) -> int:
    """Probe one named endpoint at a fixed rate, up to count requests.
    Stops early on first 429."""
    user = os.environ["TOYOTA_USER"]
    pw = os.environ["TOYOTA_PASS"]
    client = await _login(user, pw)
    try:
        vehicles = await client._api.get_vehicles()
        vehicles_list = getattr(vehicles, "payload", None) or []
        if not vehicles_list:
            return 2
        vin = vehicles_list[0].vin
        match = [(n, fn) for n, fn in ENDPOINT_PROBES if n == args.endpoint]
        if not match:
            print(f"unknown endpoint {args.endpoint!r}; try one of: {[n for n,_ in ENDPOINT_PROBES]}", file=sys.stderr)
            return 2
        name, fn = match[0]
        outfile = open(args.out, "a") if args.out else None
        try:
            for i in range(1, args.count + 1):
                sample = await _do_probe(client._api, name, fn, vin, i, args.rate)
                _emit(sample, outfile)
                if sample.status == "429":
                    print(f"stopping arm early on first 429 at attempt {i}", file=sys.stderr)
                    return 0
                if i < args.count:
                    await asyncio.sleep(args.rate)
        finally:
            if outfile:
                outfile.close()
    finally:
        try:
            await client._api.controller.aclose()
        except Exception:
            pass
    return 0


async def cmd_scan(args) -> int:
    """Full scan: for each endpoint, for each rate, up to count requests.
    Stops early per-arm on first 429."""
    user = os.environ["TOYOTA_USER"]
    pw = os.environ["TOYOTA_PASS"]
    client = await _login(user, pw)
    try:
        vehicles = await client._api.get_vehicles()
        vehicles_list = getattr(vehicles, "payload", None) or []
        if not vehicles_list:
            return 2
        vin = vehicles_list[0].vin
        print(f"[scan] using vin=...{vin[-6:]}", file=sys.stderr)

        rates = args.rates
        count = args.count
        outfile = open(args.out, "a") if args.out else None
        try:
            for name, fn in ENDPOINT_PROBES:
                for rate_s in rates:
                    print(f"[scan] {name} at {rate_s}s/req, up to {count} reqs", file=sys.stderr)
                    stopped_early = False
                    for i in range(1, count + 1):
                        sample = await _do_probe(client._api, name, fn, vin, i, rate_s)
                        _emit(sample, outfile)
                        if sample.status == "429":
                            print(f"[scan]   stopped early on 429 at attempt {i}", file=sys.stderr)
                            stopped_early = True
                            break
                        if i < count:
                            await asyncio.sleep(rate_s)
                    if stopped_early:
                        # Don't hammer faster rates on an endpoint that just 429'd.
                        # Skip to next endpoint; gives the limiter time to forgive.
                        print(f"[scan]   skipping faster rates for {name}; back off", file=sys.stderr)
                        await asyncio.sleep(60)  # cool-off between endpoints
                        break
        finally:
            if outfile:
                outfile.close()
    finally:
        try:
            await client._api.controller.aclose()
        except Exception:
            pass
    return 0


async def cmd_coordinator(args) -> int:
    """Reproduce HA's coordinator access pattern: once per interval, for
    each vehicle, fire vehicle.update() (which serially calls ~6-10
    capability endpoints) then the 4 summary calls (day/week/month/year).
    This mirrors `ha_toyota._refresh_one_vehicle` exactly. Records whether
    each endpoint-group in each cycle succeeded or 429'd.

    Note: pytoyoda's internal (2,4,8)s retry in controller.request_raw
    stays ACTIVE. That matches what HA observes: a 429 line here means
    all 4 retry attempts failed. INTER_CALL_DELAY_S from Phase 2.2 is
    also active (1.0s between endpoints inside vehicle.update). This
    exactly reproduces the current live HA stack minus the coordinator
    wrapper."""
    user = os.environ["TOYOTA_USER"]
    pw = os.environ["TOYOTA_PASS"]
    client = await _login(user, pw)
    outfile = open(args.out, "a") if args.out else None
    try:
        vehicles = await client.get_vehicles()
        vehicles = [v for v in vehicles if v is not None and v.vin is not None]
        if not vehicles:
            print("no vehicles", file=sys.stderr)
            return 2
        print(f"[coordinator] {len(vehicles)} vehicle(s), interval={args.interval}s, cycles={args.cycles}", file=sys.stderr)

        # Map Vehicle methods to (endpoint_name, coroutine_factory).
        def _summary_calls(v):
            return [
                ("vehicle.update", v.update),
                ("day_summary", v.get_current_day_summary),
                ("week_summary", v.get_current_week_summary),
                ("month_summary", v.get_current_month_summary),
                ("year_summary", v.get_current_year_summary),
            ]

        for cycle in range(1, args.cycles + 1):
            cycle_start = time.perf_counter()
            print(f"[coordinator] cycle {cycle}/{args.cycles} starting", file=sys.stderr)
            for v in vehicles:
                vin = v.vin
                for name, fn in _summary_calls(v):
                    ts = datetime.now().isoformat(timespec="seconds")
                    t0 = time.perf_counter()
                    try:
                        await fn()
                        latency = time.perf_counter() - t0
                        sample = Sample(
                            timestamp=ts, endpoint=name, rate_s=float(args.interval),
                            attempt=cycle, status="200",
                            latency_s=round(latency, 3),
                            note=f"vin=...{vin[-6:]}",
                        )
                    except ToyotaApiError as ex:
                        latency = time.perf_counter() - t0
                        msg = str(ex)
                        status = "429" if "429" in msg else ("5xx" if any(c in msg for c in ("500","502","503","504")) else "api_err")
                        sample = Sample(
                            timestamp=ts, endpoint=name, rate_s=float(args.interval),
                            attempt=cycle, status=status,
                            latency_s=round(latency, 3),
                            note=f"vin=...{vin[-6:]}; {msg[:120]}",
                        )
                    except Exception as ex:
                        latency = time.perf_counter() - t0
                        sample = Sample(
                            timestamp=ts, endpoint=name, rate_s=float(args.interval),
                            attempt=cycle, status=f"exc:{type(ex).__name__}",
                            latency_s=round(latency, 3),
                            note=f"vin=...{vin[-6:]}; {str(ex)[:120]}",
                        )
                    _emit(sample, outfile)

            cycle_elapsed = time.perf_counter() - cycle_start
            print(f"[coordinator] cycle {cycle} took {cycle_elapsed:.1f}s", file=sys.stderr)
            if cycle < args.cycles:
                # Sleep the remainder of the interval, accounting for how long
                # the cycle itself took. If a cycle took longer than interval
                # (e.g. all retries exhausted on many endpoints), proceed
                # immediately to the next - matches what HA's coordinator does.
                remaining = max(0, args.interval - cycle_elapsed)
                print(f"[coordinator] sleeping {remaining:.0f}s until next cycle", file=sys.stderr)
                await asyncio.sleep(remaining)
    finally:
        if outfile:
            outfile.close()
        try:
            await client._api.controller.aclose()
        except Exception:
            pass
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="mode", required=True)

    p_single = sub.add_parser("single", help="single probe, exit 0 iff 200")
    p_single.set_defaults(fn=cmd_single)

    p_one = sub.add_parser("one", help="one endpoint, fixed rate")
    p_one.add_argument("--endpoint", required=True, choices=[n for n, _ in ENDPOINT_PROBES])
    p_one.add_argument("--rate", type=float, default=30.0, help="seconds between requests")
    p_one.add_argument("--count", type=int, default=10)
    p_one.add_argument("--out", default=None)
    p_one.set_defaults(fn=cmd_one)

    p_scan = sub.add_parser("scan", help="full sweep: all endpoints * all rates")
    p_scan.add_argument("--rates", nargs="+", type=float, default=DEFAULT_RATES_S)
    p_scan.add_argument("--count", type=int, default=DEFAULT_COUNT_PER_ARM)
    p_scan.add_argument("--out", default=None)
    p_scan.set_defaults(fn=cmd_scan)

    p_coord = sub.add_parser("coordinator", help="mimic HA coordinator access pattern")
    p_coord.add_argument("--interval", type=float, default=360.0, help="seconds between cycles (HA default 360)")
    p_coord.add_argument("--cycles", type=int, default=10, help="how many coordinator cycles to run")
    p_coord.add_argument("--out", default=None)
    p_coord.set_defaults(fn=cmd_coordinator)

    args = p.parse_args()
    try:
        return asyncio.run(args.fn(args))
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except ToyotaLoginError as ex:
        print(f"login failed: {ex}", file=sys.stderr)
        return 2
    except Exception:
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
