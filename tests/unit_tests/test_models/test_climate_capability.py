"""Tests for Vehicle._climate_capable() - widened BEV/PHEV detection.

Regression coverage for #192: some vehicles (notably BEVs like the BZ4X, and
certain PHEVs) advertise climate support only through
``extended_capabilities`` rather than through ``features.climate_start_engine``.
Both `climate_settings` and `climate_status` endpoints must be gated on the
same widened check so BEV/PHEV accounts are not silently starved of climate
data while ICE/HEV accounts keep working exactly as before.
"""

from __future__ import annotations

from types import SimpleNamespace

from pytoyoda.models.vehicle import Vehicle


def _build_vehicle(
    features: SimpleNamespace, extended_capabilities: SimpleNamespace
) -> Vehicle:
    """Build a bare Vehicle instance with the given feature/capability stubs."""
    v = Vehicle.__new__(Vehicle)
    v._vehicle_info = SimpleNamespace(
        vin="TESTVIN0000000001",
        features=features,
        extended_capabilities=extended_capabilities,
    )
    return v


def test_climate_capable_via_legacy_feature_flag() -> None:
    """ICE/HEV vehicles keep working via features.climate_start_engine."""
    vehicle = _build_vehicle(
        features=SimpleNamespace(climate_start_engine=True),
        extended_capabilities=SimpleNamespace(),
    )

    assert vehicle._climate_capable() is True


def test_climate_capable_via_extended_climate_capable() -> None:
    """BEV without features.climate_start_engine but climate_capable=True."""
    vehicle = _build_vehicle(
        features=SimpleNamespace(climate_start_engine=False),
        extended_capabilities=SimpleNamespace(climate_capable=True),
    )

    assert vehicle._climate_capable() is True


def test_climate_capable_via_econnect_climate_capable() -> None:
    """PHEV advertising climate only via econnect_climate_capable."""
    vehicle = _build_vehicle(
        features=SimpleNamespace(climate_start_engine=False),
        extended_capabilities=SimpleNamespace(econnect_climate_capable=True),
    )

    assert vehicle._climate_capable() is True


def test_climate_capable_via_remote_engine_start_stop() -> None:
    """Vehicle advertising climate only via remote_engine_start_stop."""
    vehicle = _build_vehicle(
        features=SimpleNamespace(climate_start_engine=False),
        extended_capabilities=SimpleNamespace(remote_engine_start_stop=True),
    )

    assert vehicle._climate_capable() is True


def test_climate_not_capable_when_no_flags_set() -> None:
    """Vehicle with none of the climate flags is not climate-capable."""
    vehicle = _build_vehicle(
        features=SimpleNamespace(climate_start_engine=False),
        extended_capabilities=SimpleNamespace(
            climate_capable=False,
            econnect_climate_capable=False,
            remote_engine_start_stop=False,
        ),
    )

    assert vehicle._climate_capable() is False


def test_climate_not_capable_when_features_and_capabilities_missing() -> None:
    """Missing features/extended_capabilities objects entirely: no crash."""
    vehicle = Vehicle.__new__(Vehicle)
    vehicle._vehicle_info = SimpleNamespace(vin="TESTVIN0000000001")

    assert vehicle._climate_capable() is False
