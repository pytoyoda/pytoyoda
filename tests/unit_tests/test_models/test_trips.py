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


def _make_full() -> _SummaryBaseModel:
    return _SummaryBaseModel.model_validate(
        {
            "length": 100,
            "duration": 60,
            "averageSpeed": 50.0,
            "fuelConsumption": 10.0,
        }
    )


def test_summary_base_model_add_handles_none_fields_on_other() -> None:
    """``self.length += other.length`` used to crash when other.length was None.

    ``__add__`` mutates ``self`` in place; verify numeric fields missing on
    ``other`` leave ``self`` unchanged rather than raising TypeError.
    """
    full = _make_full()
    sparse = _SummaryBaseModel.model_validate({"length": 50})

    result = full + sparse
    assert result.length == 150
    assert result.duration == 60  # sparse had no duration -> full's value kept
    assert result.fuel_consumption == 10.0
    assert result.average_speed == 50.0


def test_summary_base_model_add_handles_none_fields_on_self() -> None:
    """Same crash but from ``self`` side: None += 50 previously raised too."""
    sparse = _SummaryBaseModel.model_validate({"length": 50})
    full = _make_full()

    result = sparse + full
    # length: 50 + 100 = 150, others seed from full since self side was None.
    assert result.length == 150
    assert result.duration == 60
    assert result.average_speed == 50.0
    assert result.fuel_consumption == 10.0


def test_summary_base_model_add_handles_both_none() -> None:
    """Both sides missing a field -> result stays None, no crash."""
    a = _SummaryBaseModel.model_validate({"length": 10})
    b = _SummaryBaseModel.model_validate({"length": 20})

    result = a + b
    assert result.length == 30
    assert result.duration is None
    assert result.average_speed is None
    assert result.fuel_consumption is None
    assert result.countries is None


def test_summary_base_model_add_noop_when_other_is_none() -> None:
    """Adding None returns self unchanged (predates this fix, kept as a guard)."""
    summary = _SummaryBaseModel.model_validate({"length": 42})
    assert (summary + None).length == 42
