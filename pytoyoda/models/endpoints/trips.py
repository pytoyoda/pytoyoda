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
    length: int | None
    duration: int | None
    duration_idle: int | None = Field(alias="durationIdle")
    countries: list[str] | None
    max_speed: float | None = Field(alias="maxSpeed")
    average_speed: float | None = Field(alias="averageSpeed")
    length_overspeed: int | None = Field(alias="lengthOverspeed")
    duration_overspeed: int | None = Field(alias="durationOverspeed")
    length_highway: int | None = Field(alias="lengthHighway")
    duration_highway: int | None = Field(alias="durationHighway")
    fuel_consumption: float | None = Field(
        alias="fuelConsumption", default=None
    )  # Electric cars might not use fuel. Milliliters.

    def __add__(self, other: _SummaryBaseModel) -> _SummaryBaseModel:
        """Add together two SummaryBaseModel's.

        Handles Min/Max/Average fields correctly.

        Args:
            other (_SummaryBaseModel): to be added

        """
        if other is not None:
            self.length += other.length
            self.duration += other.duration
            self.duration_idle += other.duration_idle
            self.countries.extend(x for x in other.countries if x not in self.countries)
            self.max_speed = max(self.max_speed, other.max_speed)
            self.average_speed = (self.average_speed + other.average_speed) / 2.0
            self.length_overspeed += other.length_overspeed
            self.duration_overspeed += other.duration_overspeed
            self.length_highway += other.length_highway
            self.duration_highway += other.duration_highway
            self.fuel_consumption = add_with_none(
                self.fuel_consumption, other.fuel_consumption
            )

        return self


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

        Handles Min/Max/Average fields correctly.

        Args:
            other (_SummaryBaseModel): to be added

        """
        if other is not None:
            self.ev_time = add_with_none(self.ev_time, other.ev_time)
            self.ev_distance = add_with_none(self.ev_distance, other.ev_distance)
            self.charge_time = add_with_none(self.charge_time, other.charge_time)
            self.charge_dist = add_with_none(self.charge_dist, other.charge_dist)
            self.eco_time = add_with_none(self.eco_time, other.eco_time)
            self.eco_dist = add_with_none(self.eco_dist, other.eco_dist)
            self.power_time = add_with_none(self.power_time, other.power_time)
            self.power_dist = add_with_none(self.power_dist, other.power_dist)

        return self


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
