"""Contract tests for the cache-expiry simulator added to mock_server.py.

These run in seconds against the in-process HTTPS harness, exercising the
two-stage protocol we discovered on 2026-04-24 (POST /refresh-status to wake
the car, GET /status to read the cache). This is the foundation of the
smart-strategy TDD work; pytoyoda's `refresh_vehicle_status()` and ha_toyota's
decision tree will be tested against the same simulator.

Run via:
    poetry run pytest tests/harness/test_cache_expiry_contract.py -v
"""

from __future__ import annotations

import json
import ssl

import httpx
import pytest

from tests.harness.mock_server import SIM, HarnessServer


@pytest.fixture()
def server():
    SIM.reset()
    s = HarnessServer()
    s.start()
    try:
        yield s
    finally:
        s.stop()


@pytest.fixture()
def client(server):
    # Mirror harness driver: trust the self-signed cert
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with httpx.Client(base_url=server.base_url, verify=ctx, timeout=5.0) as c:
        yield c


def _get_status(client, vin: str) -> httpx.Response:
    return client.get("/v1/global/remote/status", headers={"vin": vin})


def _post_refresh(client, vin: str) -> httpx.Response:
    return client.post(
        "/v1/global/remote/refresh-status",
        json={"deviceId": "harness", "deviceType": "Android", "guid": "g", "vin": vin},
    )


# ---------------------------------------------------------------------------
# Core cache-expiry contract
# ---------------------------------------------------------------------------


def test_cold_cache_get_returns_429_apigw403(client):
    """A VIN that has never had a successful POST returns 429+APIGW-403 on GET."""
    SIM.configure("VIN-COLD")
    r = _get_status(client, "VIN-COLD")
    assert r.status_code == 429
    body = r.json()
    assert body == {"code": "APIGW-403", "message": "Unauthorized"}


def test_post_then_get_succeeds_when_responsive(client):
    """Responsive car: POST populates cache, GET succeeds."""
    SIM.configure("VIN-OK", responsive=True)
    assert _get_status(client, "VIN-OK").status_code == 429  # cold
    post = _post_refresh(client, "VIN-OK")
    assert post.status_code == 200
    assert post.json()["payload"]["returnCode"] == "000000"
    get = _get_status(client, "VIN-OK")
    assert get.status_code == 200
    assert "occurrenceDate" in get.json()["payload"]


def test_post_does_not_populate_when_unresponsive(client):
    """Silent car (Aygo case): POST returns 200/000000 but cache stays cold.

    This is the ground-truth simulation we need for soft-disable testing.
    """
    SIM.configure("VIN-SILENT", responsive=False)
    assert _post_refresh(client, "VIN-SILENT").status_code == 200
    # Cache still cold afterward
    assert _get_status(client, "VIN-SILENT").status_code == 429


def test_layer1_failure_returns_non_zero_returncode(client):
    """Vehicle that doesn't support refresh-status (Layer 1 reject case)."""
    SIM.configure("VIN-LEGACY", layer1_failure=True)
    r = _post_refresh(client, "VIN-LEGACY")
    assert r.status_code == 200
    assert r.json()["payload"]["returnCode"] != "000000"


def test_cache_expires_after_ttl(client):
    """Once cache_ttl_s elapses, subsequent GETs flip back to 429."""
    SIM.configure("VIN-TTL", cache_ttl_s=0.05)  # 50 ms TTL for fast test
    _post_refresh(client, "VIN-TTL")
    assert _get_status(client, "VIN-TTL").status_code == 200
    import time as _t

    _t.sleep(0.1)
    assert _get_status(client, "VIN-TTL").status_code == 429


def test_stochastic_429_when_cache_fresh(client):
    """Deterministic stochastic 429 (seeded RNG) on top of fresh cache.

    Mimics the empirical observation that 429s leak through even when the
    cache should be hot (the layer-7 quota under the cache).
    """
    SIM.configure("VIN-FLAKY", get_429_probability=1.0)
    _post_refresh(client, "VIN-FLAKY")
    # With probability=1.0, every GET should 429 even though cache is fresh
    for _ in range(5):
        r = _get_status(client, "VIN-FLAKY")
        assert r.status_code == 429


def test_per_vin_isolation(client):
    """Two VINs share no state. POSTing one does not warm the other."""
    SIM.configure("VIN-A", responsive=True)
    SIM.configure("VIN-B", responsive=True)
    _post_refresh(client, "VIN-A")
    assert _get_status(client, "VIN-A").status_code == 200
    assert _get_status(client, "VIN-B").status_code == 429


def test_call_counts_tracked(client):
    """Tests can introspect simulator state (post_call_count, get_call_count)."""
    sim = SIM.configure("VIN-COUNT", responsive=True)
    _post_refresh(client, "VIN-COUNT")
    _get_status(client, "VIN-COUNT")
    _get_status(client, "VIN-COUNT")
    assert sim.post_call_count == 1
    assert sim.get_call_count == 2


def test_occurrence_date_is_iso8601_z(client):
    """occurrenceDate is rendered with the trailing Z (matches real API shape)."""
    SIM.configure("VIN-DATE", responsive=True)
    _post_refresh(client, "VIN-DATE")
    body = _get_status(client, "VIN-DATE").json()
    occ = body["payload"]["occurrenceDate"]
    assert occ.endswith("Z")
    # Must be parseable by a simple consumer
    from datetime import datetime

    datetime.fromisoformat(occ.replace("Z", "+00:00"))
