"""Tests for the cadence policy guard."""

from __future__ import annotations

import pytest

from tests.harness.cadence import (
    REAL_API_DEFAULT_INTERVAL_S,
    REAL_API_MIN_INTERVAL_S,
    CadenceViolation,
    assert_cadence_ok,
    is_real_api_mode,
    set_real_api_mode,
)


@pytest.fixture(autouse=True)
def reset_mode():
    """Ensure each test starts in mock mode and ends in mock mode."""
    set_real_api_mode(False)
    yield
    set_real_api_mode(False)


def test_mock_mode_allows_any_interval():
    set_real_api_mode(False)
    assert_cadence_ok(0)  # no exception
    assert_cadence_ok(0.001)
    assert_cadence_ok(99999)


def test_real_api_mode_blocks_below_floor():
    set_real_api_mode(True)
    assert is_real_api_mode()
    with pytest.raises(CadenceViolation):
        assert_cadence_ok(1.0)
    with pytest.raises(CadenceViolation):
        assert_cadence_ok(REAL_API_MIN_INTERVAL_S - 1)


def test_real_api_mode_allows_at_or_above_floor():
    set_real_api_mode(True)
    assert_cadence_ok(REAL_API_MIN_INTERVAL_S)  # exactly floor: OK
    assert_cadence_ok(REAL_API_DEFAULT_INTERVAL_S)
    assert_cadence_ok(REAL_API_MIN_INTERVAL_S * 10)


def test_default_is_mock_mode():
    """A fresh import / fresh test must default to mock mode."""
    assert not is_real_api_mode()
