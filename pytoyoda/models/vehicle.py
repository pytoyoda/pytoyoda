"""Vehicle model."""

import asyncio
import copy
import json
from datetime import date, timedelta
from functools import partial
from itertools import groupby
from operator import attrgetter
from typing import Any, Dict, List, Optional, Tuple

from arrow import Arrow

from pytoyoda.api import Api
from pytoyoda.models.climate import ClimateSettings, ClimateStatus
from pytoyoda.models.dashboard import Dashboard
from pytoyoda.models.electric_status import ElectricStatus
from pytoyoda.models.endpoints.command import CommandType
from pytoyoda.models.endpoints.common import StatusModel
from pytoyoda.models.endpoints.vehicle_guid import VehicleGuidModel
from pytoyoda.models.location import Location
from pytoyoda.models.lock_status import LockStatus
from pytoyoda.models.nofication import Notification
from pytoyoda.models.service_history import ServiceHistory
from pytoyoda.models.summary import Summary, SummaryType
from pytoyoda.models.trips import Trip
from pytoyoda.utils.helpers import add_with_none
from pytoyoda.utils.log_utils import censor_all


class Vehicle:
    """Vehicle data representation."""

    def __init__(
        self, api: Api, vehicle_info: VehicleGuidModel, metric: bool = True
    ) -> None:
        """Initialise the Vehicle data representation."""
        self._vehicle_info = vehicle_info
        self._api = api
        self._endpoint_data: Dict[str, Any] = {}
        self._metric = metric

        # Endpoint Name, Function to check if car supports the endpoint,
        # endpoint to call to update
        api_endpoints = [
            {
                "name": "location",
                "capable": vehicle_info.extended_capabilities.last_parked_capable
                or vehicle_info.features.last_parked,
                "function": partial(self._api.get_location, vin=vehicle_info.vin),
            },
            {
                "name": "health_status",
                "capable": True,  # TODO Unsure of the required capability
                "function": partial(
                    self._api.get_vehicle_health_status,
                    vin=vehicle_info.vin,
                ),
            },
            {
                "name": "electric_status",
                "capable": vehicle_info.extended_capabilities.econnect_vehicle_status_capable,  # noqa: E501
                "function": partial(
                    self._api.get_vehicle_electric_status,
                    vin=vehicle_info.vin,
                ),
            },
            {
                "name": "telemetry",
                "capable": vehicle_info.extended_capabilities.telemetry_capable,
                "function": partial(self._api.get_telemetry, vin=vehicle_info.vin),
            },
            {
                "name": "notifications",
                "capable": True,  # TODO Unsure of the required capability
                "function": partial(self._api.get_notifications, vin=vehicle_info.vin),
            },
            {
                "name": "status",
                "capable": vehicle_info.extended_capabilities.vehicle_status,
                "function": partial(self._api.get_remote_status, vin=vehicle_info.vin),
            },
            {
                "name": "service_history",
                "capable": vehicle_info.features.service_history,
                "function": partial(
                    self._api.get_service_history, vin=vehicle_info.vin
                ),
            },
            {
                "name": "climate_settings",
                "capable": vehicle_info.features.climate_start_engine,
                "function": partial(
                    self._api.get_climate_settings, vin=vehicle_info.vin
                ),
            },
            {
                "name": "climate_status",
                "capable": vehicle_info.features.climate_start_engine,
                "function": partial(self._api.get_climate_status, vin=vehicle_info.vin),
            },
            {
                "name": "trip_history",
                "capable": True,
                "function": partial(
                    self._api.get_trips,
                    vin=vehicle_info.vin,
                    from_date=(date.today() - timedelta(days=90)),
                    to_date=date.today(),
                    summary=True,
                    limit=1,
                    offset=0,
                    route=False,
                ),
            },
        ]
        self._endpoint_collect = [
            (endpoint["name"], endpoint["function"])
            for endpoint in api_endpoints
            if endpoint["capable"]
        ]

    async def update(self) -> None:
        """Update the data for the vehicle.

        This method asynchronously updates the data for the vehicle by
        calling the endpoint functions in parallel.

        Returns:
            None

        """

        async def parallel_wrapper(
            name: str, function: partial
        ) -> Tuple[str, Dict[str, Any]]:
            r = await function()
            return name, r

        responses = asyncio.gather(
            *[
                parallel_wrapper(name, function)
                for name, function in self._endpoint_collect
            ]
        )
        for name, data in await responses:
            self._endpoint_data[name] = data

    @property
    def vin(self) -> Optional[str]:
        """Return the vehicles VIN number.

        Returns:
            Optional[str]: The vehicles VIN number

        """
        return self._vehicle_info.vin

    @property
    def alias(self) -> Optional[str]:
        """Vehicle's alias.

        Returns:
            Optional[str]: Nickname of vehicle

        """
        return self._vehicle_info.nickname

    @property
    def type(self) -> Optional[str]:
        """Returns the "type" of vehicle.

        Returns:
            Optional[str]: "fuel" if only fuel based
                "mildhybrid" if hybrid
                "phev" if plugin hybrid
                "ev" if full electric vehicle

        """
        # TODO enum
        # TODO currently guessing until we see a mild hybrid and full EV
        # TODO should probably use electricalPlatformCode but values currently unknown
        # TODO list of fuel types. ?: G=Petrol Only, I=Hybrid
        return (
            "phev"
            if self._vehicle_info.ev_vehicle and self._vehicle_info.fuel_type
            else "ev"
        )

    @property
    def dashboard(self) -> Optional[Dashboard]:
        """Returns the Vehicle dashboard.

        The dashboard consists of items of information you would expect to
        find on the dashboard. i.e. Fuel Levels.

        Returns:
            Optional[Dashboard]: A dashboard

        """
        # Always returns a Dashboard object as we can always get the odometer value
        return Dashboard(
            self._endpoint_data["telemetry"]
            if "telemetry" in self._endpoint_data
            else None,
            self._endpoint_data["electric_status"]
            if "electric_status" in self._endpoint_data
            else None,
            self._endpoint_data["health_status"]
            if "health_status" in self._endpoint_data
            else None,
            self._metric,
        )

    @property
    def climate_settings(self) -> Optional[ClimateSettings]:
        """Return the vehicle climate settings.

        Returns:
            Optional[ClimateSettings]: A climate settings

        """
        return ClimateSettings(self._endpoint_data.get("climate_settings", None))

    @property
    def climate_status(self) -> Optional[ClimateStatus]:
        """Return the vehicle climate status.

        Returns:
            Optional[ClimateStatus]: A climate status

        """
        return ClimateStatus(self._endpoint_data.get("climate_status", None))

    @property
    def electric_status(self) -> Optional[ElectricStatus]:
        """Returns the Electric Status of the vehicle.

        Returns:
            Optional[ElectricStatus]: Electric Status

        """
        return (
            ElectricStatus(self._endpoint_data["electric_status"])
            if "electric_status" in self._endpoint_data
            else None
        )

    @property
    def location(self) -> Optional[Location]:
        """Return the vehicles latest reported Location.

        Returns:
            Optional[Location]: The latest location or None. If None vehicle car
                does not support providing location information.
                _Note_ an empty location object can be returned when the Vehicle
                supports location but none is currently available.

        """
        return (
            Location(self._endpoint_data["location"])
            if "location" in self._endpoint_data
            else None
        )

    @property  # TODO: Cant have a property with parameters! Split into two methods?
    def notifications(self) -> Optional[List[Notification]]:
        r"""Returns a list of notifications for the vehicle.

        Returns:
            Optional[List[Notification]]: A list of notifications for the vehicle,
                or None if not supported.

        """
        if "notifications" in self._endpoint_data:
            ret: List[Notification] = []
            for p in self._endpoint_data["notifications"].payload:
                ret.extend(Notification(n) for n in p.notifications)
            return ret

        return None

    @property
    def service_history(self) -> Optional[List[ServiceHistory]]:
        r"""Returns a list of service history entries for the vehicle.

        Returns:
            Optional[List[ServiceHistory]]: A list of service history entries
                for the vehicle, or None if not supported.

        """
        if "service_history" in self._endpoint_data:
            ret: List[ServiceHistory] = []
            payload = self._endpoint_data["service_history"].payload
            ret.extend(
                ServiceHistory(service_history)
                for service_history in payload.service_histories
            )
            return ret

        return None

    def get_latest_service_history(self) -> Optional[ServiceHistory]:
        r"""Return the latest service history entry for the vehicle.

        Returns:
            Optional[ServiceHistory]: A service history entry for the vehicle,
                ordered by date and service_category. None if not supported or unknown.

        """
        if self.service_history is not None:
            return max(
                self.service_history, key=lambda x: (x.service_date, x.service_category)
            )
        return None

    @property
    def lock_status(self) -> Optional[LockStatus]:
        """Returns the latest lock status of Doors & Windows.

        Returns:
            Optional[LockStatus]: The latest lock status of Doors & Windows,
                or None if not supported.

        """
        return LockStatus(
            self._endpoint_data["status"] if "status" in self._endpoint_data else None
        )

    @property
    def last_trip(self) -> Optional[Trip]:
        """Returns the Vehicle last trip.

        Returns:
            Optional[Trip]: The last trip

        """
        ret = None
        if "trip_history" in self._endpoint_data:
            ret = next(iter(self._endpoint_data["trip_history"].payload.trips), None)

        if ret is None:
            return None

        return Trip(ret, self._metric)

    @property
    def trip_history(self) -> Optional[List[Trip]]:
        """Returns the Vehicle trips.

        Returns:
            Optional[List[Trip]]: A list of trips

        """
        if "trip_history" in self._endpoint_data:
            ret: List[Trip] = []
            payload = self._endpoint_data["trip_history"].payload
            ret.extend(Trip(t, self._metric) for t in payload.trips)
            return ret

        return None

    async def get_summary(
        self,
        from_date: date,
        to_date: date,
        summary_type: SummaryType = SummaryType.MONTHLY,
    ) -> List[Summary]:
        """Return different summarys between the provided dates.

        All but Daily can return a partial time range. For example
        if the summary_type is weekly and the date ranges selected
        include partial weeks these partial weeks will be returned.
        The dates contained in the summary will indicate the range
        of dates that made up the partial week.

        Note: Weekly and yearly summaries lose a small amount of
        accuracy due to rounding issues.

        Args:
            from_date (date, required): The inclusive from date to report summaries.
            to_date (date, required): The inclusive to date to report summaries.
            summary_type (SummaryType, optional): Daily, Monthly or Yearly summary.
                Monthly by default.

        Returns:
            List[Summary]: A list of summaries or empty list if not supported.

        """
        to_date = min(to_date, date.today())

        # Summary information is always returned in the first response.
        # No need to check all the following pages
        resp = await self._api.get_trips(
            self.vin, from_date, to_date, summary=True, limit=1, offset=0
        )
        if resp.payload is None or len(resp.payload.summary) == 0:
            return []

        # Convert to response
        if summary_type == SummaryType.DAILY:
            return self._generate_daily_summaries(resp.payload.summary)
        elif summary_type == SummaryType.WEEKLY:
            return self._generate_weekly_summaries(resp.payload.summary)
        elif summary_type == SummaryType.MONTHLY:
            return self._generate_monthly_summaries(
                resp.payload.summary, from_date, to_date
            )
        elif summary_type == SummaryType.YEARLY:
            return self._generate_yearly_summaries(resp.payload.summary, to_date)
        else:
            raise AssertionError("No such SummaryType")

    async def get_current_day_summary(self) -> Optional[Summary]:
        """Return a summary for the current day.

        Returns:
            Optional[Summary]: A summary or None if not supported.

        """
        summary = await self.get_summary(
            from_date=Arrow.now().date(),
            to_date=Arrow.now().date(),
            summary_type=SummaryType.DAILY,
        )
        assert len(summary) < 2
        return summary[0] if len(summary) > 0 else None

    async def get_current_week_summary(self) -> Optional[Summary]:
        """Return a summary for the current week.

        Returns:
            Optional[Summary]: A summary or None if not supported.

        """
        summary = await self.get_summary(
            from_date=Arrow.now().floor("week").date(),
            to_date=Arrow.now().date(),
            summary_type=SummaryType.WEEKLY,
        )
        assert len(summary) < 2
        return summary[0] if len(summary) > 0 else None

    async def get_current_month_summary(self) -> Optional[Summary]:
        """Return a summary for the current month.

        Returns:
            Optional[Summary]: A summary or None if not supported.

        """
        summary = await self.get_summary(
            from_date=Arrow.now().floor("month").date(),
            to_date=Arrow.now().date(),
            summary_type=SummaryType.MONTHLY,
        )
        assert len(summary) < 2
        return summary[0] if len(summary) > 0 else None

    async def get_current_year_summary(self) -> Optional[Summary]:
        """Return a summary for the current year.

        Returns:
            Optional[Summary]: A summary or None if not supported.

        """
        summary = await self.get_summary(
            from_date=Arrow.now().floor("year").date(),
            to_date=Arrow.now().date(),
            summary_type=SummaryType.YEARLY,
        )
        assert len(summary) < 2
        return summary[0] if len(summary) > 0 else None

    async def get_trips(
        self, from_date: date, to_date: date, full_route: bool = False
    ) -> Optional[List[Trip]]:
        """Return information on all trips made between the provided dates.

        Args:
            from_date (date, required): The inclusive from date
            to_date (date, required): The inclusive to date
            full_route (bool, optional): Provide the full route
                                         information for each trip.

        Returns:
            Optional[List[Something]]: A list of all trips or None if not supported.

        """
        ret: List[Trip] = []
        offset = 0
        while True:
            resp = await self._api.get_trips(
                self.vin,
                from_date,
                to_date,
                summary=False,
                limit=5,
                offset=offset,
                route=full_route,
            )
            if resp.payload is None:
                break

            # Convert to response
            for t in resp.payload.trips:
                ret.append(Trip(t, self._metric))

            offset = resp.payload.metadata.pagination.next_offset
            if offset is None:
                break

        return ret

    async def get_last_trip(self) -> Optional[Trip]:
        """Return information on the last trip.

        Returns:
            Optional[Trip]: A trip model or None if not supported.

        """
        resp = await self._api.get_trips(
            self.vin,
            date.today() - timedelta(days=90),
            date.today(),
            summary=False,
            limit=1,
            offset=0,
            route=False,
        )

        if resp.payload is None:
            return None

        ret = next(iter(resp.payload.trips), None)
        if ret is None:
            return None

        return Trip(ret, self._metric)

    async def refresh_climate_status(self) -> StatusModel:
        """Force update of climate status.

        Returns:
            StatusModel: A status response for the command.

        """
        return await self._api.refresh_climate_status(self.vin)

    async def post_command(self, command: CommandType, beeps: int = 0) -> StatusModel:
        """Send remote command to the vehicle.

        Args:
            command (CommandType): The remote command model
            beeps (int): Amount of beeps for commands that support it

        Returns:
            StatusModel: A status response for the command.

        """
        return await self._api.send_command(self.vin, command=command, beeps=beeps)

    #
    # More get functionality depending on what we find
    #

    async def set_alias(self, value) -> bool:
        """Set the alias for the vehicle.

        Args:
            value: The alias value to set for the vehicle.

        Returns:
            bool: Indicator if value is set

        """
        return value

    #
    # More set functionality depending on what we find
    #

    def _dump_all(self) -> Dict[str, Any]:
        """Dump data from all endpoints for debugging and further work."""
        dump: [str, Any] = {
            "vehicle_info": json.loads(self._vehicle_info.model_dump_json())
        }
        for name, data in self._endpoint_data.items():
            dump[name] = json.loads(data.model_dump_json())

        return censor_all(copy.deepcopy(dump))

    def _generate_daily_summaries(self, summary) -> List[Summary]:
        summary.sort(key=attrgetter("year", "month"))
        return [
            Summary(
                histogram.summary,
                self._metric,
                Arrow(histogram.year, histogram.month, histogram.day).date(),
                Arrow(histogram.year, histogram.month, histogram.day).date(),
                histogram.hdc,
            )
            for month in summary
            for histogram in sorted(month.histograms, key=attrgetter("day"))
        ]

    def _generate_weekly_summaries(self, summary) -> List[Summary]:
        ret: List[Summary] = []
        summary.sort(key=attrgetter("year", "month"))

        # Flatten the list of histograms
        histograms = [histogram for month in summary for histogram in month.histograms]
        histograms.sort(key=lambda h: date(day=h.day, month=h.month, year=h.year))

        # Group histograms by week
        for _, week_histograms_iter in groupby(
            histograms, key=lambda h: Arrow(h.year, h.month, h.day).span("week")[0]
        ):
            week_histograms = list(week_histograms_iter)
            build_hdc = copy.copy(week_histograms[0].hdc)
            build_summary = copy.copy(week_histograms[0].summary)
            start_date = Arrow(
                week_histograms[0].year,
                week_histograms[0].month,
                week_histograms[0].day,
            )

            for histogram in week_histograms[1:]:
                add_with_none(build_hdc, histogram.hdc)
                build_summary += histogram.summary

            end_date = Arrow(
                week_histograms[-1].year,
                week_histograms[-1].month,
                week_histograms[-1].day,
            )
            ret.append(
                Summary(
                    build_summary,
                    self._metric,
                    start_date.date(),
                    end_date.date(),
                    build_hdc,
                )
            )

        return ret

    def _generate_monthly_summaries(
        self, summary, from_date: date, to_date: date
    ) -> List[Summary]:
        # Convert all the monthly responses from the payload to a summary response
        ret: List[Summary] = []
        summary.sort(key=attrgetter("year", "month"))
        for month in summary:
            month_start = Arrow(month.year, month.month, 1).date()
            month_end = (
                Arrow(month.year, month.month, 1).shift(months=1).shift(days=-1).date()
            )

            ret.append(
                Summary(
                    month.summary,
                    self._metric,
                    # The data might not include an entire month
                    # so update start and end dates.
                    max(month_start, from_date),
                    min(month_end, to_date),
                    month.hdc,
                )
            )

        return ret

    def _generate_yearly_summaries(self, summary, to_date: date) -> List[Summary]:
        summary.sort(key=attrgetter("year", "month"))
        ret: List[Summary] = []
        build_hdc = copy.copy(summary[0].hdc)
        build_summary = copy.copy(summary[0].summary)
        start_date = date(day=1, month=summary[0].month, year=summary[0].year)

        if len(summary) == 1:
            ret.append(
                Summary(build_summary, self._metric, start_date, to_date, build_hdc)
            )
        else:
            for month, next_month in zip(
                summary[1:], summary[2:] + [None], strict=False
            ):
                summary_month = date(day=1, month=month.month, year=month.year)
                add_with_none(build_hdc, month.hdc)
                build_summary += month.summary

                if next_month is None or next_month.year != month.year:
                    end_date = min(
                        to_date, date(day=31, month=12, year=summary_month.year)
                    )
                    ret.append(
                        Summary(
                            build_summary, self._metric, start_date, end_date, build_hdc
                        )
                    )
                    if next_month:
                        start_date = date(
                            day=1, month=next_month.month, year=next_month.year
                        )
                        build_hdc = copy.copy(next_month.hdc)
                        build_summary = copy.copy(next_month.summary)

        return ret
