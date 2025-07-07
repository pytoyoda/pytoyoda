"""Model for Trip Summaries."""

# ruff: noqa: FA100

from datetime import date, timedelta
from enum import IntEnum
from typing import Optional, TypeVar, Union

from pydantic import computed_field

from pytoyoda.const import (
    KILOMETERS_UNIT,
    MILES_UNIT,
    ML_TO_GAL_FACTOR,
    ML_TO_L_FACTOR,
)
from pytoyoda.models.endpoints.trips import _HDCModel, _SummaryBaseModel
from pytoyoda.utils.conversions import convert_distance, convert_to_mpg
from pytoyoda.utils.models import CustomAPIBaseModel

T = TypeVar(
    "T",
    bound=Union[_SummaryBaseModel, bool, date, _HDCModel],
)


class SummaryType(IntEnum):
    """Type of summary for use with get_summary."""

    DAILY = 1
    WEEKLY = 2
    MONTHLY = 3
    YEARLY = 4


class Summary(CustomAPIBaseModel[type[T]]):
    """Base class of Daily, Weekly, Monthly, Yearly summary."""

    def __init__(
        self,
        summary: _SummaryBaseModel,
        metric: bool,  # noqa : FBT001
        from_date: date,
        to_date: date,
        hdc: Optional[_HDCModel] = None,
        **kwargs: dict,
    ) -> None:
        """Initialise Class.

        Args:
            summary (_SummaryBaseModel, required): Contains all the summary information
            metric (bool, required): Report in Metric or Imperial
            from_date (date, required): Start date for this summary
            to_date (date, required): End date for this summary
            hdc: (_HDCModel, optional): Hybrid data if available
            **kwargs: Additional keyword arguments passed to the parent class

        """
        data = {
            "summary": summary,
            "metric": metric,
            "from_date": from_date,
            "to_date": to_date,
            "hdc": hdc,
        }
        super().__init__(data=data, **kwargs)  # type: ignore[reportArgumentType, arg-type]

        self._summary: _SummaryBaseModel = summary
        self._metric: bool = metric
        self._from_date: date = from_date
        self._to_date: date = to_date
        self._hdc: Optional[_HDCModel] = hdc
        self._distance_unit: str = KILOMETERS_UNIT if metric else MILES_UNIT

    @computed_field  # type: ignore[prop-decorator]
    @property
    def average_speed(self) -> Optional[float]:
        """Average speed.

        Returns:
            float: Average speed in selected metric
                Return information on all trips made between the provided dates.

        """
        if self._summary.average_speed:
            return convert_distance(
                self._distance_unit, KILOMETERS_UNIT, self._summary.average_speed
            )
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def countries(self) -> Optional[list[str]]:
        """Countries visited.

        Returns:
            list[str]: List of countries visited in 'ISO 3166-1 alpha-2' or
                two-letter country codes format.

        """
        return self._summary.countries or None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def duration(self) -> Optional[timedelta]:
        """The total time driving.

        Returns:
            timedelta: The amount of time driving

        """
        if self._summary.duration:
            return timedelta(seconds=self._summary.duration)
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def distance(self) -> Optional[float]:
        """The total distance covered.

        Returns:
            float: Distance covered in the selected metric

        """
        if self._summary.length:
            return convert_distance(
                self._distance_unit, KILOMETERS_UNIT, self._summary.length / 1000.0
            )
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ev_duration(self) -> Optional[timedelta]:
        """The total time driving using EV.

        Returns:
            Optional[timedelta]: The amount of time driving using EV or
                None if not supported

        """
        if self._hdc and self._hdc.ev_time:
            return timedelta(seconds=self._hdc.ev_time)
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ev_distance(self) -> Optional[float]:
        """The total time distance driven using EV.

        Returns:
            Optional[float]: The distance driven using EV in selectedwq
                metric or None if not supported

        """
        if self._hdc and self._hdc.ev_distance:
            return convert_distance(
                self._distance_unit, KILOMETERS_UNIT, self._hdc.ev_distance / 1000.0
            )
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def from_date(self) -> date:
        """The date the summary started.

        Returns:
            date: The date the summary started

        """
        return self._from_date

    @computed_field  # type: ignore[prop-decorator]
    @property
    def to_date(self) -> date:
        """The date the summary ended.

        Returns:
            date: The date the summary ended

        """
        return self._to_date

    @computed_field  # type: ignore[prop-decorator]
    @property
    def fuel_consumed(self) -> float:
        """The total amount of fuel consumed.

        Returns:
            float: The total amount of fuel consumed in liters if metric or gallons

        """
        if self._summary.fuel_consumption:
            return (
                round(self._summary.fuel_consumption / ML_TO_L_FACTOR, 3)
                if self._metric
                else round(self._summary.fuel_consumption / ML_TO_GAL_FACTOR, 3)
            )

        return 0.0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def average_fuel_consumed(self) -> float:
        """The average amount of fuel consumed.

        Returns:
            float: The average amount of fuel consumed in l/100km if metric or mpg

        """
        if self._summary.fuel_consumption and self._summary.length:
            avg_fuel_consumed = (
                self._summary.fuel_consumption / self._summary.length
            ) * 100
            return (
                round(avg_fuel_consumed, 3)
                if self._metric
                else convert_to_mpg(avg_fuel_consumed)
            )

        return 0.0
