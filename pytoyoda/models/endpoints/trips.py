"""Toyota Connected Services API - Trips Models."""

from __future__ import annotations

from datetime import date, datetime  # noqa : TC003
from typing import Any, Optional
from uuid import UUID  # noqa : TC003

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel
from pytoyoda.utils.helpers import add_with_none
from pytoyoda.utils.models import CustomEndpointBaseModel


class _SummaryBaseModel(CustomEndpointBaseModel):
    length: Optional[int]
    duration: Optional[int]
    duration_idle: Optional[int] = Field(alias="durationIdle")
    countries: Optional[list[str]]
    max_speed: Optional[float] = Field(alias="maxSpeed")
    average_speed: Optional[float] = Field(alias="averageSpeed")
    length_overspeed: Optional[int] = Field(alias="lengthOverspeed")
    duration_overspeed: Optional[int] = Field(alias="durationOverspeed")
    length_highway: Optional[int] = Field(alias="lengthHighway")
    duration_highway: Optional[int] = Field(alias="durationHighway")
    fuel_consumption: Optional[float] = Field(
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
    start_lat: Optional[float] = Field(alias="startLat")
    start_lon: Optional[float] = Field(alias="startLon")
    start_ts: Optional[datetime] = Field(alias="startTs")
    end_lat: Optional[float] = Field(alias="endLat")
    end_lon: Optional[float] = Field(alias="endLon")
    end_ts: Optional[datetime] = Field(alias="endTs")
    night_trip: Optional[bool] = Field(alias="nightTrip")


class _CoachingMsgParamModel(CustomEndpointBaseModel):
    name: Optional[str]
    unit: Optional[str]
    value: Optional[int]


class _BehaviourModel(CustomEndpointBaseModel):
    ts: Optional[datetime]
    type: Optional[str] = None
    coaching_msg_params: Optional[list[_CoachingMsgParamModel]] = Field(
        alias="coachingMsgParams", default=None
    )


class _ScoresModel(CustomEndpointBaseModel):
    global_: Optional[int] = Field(..., alias="global")
    acceleration: Optional[int] = None
    braking: Optional[int] = None
    advice: Optional[int] = None
    constant_speed: Optional[int] = Field(alias="constantSpeed", default=None)


class _HDCModel(CustomEndpointBaseModel):
    ev_time: Optional[int] = Field(alias="evTime", default=None)
    ev_distance: Optional[int] = Field(alias="evDistance", default=None)
    charge_time: Optional[int] = Field(alias="chargeTime", default=None)
    charge_dist: Optional[int] = Field(alias="chargeDist", default=None)
    eco_time: Optional[int] = Field(alias="ecoTime", default=None)
    eco_dist: Optional[int] = Field(alias="ecoDist", default=None)
    power_time: Optional[int] = Field(alias="powerTime", default=None)
    power_dist: Optional[int] = Field(alias="powerDist", default=None)

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
    lat: Optional[float] = Field(repr=False)
    lon: Optional[float]
    overspeed: Optional[bool]
    highway: Optional[bool]
    index_in_points: Optional[int] = Field(alias="indexInPoints")
    mode: Optional[int] = None
    is_ev: Optional[bool] = Field(alias="isEv")


class _TripModel(CustomEndpointBaseModel):
    id: Optional[UUID]
    category: Optional[int]
    summary: Optional[_SummaryModel]
    scores: Optional[_ScoresModel] = None
    behaviours: Optional[list[_BehaviourModel]] = None
    hdc: Optional[_HDCModel] = None
    route: Optional[list[_RouteModel]] = None


class _HistogramModel(CustomEndpointBaseModel):
    year: Optional[int]
    month: Optional[int]
    day: Optional[int]
    summary: Optional[_SummaryBaseModel]
    scores: Optional[_ScoresModel] = None
    hdc: Optional[_HDCModel] = None


class _SummaryItemModel(CustomEndpointBaseModel):
    year: Optional[int]
    month: Optional[int]
    summary: Optional[_SummaryBaseModel]
    scores: Optional[_ScoresModel] = None
    hdc: Optional[_HDCModel] = None
    histograms: list[_HistogramModel]


class _PaginationModel(CustomEndpointBaseModel):
    limit: Optional[int]
    offset: Optional[int]
    previous_offset: Optional[Any] = Field(alias="previousOffset", default=None)
    next_offset: Optional[int] = Field(alias="nextOffset", default=None)
    current_page: Optional[int] = Field(alias="currentPage")
    total_count: Optional[int] = Field(alias="totalCount")
    page_count: Optional[int] = Field(alias="pageCount")


class _SortedByItemModel(CustomEndpointBaseModel):
    field: Optional[str]
    order: Optional[str]


class _MetadataModel(CustomEndpointBaseModel):
    pagination: Optional[_PaginationModel]
    sorted_by: Optional[list[_SortedByItemModel]] = Field(alias="sortedBy")


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

    from_date: Optional[date] = Field(..., alias="from")
    to_date: Optional[date] = Field(..., alias="to")
    trips: Optional[list[_TripModel]]
    summary: Optional[list[_SummaryItemModel]] = None
    metadata: Optional[_MetadataModel] = Field(..., alias="_metadata")
    route: Optional[_RouteModel] = None


class TripsResponseModel(StatusModel):
    r"""Model representing a trips response.

    Inherits from StatusModel.

    Attributes:
        payload (Optional[TripsModel], optional): The trips payload.
            Defaults to None.

    """

    payload: Optional[TripsModel] = None
