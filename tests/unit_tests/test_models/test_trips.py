"""Tests for the trips endpoint models."""

from __future__ import annotations

from pytoyoda.models.endpoints.trips import _SummaryBaseModel


def test_summary_base_model_parses_partial_payload() -> None:
    """Real Toyota /v1/trips responses only contain 4 of the 11 summary fields.

    Regression for pytoyoda/ha_toyota#278: without default=None on every field,
    ``CustomEndpointBaseModel``'s ``invalid_to_none`` wrapper silently converted
    the whole summary to None when any required field was missing, masking
    real API data.
    """
    partial = {
        "length": 237614,
        "duration": 13702,
        "averageSpeed": 62.43,
        "fuelConsumption": 15912.0,
    }

    summary = _SummaryBaseModel.model_validate(partial)

    assert summary.length == 237614
    assert summary.duration == 13702
    assert summary.average_speed == 62.43
    assert summary.fuel_consumption == 15912.0
    # Fields absent from the payload must be None, not reject the whole model.
    assert summary.duration_idle is None
    assert summary.countries is None
    assert summary.max_speed is None
    assert summary.length_overspeed is None
    assert summary.duration_overspeed is None
    assert summary.length_highway is None
    assert summary.duration_highway is None
