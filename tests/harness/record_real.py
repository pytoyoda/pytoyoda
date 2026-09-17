"""Capture real Toyota API responses for use in the memory-leak harness.

Drives a real pytoyoda login + poll against the user's live Toyota account.
Intercepts every request the Controller makes and writes the raw response body
to `tests/harness/fixtures/real/<slug>.json`. The HTTPS mock server will prefer
these real fixtures over the generic unit-test fixtures when present, so the
harness can replay real Toyota content without hitting the live API.

Security:
- Reads credentials from TOYOTA_EMAIL + TOYOTA_PASSWORD env vars, never takes
  them from argv (which would leak into shell history).
- Writes responses to `fixtures/real/`, which is gitignored (see .gitignore).
- Never writes access/refresh tokens to disk. Auth-flow responses are recorded
  with the token fields scrubbed.

Run once, save, replay forever. Toyota rate-limits, so do not drive this in a
loop. One invocation == one sweep of ~12 requests.

Usage:
    TOYOTA_EMAIL=... TOYOTA_PASSWORD=... \\
    .venv-harness/bin/python -m tests.harness.record_real
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import date, timedelta
from pathlib import Path

from loguru import logger as _logger
_logger.remove()

from pytoyoda import MyT
from pytoyoda import controller as controller_mod


FIXTURES_REAL = Path(__file__).resolve().parent / "fixtures" / "real"


def _slugify(method: str, path: str) -> str:
    """Turn a request into a filename-safe slug."""
    # Strip query string + leading slash
    base = path.split("?", 1)[0].lstrip("/")
    # Collapse path separators and parametric segments
    slug = re.sub(r"[^a-zA-Z0-9_.-]", "_", base)
    return f"{method.lower()}_{slug}"


def _scrub_token_response(body: bytes) -> bytes:
    """Replace bearer tokens with harness placeholders so nothing sensitive
    lands on disk. Applies to /access_token responses only."""
    try:
        data = json.loads(body)
    except Exception:
        return body
    if not isinstance(data, dict):
        return body
    scrubbed = dict(data)
    for k in ("access_token", "refresh_token", "id_token"):
        if k in scrubbed:
            scrubbed[k] = f"<scrubbed-{k}>"
    return json.dumps(scrubbed, indent=2).encode()


async def run() -> None:
    email = os.environ.get("TOYOTA_EMAIL")
    password = os.environ.get("TOYOTA_PASSWORD")
    if not email or not password:
        raise SystemExit("Set TOYOTA_EMAIL and TOYOTA_PASSWORD env vars")

    FIXTURES_REAL.mkdir(parents=True, exist_ok=True)

    # Monkey-patch Controller.request_raw to record responses.
    # We wrap the ORIGINAL implementation (post-#1, the branch has the persistent
    # client) so we exercise the real network stack.
    original = controller_mod.Controller.request_raw
    recorded: dict[str, int] = {}

    async def recording_request_raw(
        self,
        method: str,
        endpoint: str,
        vin=None,
        body=None,
        params=None,
        headers=None,
    ):
        response = await original(self, method, endpoint, vin, body, params, headers)
        slug = _slugify(method, endpoint)
        FIXTURES_REAL.joinpath(f"{slug}.json").write_bytes(response.content)
        recorded[slug] = recorded.get(slug, 0) + 1
        print(f"  recorded {method} {endpoint}  -> {slug}.json ({len(response.content)}B)")
        return response

    controller_mod.Controller.request_raw = recording_request_raw

    # Similarly patch the auth flow's client.post / client.get to save the
    # authenticate / authorize / access_token responses. These bypass
    # request_raw because they go through the hishel AsyncCacheClient directly.
    import httpx
    original_request = httpx.AsyncClient.request

    async def recording_httpx_request(self, method, url, **kwargs):
        response = await original_request(self, method, url, **kwargs)
        url_str = str(url)
        if any(tok in url_str for tok in ("/authenticate", "/authorize", "/access_token")):
            slug = _slugify(
                method, url_str.split("://", 1)[-1].split("/", 1)[-1].split("?", 1)[0]
            )
            payload = response.content
            if "/access_token" in url_str:
                payload = _scrub_token_response(payload)
            FIXTURES_REAL.joinpath(f"auth_{slug}.json").write_bytes(payload)
            print(
                f"  recorded AUTH {method} {url_str[:80]}...  -> auth_{slug}.json"
                f" ({len(payload)}B)"
            )
        return response

    httpx.AsyncClient.request = recording_httpx_request

    client = MyT(username=email, password=password)

    print("== login ==")
    await client.login()

    print("== get_vehicles ==")
    vehicles = await client.get_vehicles()

    for v in vehicles or []:
        print(f"== vehicle update (vin=...{(v.vin or '')[-6:]}) ==")
        await v.update()
        print("== daily/weekly/monthly/yearly summaries ==")
        await v.get_current_day_summary()
        await v.get_current_week_summary()
        await v.get_current_month_summary()
        await v.get_current_year_summary()

    # Clean shutdown so we don't leak the pooled client.
    await client.aclose()

    print()
    print(f"Recorded {sum(recorded.values())} request(s) across {len(recorded)} endpoint(s).")
    print(f"Written to: {FIXTURES_REAL}")
    print("Fixture slugs seen:")
    for slug, n in sorted(recorded.items()):
        print(f"  {slug}: {n} call(s)")


if __name__ == "__main__":
    asyncio.run(run())
