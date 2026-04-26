"""Drop-in variant of record_real.py that serializes every `asyncio.gather`.

Purpose: test the burst-rate-limit hypothesis. If pytoyoda currently fires ~20
parallel requests per poll (2 vehicles x ~10 endpoints via vehicle.update()),
a burst-aware Toyota limiter may trip much more readily than a sustained-rate
one. This script patches the asyncio scheduler so every gather becomes
sequential, optionally with an inter-call delay.

If this completes cleanly while record_real.py 429s, burst is validated as the
dominant cause. Remediation #2 (serialize gather) should then be prioritised.
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import os
import re
import sys
from pathlib import Path


INTER_CALL_DELAY_S = float(os.environ.get("TOYOTA_INTER_CALL_DELAY_S", "0.2"))


async def _sequential_gather(*awaitables, return_exceptions=False):
    """Replacement for asyncio.gather that awaits tasks one at a time.

    Adds an optional small sleep between calls (TOYOTA_INTER_CALL_DELAY_S env,
    default 200 ms) to give Toyota's rate limiter some headroom.
    """
    results = []
    for idx, aw in enumerate(awaitables):
        if idx > 0 and INTER_CALL_DELAY_S > 0:
            await asyncio.sleep(INTER_CALL_DELAY_S)
        try:
            results.append(await aw)
        except Exception as e:  # noqa: BLE001
            if return_exceptions:
                results.append(e)
            else:
                raise
    return results


# IMPORTANT: patch asyncio.gather before importing pytoyoda so even
# `from asyncio import gather` bindings inside pytoyoda pick up the override.
asyncio.gather = _sequential_gather  # type: ignore[assignment]

# Also update any imports of asyncio.gather that happened before this script
# ran. There shouldn't be any at this point (we haven't imported pytoyoda yet),
# but patch defensively by rewriting references in any module that already
# imported it.
for mod in list(sys.modules.values()):
    if mod is None or not hasattr(mod, "__dict__"):
        continue
    try:
        for attr_name in list(mod.__dict__.keys()):
            if attr_name == "gather":
                val = mod.__dict__.get(attr_name)
                if inspect.iscoroutinefunction(val) or callable(val):
                    if getattr(val, "__module__", "") == "asyncio":
                        mod.__dict__[attr_name] = _sequential_gather
    except Exception:
        continue


# Now run the original recorder logic. We re-use record_real.py's implementation
# so we don't drift between the two paths.
from tests.harness.record_real import run  # noqa: E402


if __name__ == "__main__":
    print(f"== running with sequential gather (delay={INTER_CALL_DELAY_S}s) ==")
    asyncio.run(run())
