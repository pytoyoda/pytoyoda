"""Model for Trip Summaries."""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Type, TypeVar, Union

from pydantic import BaseModel, computed_field

from pytoyoda.const import (
    KILOMETERS_UNIT,
    MILES_UNIT,
    ML_GAL_FACTOR,
    ML_L_FACTOR,
    MPG_FACTOR,
)
from pytoyoda.models.endpoints.trips import _TripModel
from pytoyoda.utils.conversions import convert_distance
from pytoyoda.utils.models import CustomAPIBaseModel

T = TypeVar(
    "T",
    bound=Union[_TripModel, bool],
)


class TripPositions(BaseModel):
    """Latitude and longitude."""

    lat: Optional[float]
    lon: Optional[float]


class TripLocations(BaseModel):
    """Trip locations."""

    start: Optional[TripPositions]
    end: Optional[TripPositions]


class Trip(CustomAPIBaseModel[Type[T]]):
    """Base class of Daily, Weekly, Monthly, Yearly summary."""

    def __init__(
        self,
        trip: _TripModel,
        metric: bool,
        **kwargs,
    ):
        """Initialise Class.

        Args:
            trip (_TripModel, required): Contains all information regarding the trip
            metric (bool, required): Report in Metric or Imperial
            **kwargs: Additional keyword arguments passed to the parent class

        """
        data = {
            "trip": trip,
            "metric": metric,
        }
        super().__init__(data=data, **kwargs)  # type: ignore[reportArgumentType, arg-type]
        self._trip = trip
        self._distance_unit: str = KILOMETERS_UNIT if metric else MILES_UNIT

    @computed_field  # type: ignore[prop-decorator]
    @property
    def locations(self) -> Optional[TripLocations]:
        """Trip locations.

        Returns:
            TripLocations: Latitude and longitude for trip start and end points

        """
        if self._trip.summary:
            return TripLocations(
                start=TripPositions(
                    lat=self._trip.summary.start_lat, lon=self._trip.summary.start_lon
                ),
                end=TripPositions(
                    lat=self._trip.summary.end_lat, lon=self._trip.summary.end_lon
                ),
            )
        else:
            return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def start_time(self) -> Optional[datetime]:
        """Start time.

        Returns:
            datetime: Start time of trip

        """
        return self._trip.summary.start_ts if self._trip.summary else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def end_time(self) -> Optional[datetime]:
        """End time.

        Returns:
            datetime: End time of trip

        """
        return self._trip.summary.end_ts if self._trip.summary else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def duration(self) -> Optional[timedelta]:
        """The total time driving.

        Returns:
            timedelta: The amount of time driving

        """
        return (
            timedelta(seconds=self._trip.summary.duration)
            if self._trip.summary and self._trip.summary.duration
            else None
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def distance(self) -> Optional[float]:
        """The total distance covered.

        Returns:
            float: Distance covered in the selected metric

        """
        if self._trip.summary and self._trip.summary.length:
            return convert_distance(
                self._distance_unit, KILOMETERS_UNIT, self._trip.summary.length / 1000.0
            )
        else:
            return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ev_duration(self) -> Optional[timedelta]:
        """The total time driving using EV.

        Returns:
            timedelta: The amount of time driving using EV or None if not supported

        """
        return (
            timedelta(seconds=self._trip.hdc.ev_time)
            if self._trip.hdc and self._trip.hdc.ev_time
            else None
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ev_distance(self) -> Optional[float]:
        """The total time distance driven using EV.

        Returns:
            timedelta: The distance driven using EV in selected metric
                or None if not supported.

        """
        return (
            convert_distance(
                self._distance_unit,
                KILOMETERS_UNIT,
                self._trip.hdc.ev_distance / 1000.0,
            )
            if self._trip.hdc and self._trip.hdc.ev_distance
            else None
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def fuel_consumed(self) -> float:
        """The total amount of fuel consumed.

        Returns:
            float: The total amount of fuel consumed in liters if metric or gallons

        """
        if self._trip.summary and self._trip.summary.fuel_consumption:
            return (
                round(self._trip.summary.fuel_consumption / ML_L_FACTOR, 3)
                if self._distance_unit
                else round(self._trip.summary.fuel_consumption / ML_GAL_FACTOR, 3)
            )

        return 0.0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def average_fuel_consumed(self) -> float:
        """The average amount of fuel consumed.

        Returns:
            float: The average amount of fuel consumed in l/100km if metric or mpg

        """
        if (
            self._trip.summary
            and self._trip.summary.fuel_consumption
            and self._trip.summary.length
        ):
            avg_fuel_consumed = (
                self._trip.summary.fuel_consumption / self._trip.summary.length
            ) * 100
            return (
                round(avg_fuel_consumed, 3)
                if self._distance_unit
                else round(MPG_FACTOR / avg_fuel_consumed, 3)
            )

        return 0.0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def score(self) -> float:
        """The (hybrid) score for the trip.

        Returns:
            float: The hybrid score for the trip

        """
        if self._trip.scores and self._trip.scores.global_:
            return self._trip.scores.global_

        return 0.0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def route(self) -> Optional[List[Tuple[Optional[float], Optional[float]]]]:
        """The route taken.

        Returns:
            Optional[List[Tuple[float, float]]]: List of Lat, Lon of the route taken.
                None if no route provided.

        """
        if self._trip.route:
            return [(rm.lat, rm.lon) for rm in self._trip.route]

        return None
