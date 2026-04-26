"""Cadence policy guard for the test harness.

Encodes Rule 2 from the rate-limit-remediation plan, Addendum 5 (2026-04-25):

- Mock API: any cadence allowed. Tests can run thousands of cycles in seconds.
- Real Toyota API: probe scripts must respect the integration's natural floor.
  The coordinator interval is configurable but >= 5 minutes (B10 lower bound).

The point: prevent ourselves (and anyone reading these test scripts) from
overloading Toyota's API with sweep loops that have no business existing.
The mock harness is the right place for sweeps; real-API hits are explicit
one-off probes only.

Usage in a probe script:

    from tests.harness.cadence import (
        REAL_API_MIN_INTERVAL_S,
        assert_cadence_ok,
        set_real_api_mode,
    )

    set_real_api_mode(True)            # explicit opt-in
    assert_cadence_ok(my_interval_s)   # raises CadenceViolation if too fast
"""

from __future__ import annotations


# Coordinator floor from Track B B10. The integration cannot poll faster than
# this against the real API; probe scripts must match or exceed it.
REAL_API_MIN_INTERVAL_S: int = 5 * 60

# Track B B10 default. Probes that mimic the integration's actual cadence
# should use this rather than the floor.
REAL_API_DEFAULT_INTERVAL_S: int = 6 * 60


_real_api_mode: bool = False


class CadenceViolation(RuntimeError):
    """Raised when a probe script attempts to hit the real API faster than the
    coordinator floor. This is a hard stop, not a warning, because the
    consequences (potential API hardening by Toyota) outlive the script."""


def set_real_api_mode(enabled: bool) -> None:
    """Switch between mock-API mode (default, no constraint) and real-API mode
    (cadence floor enforced). Must be called explicitly; default is mock."""
    global _real_api_mode
    _real_api_mode = enabled


def is_real_api_mode() -> bool:
    return _real_api_mode


def assert_cadence_ok(interval_s: float) -> None:
    """Raise CadenceViolation if real-API mode is on and the interval is below
    the floor. No-op in mock mode (the harness can poll arbitrarily fast).

    Args:
        interval_s: The polling/loop interval the script intends to use,
            in seconds.
    """
    if not _real_api_mode:
        return
    if interval_s < REAL_API_MIN_INTERVAL_S:
        raise CadenceViolation(
            f"Real-API cadence violation: interval={interval_s}s is below the "
            f"floor of {REAL_API_MIN_INTERVAL_S}s. Either raise the interval, "
            f"or run against the mock harness (set_real_api_mode(False))."
        )
