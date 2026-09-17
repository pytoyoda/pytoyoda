"""Three-variant poll driver for the leak measurement.

Usage:
    python -m tests.harness.driver --mode=post-283 --duration-min=120 --poll-interval-s=30 --out=results/A.csv
    python -m tests.harness.driver --mode=pre-283  --duration-min=120 --poll-interval-s=30 --out=results/B.csv
    python -m tests.harness.driver --mode=post-1   --duration-min=120 --poll-interval-s=30 --out=results/C.csv

Each invocation runs as a single subprocess (required for fair comparison - OpenSSL
and asyncio state is process-scoped; running multiple variants in the same process
cross-contaminates).

Modes:
- post-283: current code. Single event loop via asyncio.run, all pytoyoda methods
  directly awaited. This is what's on nledenyi/ha_toyota:bug/memory-leak-direct-await.
- pre-283: reproduces the leaking wrapper. Every pytoyoda coroutine is wrapped in
  asyncio.new_event_loop() / run_until_complete / loop.close(), mimicking ha_toyota's
  _run_pytoyoda_sync behaviour. NOTE: we do this directly inside the main thread
  here, not via an executor, because the leak mechanism is the loop-per-call, not
  the thread.
- post-1: same as post-283 BUT monkey-patches pytoyoda.controller.Controller to
  hold a single persistent httpx.AsyncClient on the instance, reusing it across
  requests. This is the "remediation #1" candidate.

Each poll simulates what ha_toyota does per refresh:
  1. client.login() (first iteration only; subsequent polls reuse token)
  2. client.get_vehicles()
  3. for each vehicle: vehicle.update()
  4. for each vehicle: 4 summary calls (day/week/month/year)

Under mocks, all network is trapped by respx - no real Toyota contact.
"""

from __future__ import annotations

import argparse
import asyncio
import gc
import signal
import sys
import time
from contextlib import asynccontextmanager, contextmanager
from datetime import date, timedelta
from pathlib import Path

import httpx

# Silence pytoyoda's loguru firehose - it allocates for every log line.
from loguru import logger as _logger
_logger.remove()

# Top-level pytoyoda imports are safe: Controller reads const_mod.* values at
# __init__ time, not at import time. install_harness_patches() updates the
# module's attributes in place, so any MyT() built after the patches see the
# patched URLs.
from pytoyoda import MyT
from pytoyoda import controller as controller_mod

from tests.harness.mock_server import HarnessServer, CERT_PATH
from tests.harness.sampler import Sampler


def install_harness_patches(base_url: str, ca_path: Path) -> None:
    """Redirect pytoyoda's hardcoded URLs to the local server and pin CA.

    Must run BEFORE any MyT() is instantiated. Controller stores URL constants
    as httpx.URL instances on __init__, so late patching after an instance
    exists has no effect on that instance.

    We also monkey-patch httpx.AsyncClient.__init__ to default verify=<ca_path>.
    This reproduces the load_verify_locations blocking-call path from PR #171
    while trusting our self-signed cert.
    """
    from pytoyoda import const as const_mod
    from pytoyoda import controller as controller_mod_inner

    patched_urls = {
        "API_BASE_URL": base_url,
        "ACCESS_TOKEN_URL": f"{base_url}/v2/oauth2/realms/root/realms/tme/access_token",
        "AUTHENTICATE_URL": (
            f"{base_url}/json/realms/root/realms/tme/authenticate"
            "?authIndexType=service&authIndexValue=oneapp"
        ),
        "AUTHORIZE_URL": (
            f"{base_url}/oauth2/realms/root/realms/tme/authorize"
            "?client_id=oneapp&scope=openid+profile+write"
            "&response_type=code&redirect_uri=com.toyota.oneapp:/oauth2Callback"
            "&code_challenge=plain&code_challenge_method=plain"
        ),
    }
    # Patch both the const module AND the controller module, because controller
    # does `from .const import API_BASE_URL, ...` (binds at controller import).
    for name, value in patched_urls.items():
        setattr(const_mod, name, value)
        setattr(controller_mod_inner, name, value)

    # Force every AsyncClient to trust our self-signed CA. We intentionally pass
    # verify=<path-to-cert> rather than verify=False so that the full SSL setup
    # path (load_verify_locations, SSLContext construction) is still executed;
    # that is precisely the code PR #171 was trying to avoid blocking on.
    original_init = httpx.AsyncClient.__init__

    def patched_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        kwargs.setdefault("verify", str(ca_path))
        return original_init(self, *args, **kwargs)

    httpx.AsyncClient.__init__ = patched_init


# -------------------------------------------------------------------------
# Mode: pre-283 wrapper that reproduces ha_toyota's _run_pytoyoda_sync pattern
# -------------------------------------------------------------------------

def _run_pytoyoda_sync(coro):
    """Reproduction of ha_toyota's pre-PR-283 wrapper.

    Creates a fresh event loop, runs one coroutine to completion, closes the loop.
    This is the leak mechanism we want to observe.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# -------------------------------------------------------------------------
# Mode: post-1 persistent httpx.AsyncClient
# -------------------------------------------------------------------------

@contextmanager
def patched_controller_for_persistent_client():
    """Monkey-patch Controller.request_raw to use a single AsyncClient per Controller.

    Upstream:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.request(...)

    Patched:
        # lazy-init once, reuse forever
        if self._persistent_client is None:
            self._persistent_client = httpx.AsyncClient(timeout=self._timeout)
        response = await self._persistent_client.request(...)

    Caller is responsible for calling aclose() on the client if it cares.
    We don't, because the harness process exits between tests.
    """
    import httpx
    from http import HTTPStatus

    original = controller_mod.Controller.request_raw

    async def patched_request_raw(
        self,
        method: str,
        endpoint: str,
        vin: str | None = None,
        body=None,
        params=None,
        headers=None,
    ):
        valid_methods = ("GET", "POST", "PUT", "DELETE")
        if method not in valid_methods:
            from pytoyoda.exceptions import ToyotaInternalError
            raise ToyotaInternalError(
                f"Invalid request method: {method}. Must be one of {valid_methods}"
            )
        if not self._is_token_valid():
            await self._update_token()
        request_headers = self._prepare_headers(vin, headers)

        if getattr(self, "_persistent_client", None) is None:
            self._persistent_client = httpx.AsyncClient(timeout=self._timeout)

        response = await self._persistent_client.request(
            method,
            f"{self._api_base_url}{endpoint}",
            headers=request_headers,
            json=body,
            params=params,
            follow_redirects=True,
        )

        if response.status_code in (HTTPStatus.OK, HTTPStatus.ACCEPTED):
            return response
        from pytoyoda.exceptions import ToyotaApiError
        raise ToyotaApiError(
            f"Request Failed. {response.status_code}, {response.text}."
        )

    controller_mod.Controller.request_raw = patched_request_raw
    try:
        yield
    finally:
        controller_mod.Controller.request_raw = original


# -------------------------------------------------------------------------
# The poll workload (what ha_toyota does per coordinator refresh)
# -------------------------------------------------------------------------

async def _one_poll_async(client: MyT) -> int:
    """Run a single refresh cycle. Returns the number of pytoyoda calls made."""
    calls = 0
    vehicles = await client.get_vehicles()
    calls += 1
    today = date.today()
    month_start = today.replace(day=1)
    week_start = today - timedelta(days=today.weekday())
    year_start = today.replace(month=1, day=1)
    for v in vehicles or []:
        await v.update()
        calls += 1
        await v.get_current_day_summary()
        calls += 1
        await v.get_current_week_summary()
        calls += 1
        await v.get_current_month_summary()
        calls += 1
        await v.get_current_year_summary()
        calls += 1
    _ = today, month_start, week_start, year_start  # unused locals placate pyflakes
    return calls


async def _login_once(client: MyT) -> None:
    await client.login()


def _poll_via_wrapper(client: MyT) -> int:
    """The pre-283 pattern: every coroutine gets its own fresh event loop."""
    calls = 0
    vehicles = _run_pytoyoda_sync(client.get_vehicles())
    calls += 1
    for v in vehicles or []:
        _run_pytoyoda_sync(v.update())
        calls += 1
        _run_pytoyoda_sync(v.get_current_day_summary())
        calls += 1
        _run_pytoyoda_sync(v.get_current_week_summary())
        calls += 1
        _run_pytoyoda_sync(v.get_current_month_summary())
        calls += 1
        _run_pytoyoda_sync(v.get_current_year_summary())
        calls += 1
    return calls


# -------------------------------------------------------------------------
# Main entry
# -------------------------------------------------------------------------

def _make_client() -> MyT:
    return MyT(username="harness@example.invalid", password="harness-password")


async def _run_mode_post283(duration_s: float, poll_interval_s: float, progress_path: Path) -> dict:
    """Single event loop, direct awaits. Current behaviour (post PR #283)."""
    client = _make_client()
    await _login_once(client)
    return await _run_loop_single_loop(
        client, duration_s, poll_interval_s, progress_path, mode_label="post-283"
    )


async def _run_mode_post1(duration_s: float, poll_interval_s: float, progress_path: Path) -> dict:
    """post-283 + monkey-patched persistent AsyncClient."""
    with patched_controller_for_persistent_client():
        client = _make_client()
        await _login_once(client)
        return await _run_loop_single_loop(
            client, duration_s, poll_interval_s, progress_path, mode_label="post-1"
        )


def _run_mode_pre283_sync(duration_s: float, poll_interval_s: float, progress_path: Path) -> dict:
    """Pre-283 wrapper pattern. Each call gets a fresh event loop."""
    client = _make_client()
    _run_pytoyoda_sync(client.login())
    start = time.monotonic()
    poll_count = 0
    call_count = 0
    last_progress = 0.0
    while time.monotonic() - start < duration_s:
        poll_start = time.monotonic()
        poll_count += 1
        call_count += _poll_via_wrapper(client)
        elapsed = time.monotonic() - start
        if elapsed - last_progress >= 60.0:
            last_progress = elapsed
            _write_progress(progress_path, poll_count, call_count, elapsed, duration_s, "pre-283")
        elapsed_in_poll = time.monotonic() - poll_start
        sleep_for = max(0.0, poll_interval_s - elapsed_in_poll)
        time.sleep(sleep_for)
    return {"polls": poll_count, "calls": call_count}


async def _run_loop_single_loop(
    client: MyT,
    duration_s: float,
    poll_interval_s: float,
    progress_path: Path,
    mode_label: str,
) -> dict:
    start = time.monotonic()
    poll_count = 0
    call_count = 0
    last_progress = 0.0
    while time.monotonic() - start < duration_s:
        poll_start = time.monotonic()
        poll_count += 1
        call_count += await _one_poll_async(client)
        elapsed = time.monotonic() - start
        if elapsed - last_progress >= 60.0:
            last_progress = elapsed
            _write_progress(progress_path, poll_count, call_count, elapsed, duration_s, mode_label)
        elapsed_in_poll = time.monotonic() - poll_start
        sleep_for = max(0.0, poll_interval_s - elapsed_in_poll)
        if sleep_for > 0:
            await asyncio.sleep(sleep_for)
    return {"polls": poll_count, "calls": call_count}


def _write_progress(path: Path, polls: int, calls: int, elapsed: float, duration: float, mode: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"mode: {mode}\n"
        f"polls_done: {polls}\n"
        f"calls_done: {calls}\n"
        f"elapsed_s: {elapsed:.0f}\n"
        f"duration_s: {duration:.0f}\n"
        f"progress: {100 * elapsed / duration:.1f}%\n"
        f"updated_ts: {time.time():.0f}\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["post-283", "pre-283", "post-1"], required=True)
    parser.add_argument("--duration-min", type=float, required=True)
    parser.add_argument("--poll-interval-s", type=float, default=30.0)
    parser.add_argument("--sample-interval-s", type=float, default=10.0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    duration_s = args.duration_min * 60
    progress_path = args.out.with_suffix(".progress.txt")
    summary_path = args.out.with_suffix(".summary.txt")

    sampler = Sampler(csv_path=args.out, interval_s=args.sample_interval_s)

    # Aggressive GC baseline - we want the leak signal, not warmup allocations.
    gc.collect()

    def _graceful_exit(signum, frame):
        sampler.stop()
        sys.exit(130)

    signal.signal(signal.SIGINT, _graceful_exit)
    signal.signal(signal.SIGTERM, _graceful_exit)

    with HarnessServer() as server:
        install_harness_patches(server.base_url, CERT_PATH)
        sampler.start()
        try:
            if args.mode == "pre-283":
                result = _run_mode_pre283_sync(duration_s, args.poll_interval_s, progress_path)
            elif args.mode == "post-283":
                result = asyncio.run(_run_mode_post283(duration_s, args.poll_interval_s, progress_path))
            elif args.mode == "post-1":
                result = asyncio.run(_run_mode_post1(duration_s, args.poll_interval_s, progress_path))
            else:
                raise ValueError(f"unknown mode: {args.mode}")
            snapshot_txt = sampler.take_snapshot(top_n=20)
        finally:
            sampler.stop()
    summary_path.write_text(
        f"mode: {args.mode}\n"
        f"duration_min: {args.duration_min}\n"
        f"poll_interval_s: {args.poll_interval_s}\n"
        f"sample_interval_s: {args.sample_interval_s}\n"
        f"polls: {result['polls']}\n"
        f"pytoyoda_calls: {result['calls']}\n"
        f"csv: {args.out}\n\n"
        f"=== tracemalloc top 20 at end ===\n{snapshot_txt}\n"
    )
    print(f"done. mode={args.mode} polls={result['polls']} calls={result['calls']}")
    print(f"csv: {args.out}")
    print(f"summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
