"""Local HTTPS mock server for the leak harness.

Uses the standard library only (http.server + ssl). Serves every endpoint
pytoyoda hits during a full poll, reading payloads from the project's existing
unit-test JSON fixtures. Reproduces the original leak hypothesis mechanism
because httpx.AsyncClient() will do a real TLS handshake against this server.

Why not respx: respx intercepts at the transport layer BEFORE the SSL
handshake. The hypothesis for the memory leak is that repeated
SSLContext construction / load_verify_locations calls accumulate state
that Python doesn't reclaim cleanly when the event loop is short-lived.
With respx we never exercise that path. With this server we do.
"""

from __future__ import annotations

import json
import random
import socket
import ssl
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import jwt as pyjwt


CERTS_DIR = Path(__file__).resolve().parent / "certs"
CERT_PATH = CERTS_DIR / "cert.pem"
KEY_PATH = CERTS_DIR / "key.pem"
FIXTURES = Path(__file__).resolve().parent.parent / "unit_tests" / "data"
FIXTURES_REAL = Path(__file__).resolve().parent / "fixtures" / "real"


def _fake_jwt() -> str:
    """JWT containing a uuid claim. pytoyoda decodes id_token and reads .uuid."""
    return pyjwt.encode(
        {"uuid": "harness-uuid-0001", "sub": "harness", "exp": 9999999999},
        "harness-secret-not-verified",
        algorithm="HS256",
    )


def _load(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text())


def _load_real_or(name: str, fallback_fixture: str) -> Any:
    """Prefer a recorded real-response fixture; fall back to the project's
    generic unit-test fixture if no real one is present.

    `name` is the slug filename written by record_real.py (e.g.
    `get_v1_location.json`). `fallback_fixture` is the generic fixture path
    under tests/unit_tests/data/.
    """
    real = FIXTURES_REAL / name
    if real.exists():
        return json.loads(real.read_text())
    return _load(fallback_fixture)


def _load_real_raw(name: str) -> bytes | None:
    """Return raw bytes of a real fixture if present, else None."""
    real = FIXTURES_REAL / name
    if real.exists():
        return real.read_bytes()
    return None


def _bodies() -> dict[str, Any]:
    return {
        "authenticate": {
            "tokenId": "harness-token-id-0001",
            "successUrl": "/",
            "realm": "/",
        },
        "tokens": {
            "access_token": _fake_jwt(),
            "refresh_token": _fake_jwt(),
            "id_token": _fake_jwt(),
            "token_type": "Bearer",
            "expires_in": 1800,
        },
        "vehicles": _load_real_or("get_v2_vehicle_guid.json", "v2_vehicleguid.json"),
        "location": _load_real_or("get_v1_location.json", "v1_location_ok.json"),
        "health": _load_real_or(
            "get_v1_vehiclehealth_status.json", "v1_vehicle_health_ok.json"
        ),
        "remote": _load_real_or(
            "get_v1_global_remote_status.json", "v1_global_remote_status.json"
        ),
        "electric": _load_real_or(
            "get_v1_global_remote_electric_status.json",
            "v1_global_remote_electric_status.json",
        ),
        "telemetry": _load_real_or("get_v3_telemetry.json", "v3_telemetry.json"),
        "notifications": _load_real_or(
            "get_v2_notification_history.json", "v2_notification.json"
        ),
        "service_history": _load_real_or(
            "get_v1_servicehistory_vehicle_summary.json", "v1_service_history.json"
        ),
        "climate_status": {"payload": None, "status": {"messages": []}},
        "climate_settings": {"payload": None, "status": {"messages": []}},
        "trips": _load_real_or("get_v1_trips.json", "v1_trips.json"),
    }


# Pre-compute once; reused across requests so we don't re-parse fixtures each time.
_BODIES_CACHE: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Per-VIN cache-expiry simulator (for smart-strategy TDD, 2026-04-25+).
#
# Models the Toyota two-stage protocol we discovered on 2026-04-24:
#   - GET  /v1/global/remote/status         reads the cache (429+APIGW-403 if cold/stale)
#   - POST /v1/global/remote/refresh-status wakes the car (200/returnCode 000000),
#                                            cache populates if the car responds
#
# Simulator invariants (per VIN):
#   - cache_populated_at: when the cache was last refreshed by a successful POST
#                         (None = never been populated; cold cache)
#   - cache_ttl_s:        how long after cache_populated_at the GET keeps returning 200
#   - responsive:         POST populates cache iff this is True
#                         (False simulates "deeply parked" car: POST 200, cache no-op)
#   - layer1_failure:     POST returns returnCode != "000000"
#                         (simulates "this vehicle does not support refresh-status")
#   - get_429_probability: stochastic 429 on GET even when cache is fresh
#                         (matches the empirical observation that 429s leak through)
#   - last_post_at:       wall-clock; tests assert spacing
#   - post_call_count, get_call_count: cumulative per-VIN
#
# Tests pre-populate the registry, then point the pytoyoda client at the harness URL.
# Real time advances. Tests that need to skip ahead use Sim.advance_clock(seconds);
# the simulator uses its own monotonic clock so wall-clock tests don't have to wait.
# ---------------------------------------------------------------------------


@dataclass
class VehicleSim:
    """Per-VIN simulation state."""

    vin: str
    responsive: bool = True
    layer1_failure: bool = False
    cache_ttl_s: float = 30 * 60  # 30 minutes; matches Addendum 4 default
    get_429_probability: float = 0.0
    cache_populated_at: float | None = None
    last_post_at: float | None = None
    post_call_count: int = 0
    get_call_count: int = 0
    # Each successful repopulation bumps the occurrence_date by this many seconds
    # off the simulator's clock baseline so tests can assert "advanced".
    occurrence_date_baseline: float = field(default_factory=time.monotonic)
    occurrence_date_offset: float = 0.0

    def is_cache_fresh_at(self, now: float) -> bool:
        if self.cache_populated_at is None:
            return False
        return (now - self.cache_populated_at) < self.cache_ttl_s

    def occurrence_date(self) -> str:
        """ISO-8601 timestamp; advances every time POST repopulates the cache."""
        # Map sim seconds onto a real datetime anchored at "now" minus offset
        # so the value is plausible (UTC, recent) while remaining test-determinant.
        anchor = datetime.now(tz=timezone.utc).timestamp()
        return (
            datetime.fromtimestamp(
                anchor - self.occurrence_date_offset, tz=timezone.utc
            )
            .isoformat()
            .replace("+00:00", "Z")
        )


class _Registry:
    """Module-global per-VIN registry. Tests interact via SIM."""

    def __init__(self) -> None:
        self._sims: dict[str, VehicleSim] = {}
        self._default_factory = lambda vin: VehicleSim(vin=vin)
        self._lock = threading.Lock()
        self._rng = random.Random(0)

    def reset(self) -> None:
        with self._lock:
            self._sims.clear()
            self._rng = random.Random(0)

    def configure(self, vin: str, **kwargs: Any) -> VehicleSim:
        with self._lock:
            sim = self._sims.get(vin)
            if sim is None:
                sim = self._default_factory(vin)
                self._sims[vin] = sim
            for k, v in kwargs.items():
                setattr(sim, k, v)
            return sim

    def get(self, vin: str) -> VehicleSim:
        with self._lock:
            sim = self._sims.get(vin)
            if sim is None:
                sim = self._default_factory(vin)
                self._sims[vin] = sim
            return sim

    def all(self) -> dict[str, VehicleSim]:
        with self._lock:
            return dict(self._sims)

    def maybe_force_429(self, sim: VehicleSim) -> bool:
        if sim.get_429_probability <= 0:
            return False
        with self._lock:
            return self._rng.random() < sim.get_429_probability


SIM = _Registry()


def _vin_from_path_or_body(path: str, body_bytes: bytes | None) -> str:
    """Resolve the VIN this request targets.

    /status: VIN comes from the X-VIN header (handled separately - we cannot get
    headers here). Fallback to a default 'DEFAULT' VIN if nothing else.

    /refresh-status: VIN is in the JSON body.
    """
    if body_bytes:
        try:
            data = json.loads(body_bytes)
            if isinstance(data, dict) and "vin" in data:
                return str(data["vin"])
        except (json.JSONDecodeError, ValueError):
            pass
    return "DEFAULT"


_APIGW_403_BODY = json.dumps({"code": "APIGW-403", "message": "Unauthorized"}).encode()


def _build_status_response(sim: VehicleSim) -> bytes:
    """Render the /status fixture body but with the simulator's occurrence_date.

    We deep-copy lazily by re-loading the JSON each call (cheap; happens only on
    cache-fresh hits) so we don't mutate _BODIES_CACHE."""
    raw = _load_real_or(
        "get_v1_global_remote_status.json", "v1_global_remote_status.json"
    )
    payload = raw.get("payload") or {}
    payload["occurrenceDate"] = sim.occurrence_date()
    raw["payload"] = payload
    return json.dumps(raw).encode()


def _route(
    method: str,
    path: str,
    headers: dict[str, str] | None = None,
    body_bytes: bytes | None = None,
) -> tuple[int, dict[str, str], bytes | None]:
    """Return (status, headers_dict, body_bytes_or_None) for a given request."""
    global _BODIES_CACHE
    if _BODIES_CACHE is None:
        _BODIES_CACHE = _bodies()
    b = _BODIES_CACHE
    headers = headers or {}

    # Strip query string; route by path + method
    base_path = path.split("?", 1)[0]

    # Auth flow
    if method == "POST" and "/authenticate" in base_path:
        return 200, {"Content-Type": "application/json"}, json.dumps(b["authenticate"]).encode()
    if method == "GET" and "/authorize" in base_path:
        return (
            302,
            {"Location": "com.toyota.oneapp:/oauth2Callback?code=harness-auth-code"},
            None,
        )
    if method == "POST" and "/access_token" in base_path:
        return 200, {"Content-Type": "application/json"}, json.dumps(b["tokens"]).encode()

    # --- Smart-strategy endpoints (simulator-backed) ---
    # POST /v1/global/remote/refresh-status (must precede /status check below)
    if method == "POST" and "/v1/global/remote/refresh-status" in base_path:
        vin = _vin_from_path_or_body(path, body_bytes)
        sim = SIM.get(vin)
        now = time.monotonic()
        sim.last_post_at = now
        sim.post_call_count += 1
        if sim.layer1_failure:
            return (
                200,
                {"Content-Type": "application/json"},
                json.dumps(
                    {
                        "status": {"messages": []},
                        "payload": {"returnCode": "010001"},
                    }
                ).encode(),
            )
        if sim.responsive:
            sim.cache_populated_at = now
            sim.occurrence_date_offset = 0.0
        return (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "status": {"messages": []},
                    "payload": {"returnCode": "000000"},
                }
            ).encode(),
        )

    # GET /v1/global/remote/status (cache-expiry semantics)
    if method == "GET" and "/v1/global/remote/status" in base_path:
        vin = headers.get("vin") or headers.get("VIN") or "DEFAULT"
        sim = SIM.get(vin)
        sim.get_call_count += 1
        now = time.monotonic()
        if not sim.is_cache_fresh_at(now):
            return 429, {"Content-Type": "application/json"}, _APIGW_403_BODY
        if SIM.maybe_force_429(sim):
            return 429, {"Content-Type": "application/json"}, _APIGW_403_BODY
        return 200, {"Content-Type": "application/json"}, _build_status_response(sim)

    # API data endpoints (other GETs)
    routing = [
        ("/v2/vehicle/guid", "vehicles"),
        ("/v1/location", "location"),
        ("/v1/vehiclehealth/status", "health"),
        ("/v1/global/remote/electric/status", "electric"),
        ("/v1/global/remote/climate-status", "climate_status"),
        ("/v1/global/remote/climate-settings", "climate_settings"),
        ("/v3/telemetry", "telemetry"),
        ("/v2/notification/history", "notifications"),
        ("/v1/servicehistory", "service_history"),
        ("/v1/trips", "trips"),
    ]
    for prefix, body_key in routing:
        if method == "GET" and prefix in base_path:
            return 200, {"Content-Type": "application/json"}, json.dumps(b[body_key]).encode()

    return 404, {"Content-Type": "application/json"}, json.dumps({"error": "harness: unmocked endpoint", "path": base_path, "method": method}).encode()


class _Handler(BaseHTTPRequestHandler):
    """Minimal handler that silences default logging and dispatches on path."""

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        # Silent by default; stdlib http.server is very noisy otherwise.
        pass

    def _send(self, status: int, headers: dict[str, str], body: bytes | None) -> None:
        self.send_response(status)
        if body is not None:
            headers.setdefault("Content-Length", str(len(body)))
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        if body is not None:
            self.wfile.write(body)

    def _request_headers(self) -> dict[str, str]:
        return {k: v for k, v in self.headers.items()}

    def do_GET(self) -> None:  # noqa: N802
        status, headers, body = _route(
            "GET", self.path, headers=self._request_headers(), body_bytes=None
        )
        self._send(status, headers, body)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0") or "0")
        body_bytes = self.rfile.read(length) if length > 0 else b""
        status, headers, body = _route(
            "POST",
            self.path,
            headers=self._request_headers(),
            body_bytes=body_bytes,
        )
        self._send(status, headers, body)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class HarnessServer:
    """Start a TLS HTTP server bound to 127.0.0.1:<auto> in a background thread."""

    def __init__(self, port: int | None = None) -> None:
        self.port = port or _find_free_port()
        self.host = "127.0.0.1"
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        return f"https://{self.host}:{self.port}"

    def start(self) -> None:
        httpd = ThreadingHTTPServer((self.host, self.port), _Handler)
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(certfile=str(CERT_PATH), keyfile=str(KEY_PATH))
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
        self._httpd = httpd
        self._thread = threading.Thread(target=httpd.serve_forever, daemon=True, name="harness-https")
        self._thread.start()
        # Wait for listener to be reachable
        for _ in range(50):
            try:
                with socket.create_connection((self.host, self.port), timeout=0.2):
                    return
            except OSError:
                time.sleep(0.05)
        raise RuntimeError("harness server failed to become reachable")

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def __enter__(self) -> HarnessServer:
        self.start()
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.stop()
