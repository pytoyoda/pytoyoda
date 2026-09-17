"""Toyota Connected Services API - Trips Models."""

from __future__ import annotations

from datetime import date, datetime  # noqa : TC003
from typing import Any
from uuid import UUID  # noqa : TC003

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel
from pytoyoda.utils.helpers import add_with_none
from pytoyoda.utils.models import CustomEndpointBaseModel


class _SummaryBaseModel(CustomEndpointBaseModel):
    # Every field is optional. The Toyota /v1/trips endpoint currently returns
    # only {length, duration, averageSpeed, fuelConsumption} at the histogram
    # summary level; the rest (durationIdle, countries, min/max speed,
    # overspeed/highway breakdowns) are not present in the payload. Without
    # defaults here, the CustomEndpointBaseModel wrapper silently converts the
    # whole summary to None on every field it can't fill, masking real data.
    length: int | None = None
    duration: int | None = None
    duration_idle: int | None = Field(alias="durationIdle", default=None)
    countries: list[str] | None = None
    max_speed: float | None = Field(alias="maxSpeed", default=None)
    average_speed: float | None = Field(alias="averageSpeed", default=None)
    length_overspeed: int | None = Field(alias="lengthOverspeed", default=None)
    duration_overspeed: int | None = Field(alias="durationOverspeed", default=None)
    length_highway: int | None = Field(alias="lengthHighway", default=None)
    duration_highway: int | None = Field(alias="durationHighway", default=None)
    fuel_consumption: float | None = Field(
        alias="fuelConsumption", default=None
    )  # Electric cars might not use fuel. Milliliters.

    def __add__(self, other: _SummaryBaseModel) -> _SummaryBaseModel:
        """Add together two SummaryBaseModel's.

        Returns a new instance rather than mutating ``self`` (Python convention
        for ``__add__`` vs ``__iadd__``). Every numeric field is declared
        ``int | None`` / ``float | None``, so either operand may be ``None`` on
        any given day. Use ``add_with_none`` throughout and guard list/max/avg
        ops so a single missing day doesn't crash the whole weekly summary.

        Args:
            other (_SummaryBaseModel): to be added

        """
        result = self.model_copy(deep=True)
        if other is None:
            return result
        result.length = add_with_none(result.length, other.length)
        result.duration = add_with_none(result.duration, other.duration)
        result.duration_idle = add_with_none(result.duration_idle, other.duration_idle)
        if other.countries:
            if result.countries is None:
                result.countries = []
            result.countries.extend(
                x for x in other.countries if x not in result.countries
            )
        if result.max_speed is None:
            result.max_speed = other.max_speed
        elif other.max_speed is not None:
            result.max_speed = max(result.max_speed, other.max_speed)
        if result.average_speed is None:
            result.average_speed = other.average_speed
        elif other.average_speed is not None:
            result.average_speed = (result.average_speed + other.average_speed) / 2.0
        result.length_overspeed = add_with_none(
            result.length_overspeed, other.length_overspeed
        )
        result.duration_overspeed = add_with_none(
            result.duration_overspeed, other.duration_overspeed
        )
        result.length_highway = add_with_none(
            result.length_highway, other.length_highway
        )
        result.duration_highway = add_with_none(
            result.duration_highway, other.duration_highway
        )
        result.fuel_consumption = add_with_none(
            result.fuel_consumption, other.fuel_consumption
        )
        return result


class _SummaryModel(_SummaryBaseModel):
    start_lat: float | None = Field(alias="startLat")
    start_lon: float | None = Field(alias="startLon")
    start_ts: datetime | None = Field(alias="startTs")
    end_lat: float | None = Field(alias="endLat")
    end_lon: float | None = Field(alias="endLon")
    end_ts: datetime | None = Field(alias="endTs")
    night_trip: bool | None = Field(alias="nightTrip")


class _CoachingMsgParamModel(CustomEndpointBaseModel):
    name: str | None
    unit: str | None
    value: int | None


class _BehaviourModel(CustomEndpointBaseModel):
    ts: datetime | None
    type: str | None = None
    coaching_msg_params: list[_CoachingMsgParamModel] | None = Field(
        alias="coachingMsgParams", default=None
    )


class _ScoresModel(CustomEndpointBaseModel):
    global_: int | None = Field(..., alias="global")
    acceleration: int | None = None
    braking: int | None = None
    advice: int | None = None
    constant_speed: int | None = Field(alias="constantSpeed", default=None)


class _HDCModel(CustomEndpointBaseModel):
    ev_time: int | None = Field(alias="evTime", default=None)
    ev_distance: int | None = Field(alias="evDistance", default=None)
    charge_time: int | None = Field(alias="chargeTime", default=None)
    charge_dist: int | None = Field(alias="chargeDist", default=None)
    eco_time: int | None = Field(alias="ecoTime", default=None)
    eco_dist: int | None = Field(alias="ecoDist", default=None)
    power_time: int | None = Field(alias="powerTime", default=None)
    power_dist: int | None = Field(alias="powerDist", default=None)

    def __add__(self, other: _HDCModel) -> _HDCModel:
        """Add together two HDCModel's.

        Returns a new instance rather than mutating ``self``.

        Args:
            other (_HDCModel): to be added

        """
        result = self.model_copy(deep=True)
        if other is None:
            return result
        result.ev_time = add_with_none(result.ev_time, other.ev_time)
        result.ev_distance = add_with_none(result.ev_distance, other.ev_distance)
        result.charge_time = add_with_none(result.charge_time, other.charge_time)
        result.charge_dist = add_with_none(result.charge_dist, other.charge_dist)
        result.eco_time = add_with_none(result.eco_time, other.eco_time)
        result.eco_dist = add_with_none(result.eco_dist, other.eco_dist)
        result.power_time = add_with_none(result.power_time, other.power_time)
        result.power_dist = add_with_none(result.power_dist, other.power_dist)
        return result


class _RouteModel(CustomEndpointBaseModel):
    lat: float | None = Field(repr=False)
    lon: float | None
    overspeed: bool | None
    highway: bool | None
    index_in_points: int | None = Field(alias="indexInPoints")
    mode: int | None = None
    is_ev: bool | None = Field(alias="isEv")


class _TripModel(CustomEndpointBaseModel):
    id: UUID | None
    category: int | None
    summary: _SummaryModel | None
    scores: _ScoresModel | None = None
    behaviours: list[_BehaviourModel] | None = None
    hdc: _HDCModel | None = None
    route: list[_RouteModel] | None = None


class _HistogramModel(CustomEndpointBaseModel):
    year: int | None
    month: int | None
    day: int | None
    summary: _SummaryBaseModel | None
    scores: _ScoresModel | None = None
    hdc: _HDCModel | None = None


class _SummaryItemModel(CustomEndpointBaseModel):
    year: int | None
    month: int | None
    summary: _SummaryBaseModel | None
    scores: _ScoresModel | None = None
    hdc: _HDCModel | None = None
    histograms: list[_HistogramModel]


class _PaginationModel(CustomEndpointBaseModel):
    limit: int | None
    offset: int | None
    previous_offset: Any | None = Field(alias="previousOffset", default=None)
    next_offset: int | None = Field(alias="nextOffset", default=None)
    current_page: int | None = Field(alias="currentPage")
    total_count: int | None = Field(alias="totalCount")
    page_count: int | None = Field(alias="pageCount")


class _SortedByItemModel(CustomEndpointBaseModel):
    field: str | None
    order: str | None


class _MetadataModel(CustomEndpointBaseModel):
    pagination: _PaginationModel | None
    sorted_by: list[_SortedByItemModel] | None = Field(alias="sortedBy")


class TripsModel(CustomEndpointBaseModel):
    r"""Model representing trips data.

    Attributes:
        from_date (date): The start date of the trips.
        to_date (date): The end date of the trips.
        trips (list[_TripModel]): The list of trips.
        summary (Optional[list[_SummaryItemModel]], optional): The summary of the trips.
            Defaults to None.
        metadata (_MetadataModel): The metadata of the trips.
        route (Optional[_RouteModel], optional): The route of the trips.
            Defaults to None.

    """

    from_date: date | None = Field(..., alias="from")
    to_date: date | None = Field(..., alias="to")
    trips: list[_TripModel] | None
    summary: list[_SummaryItemModel] | None = None
    metadata: _MetadataModel | None = Field(..., alias="_metadata")
    route: _RouteModel | None = None


class TripsResponseModel(StatusModel):
    r"""Model representing a trips response.

    Inherits from StatusModel.

    Attributes:
        payload (Optional[TripsModel], optional): The trips payload.
            Defaults to None.

    """

    payload: TripsModel | None = None
