"""Vehicle model."""

import copy
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum, auto
from functools import partial
from itertools import groupby
from operator import attrgetter
from typing import Any, TypeVar

from arrow import Arrow
from loguru import logger
from pydantic import computed_field

from pytoyoda.api import Api
from pytoyoda.exceptions import ToyotaApiError
from pytoyoda.models.climate import ClimateSettings, ClimateStatus
from pytoyoda.models.dashboard import Dashboard
from pytoyoda.models.electric_status import ElectricStatus
from pytoyoda.models.endpoints.command import CommandType
from pytoyoda.models.endpoints.common import StatusModel
from pytoyoda.models.endpoints.electric import (
    ElectricCommandResponseModel,
    NextChargeSettings,
)
from pytoyoda.models.endpoints.refresh_status import RefreshStatusResponseModel
from pytoyoda.models.endpoints.trips import _SummaryItemModel
from pytoyoda.models.endpoints.vehicle_guid import VehicleGuidModel
from pytoyoda.models.location import Location
from pytoyoda.models.lock_status import LockStatus
from pytoyoda.models.nofication import Notification
from pytoyoda.models.service_history import ServiceHistory
from pytoyoda.models.summary import Summary, SummaryType
from pytoyoda.models.trips import Trip
from pytoyoda.utils.helpers import add_with_none
from pytoyoda.utils.log_utils import censor_all
from pytoyoda.utils.models import CustomAPIBaseModel

T = TypeVar(
    "T",
    bound=Api | VehicleGuidModel | bool,
)


class VehicleType(Enum):
    """Vehicle types."""

    PLUG_IN_HYBRID = auto()
    FULL_HYBRID = auto()
    ELECTRIC = auto()
    FUEL_ONLY = auto()

    @classmethod
    def from_vehicle_info(cls, info: VehicleGuidModel) -> "VehicleType":
        """Determine the vehicle type based on detailed vehicle fuel information.

        Args:
            info (VehicleGuidModel): Vehicle information model

        Returns:
            VehicleType: Determined vehicle type

        """
        try:
            if info.fuel_type == "B":
                vehicle_type = cls.FULL_HYBRID
            elif info.fuel_type == "E":
                vehicle_type = cls.ELECTRIC
            elif info.fuel_type == "I":
                vehicle_type = cls.PLUG_IN_HYBRID
            else:
                vehicle_type = cls.FUEL_ONLY
        except AttributeError:
            return cls.FUEL_ONLY
        else:
            return vehicle_type


@dataclass
class EndpointDefinition:
    """Definition of an API endpoint."""

    name: str
    capable: bool
    function: Callable
    # If True, failures here are caught + recorded in
    # Vehicle._endpoint_errors instead of aborting update().
    optional: bool = False


class Vehicle(CustomAPIBaseModel[type[T]]):
    """Vehicle data representation."""

    def __init__(
        self,
        api: Api,
        vehicle_info: VehicleGuidModel,
        metric: bool = True,  # noqa: FBT001, FBT002
        **kwargs: dict,
    ) -> None:
        """Initialise the Vehicle data representation."""
        data = {
            "api": api,
            "vehicle_info": vehicle_info,
            "metric": metric,
        }
        super().__init__(data=data, **kwargs)  # type: ignore[reportArgumentType, arg-type]
        self._api = api
        self._vehicle_info = vehicle_info
        self._metric = metric
        self._endpoint_data: dict[str, Any] = {}

        if self._vehicle_info.vin:
            self._api_endpoints: list[EndpointDefinition] = [
                EndpointDefinition(
                    name="location",
                    capable=(
                        getattr(
                            getattr(self._vehicle_info, "extended_capabilities", False),
                            "last_parked_capable",
                            False,
                        )
                        or getattr(
                            getattr(self._vehicle_info, "features", False),
                            "last_parked",
                            False,
                        )
                    ),
                    function=partial(
                        self._api.get_location, vin=self._vehicle_info.vin
                    ),
                ),
                EndpointDefinition(
                    name="health_status",
                    capable=True,
                    function=partial(
                        self._api.get_vehicle_health_status,
                        vin=self._vehicle_info.vin,
                    ),
                ),
                EndpointDefinition(
                    name="electric_status",
                    capable=getattr(
                        getattr(self._vehicle_info, "extended_capabilities", False),
                        "econnect_vehicle_status_capable",
                        False,
                    ),
                    function=partial(
                        self._api.get_vehicle_electric_status,
                        vin=self._vehicle_info.vin,
                    ),
                ),
                EndpointDefinition(
                    name="telemetry",
                    capable=getattr(
                        getattr(self._vehicle_info, "extended_capabilities", False),
                        "telemetry_capable",
                        False,
                    ),
                    function=partial(
                        self._api.get_telemetry, vin=self._vehicle_info.vin
                    ),
                ),
                EndpointDefinition(
                    name="notifications",
                    capable=True,
                    function=partial(
                        self._api.get_notifications, vin=self._vehicle_info.vin
                    ),
                ),
                EndpointDefinition(
                    name="status",
                    capable=getattr(
                        getattr(self._vehicle_info, "extended_capabilities", False),
                        "vehicle_status",
                        False,
                    ),
                    function=partial(
                        self._api.get_remote_status, vin=self._vehicle_info.vin
                    ),
                ),
                EndpointDefinition(
                    name="service_history",
                    capable=getattr(
                        getattr(self._vehicle_info, "features", False),
                        "service_history",
                        False,
                    ),
                    function=partial(
                        self._api.get_service_history, vin=self._vehicle_info.vin
                    ),
                ),
                EndpointDefinition(
                    name="climate_settings",
                    capable=getattr(
                        getattr(self._vehicle_info, "features", False),
                        "climate_start_engine",
                        False,
                    ),
                    function=partial(
                        self._api.get_climate_settings, vin=self._vehicle_info.vin
                    ),
                    # Toyota selectively 500s on this endpoint for some
                    # accounts. See ha_toyota#291.
                    optional=True,
                ),
                EndpointDefinition(
                    name="climate_status",
                    capable=getattr(
                        getattr(self._vehicle_info, "features", False),
                        "climate_start_engine",
                        False,
                    ),
                    function=partial(
                        self._api.get_climate_status, vin=self._vehicle_info.vin
                    ),
                    optional=True,
                ),
                EndpointDefinition(
                    name="trip_history",
                    capable=True,
                    function=partial(
                        self._api.get_trips,
                        vin=self._vehicle_info.vin,
                        from_date=(date.today() - timedelta(days=90)),  # noqa: DTZ011
                        to_date=date.today(),  # noqa: DTZ011
                        summary=True,
                        limit=1,
                        offset=0,
                        route=False,
                    ),
                ),
            ]
        else:
            raise ToyotaApiError(
                logger.error(
                    "The VIN (vehicle identification number) "
                    "required for the end point request could not be determined"
                )
            )
        self._endpoint_collect = [
            endpoint for endpoint in self._api_endpoints if endpoint.capable
        ]
        # Failures on optional endpoints from the most recent update().
        self._endpoint_errors: dict[str, Exception] = {}

    async def update(
        self,
        skip: list[str] | None = None,
        only: list[str] | None = None,
    ) -> None:
        """Update the data for the vehicle.

        Endpoint functions are awaited sequentially rather than in a single
        asyncio.gather. Toyota's API gateway appears to rate-limit on bursts
        of near-simultaneous requests: firing ~10 requests in the same event
        loop tick reliably trips a 429 with `{"description": "Unauthorized"}`
        response bodies, while the same requests serialised at poll cadence
        succeed cleanly. See pytoyoda/ha_toyota#282 for measurement evidence.

        Args:
            skip: Endpoint names (matching EndpointDefinition.name values
                like "status", "telemetry", etc.) to skip this cycle.
                Skipped endpoints retain their previous _endpoint_data
                entry, so consumers continue to see the last-known value.
                Used by ha_toyota's smart-refresh strategy to skip
                /v1/global/remote/status when a separate POST/GET cycle
                handles it explicitly.
            only: Inverse of skip - if provided, ONLY these endpoint names
                will be fetched. Mutually exclusive with skip.
                Used by ha_toyota's smart-refresh strategy to update just
                /v1/global/remote/status after a wake POST without
                re-hitting the other endpoints that are already fresh.

        Returns:
            None

        Raises:
            ValueError: If both skip and only are provided.

        """
        if skip is not None and only is not None:
            msg = "update(): pass either skip or only, not both"
            raise ValueError(msg)
        skip_set = set(skip or [])
        only_set = set(only) if only is not None else None
        self._endpoint_errors = {}
        for endpoint in self._endpoint_collect:
            if only_set is not None and endpoint.name not in only_set:
                continue
            if endpoint.name in skip_set:
                continue
            try:
                self._endpoint_data[endpoint.name] = await endpoint.function()
            except Exception as ex:
                if not endpoint.optional:
                    raise
                self._endpoint_errors[endpoint.name] = ex
                # Clear any stale payload from a previous successful cycle so
                # downstream getters return None instead of outdated data.
                self._endpoint_data.pop(endpoint.name, None)
                logger.warning(
                    "Optional endpoint '{}' failed and will be cleared this "
                    "cycle: {}: {}",
                    endpoint.name,
                    type(ex).__name__,
                    ex,
                )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def vin(self) -> str | None:
        """Return the vehicles VIN number.

        Returns:
            Optional[str]: The vehicles VIN number

        """
        return self._vehicle_info.vin

    @computed_field  # type: ignore[prop-decorator]
    @property
    def alias(self) -> str | None:
        """Vehicle's alias.

        Returns:
            Optional[str]: Nickname of vehicle

        """
        return self._vehicle_info.nickname

    @computed_field  # type: ignore[prop-decorator]
    @property
    def type(self) -> str | None:
        """Returns the "type" of vehicle.

        Returns:
            Optional[str]: "fuel" if only fuel based
                "mildhybrid" if hybrid
                "phev" if plugin hybrid
                "ev" if full electric vehicle

        """
        vehicle_type = VehicleType.from_vehicle_info(self._vehicle_info)
        return vehicle_type.name.lower()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def dashboard(self) -> Dashboard | None:
        """Returns the Vehicle dashboard.

        The dashboard consists of items of information you would expect to
        find on the dashboard. i.e. Fuel Levels.

        Returns:
            Optional[Dashboard]: A dashboard

        """
        # Always returns a Dashboard object as we can always get the odometer value
        return Dashboard(
            self._endpoint_data.get("telemetry", None),
            self._endpoint_data.get("electric_status", None),
            self._endpoint_data.get("health_status", None),
            self._metric,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def climate_settings(self) -> ClimateSettings | None:
        """Return the vehicle climate settings.

        Returns:
            Optional[ClimateSettings]: A climate settings

        """
        return ClimateSettings(self._endpoint_data.get("climate_settings", None))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def climate_status(self) -> ClimateStatus | None:
        """Return the vehicle climate status.

        Returns:
            Optional[ClimateStatus]: A climate status

        """
        return ClimateStatus(self._endpoint_data.get("climate_status", None))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def electric_status(self) -> ElectricStatus | None:
        """Returns the Electric Status of the vehicle.

        Returns:
            Optional[ElectricStatus]: Electric Status

        """
        return ElectricStatus(self._endpoint_data.get("electric_status", None))

    async def refresh_electric_realtime_status(self) -> StatusModel:
        """Force update of electric realtime status.

        This will drain the 12V battery of the vehicle if
        used to often!

        Returns:
            StatusModel: A status response for the command.

        """
        return await self._api.refresh_electric_realtime_status(self.vin)

    async def refresh_status(self) -> RefreshStatusResponseModel:
        """Wake the vehicle and request a fresh /status cache populate.

        Issues POST /v1/global/remote/refresh-status. Use sparingly:
        each call uses cellular airtime and a small amount of 12V battery.
        Returns when the gateway has accepted the wake request, NOT when
        the cache has actually been populated; the caller should poll
        /status afterwards (and check occurrence_date advancement) to
        verify the wake succeeded end-to-end.

        Returns:
            RefreshStatusResponseModel: payload.return_code "000000"
                = wake accepted, anything else = vehicle does not
                support refresh-status (caller should disable further
                attempts for this VIN).

        """
        return await self._api.refresh_vehicle_status(self.vin)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def location(self) -> Location | None:
        """Return the vehicles latest reported Location.

        Returns:
            Optional[Location]: The latest location or None. If None vehicle car
                does not support providing location information.
                _Note_ an empty location object can be returned when the Vehicle
                supports location but none is currently available.

        """
        return Location(self._endpoint_data.get("location", None))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def notifications(self) -> list[Notification] | None:
        r"""Returns a list of notifications for the vehicle.

        Returns:
            Optional[list[Notification]]: A list of notifications for the vehicle,
                or None if not supported.

        """
        if "notifications" in self._endpoint_data:
            ret: list[Notification] = []
            for p in self._endpoint_data["notifications"].payload:
                ret.extend(Notification(n) for n in p.notifications)
            return ret

        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def service_history(self) -> list[ServiceHistory] | None:
        r"""Returns a list of service history entries for the vehicle.

        Returns:
            Optional[list[ServiceHistory]]: A list of service history entries
                for the vehicle, or None if not supported.

        """
        if "service_history" in self._endpoint_data:
            ret: list[ServiceHistory] = []
            payload = self._endpoint_data["service_history"].payload
            if not payload:
                return None
            ret.extend(
                ServiceHistory(service_history)
                for service_history in payload.service_histories
            )
            return ret

        return None

    def get_latest_service_history(self) -> ServiceHistory | None:
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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def lock_status(self) -> LockStatus | None:
        """Returns the latest lock status of Doors & Windows.

        Returns:
            Optional[LockStatus]: The latest lock status of Doors & Windows,
                or None if not supported.

        """
        return LockStatus(self._endpoint_data.get("status", None))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def last_trip(self) -> Trip | None:
        """Returns the Vehicle last trip.

        Returns:
            Optional[Trip]: The last trip

        """
        ret = None
        if "trip_history" in self._endpoint_data:
            ret = next(iter(self._endpoint_data["trip_history"].payload.trips), None)

        return None if ret is None else Trip(ret, self._metric)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def trip_history(self) -> list[Trip] | None:
        """Returns the Vehicle trips.

        Returns:
            Optional[list[Trip]]: A list of trips

        """
        if "trip_history" in self._endpoint_data:
            ret: list[Trip] = []
            payload = self._endpoint_data["trip_history"].payload
            ret.extend(Trip(t, self._metric) for t in payload.trips)
            return ret

        return None

    async def get_summary(
        self,
        from_date: date,
        to_date: date,
        summary_type: SummaryType = SummaryType.MONTHLY,
    ) -> list[Summary]:
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
            list[Summary]: A list of summaries or empty list if not supported.

        """
        to_date = min(to_date, date.today())  # noqa : DTZ011

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
        if summary_type == SummaryType.WEEKLY:
            return self._generate_weekly_summaries(resp.payload.summary)
        if summary_type == SummaryType.MONTHLY:
            return self._generate_monthly_summaries(
                resp.payload.summary, from_date, to_date
            )
        if summary_type == SummaryType.YEARLY:
            return self._generate_yearly_summaries(resp.payload.summary, to_date)
        msg = "No such SummaryType"
        raise AssertionError(msg)

    async def get_current_day_summary(self) -> Summary | None:
        """Return a summary for the current day.

        Returns:
            Optional[Summary]: A summary or None if not supported.

        """
        summary = await self.get_summary(
            from_date=Arrow.now().date(),
            to_date=Arrow.now().date(),
            summary_type=SummaryType.DAILY,
        )
        min_no_of_summaries_required_for_calculation = 2
        if len(summary) < min_no_of_summaries_required_for_calculation:
            logger.info("Not enough summaries for calculation.")
        return summary[0] if len(summary) > 0 else None

    async def get_current_week_summary(self) -> Summary | None:
        """Return a summary for the current week.

        Returns:
            Optional[Summary]: A summary or None if not supported.

        """
        summary = await self.get_summary(
            from_date=Arrow.now().floor("week").date(),
            to_date=Arrow.now().date(),
            summary_type=SummaryType.WEEKLY,
        )
        min_no_of_summaries_required_for_calculation = 2
        if len(summary) < min_no_of_summaries_required_for_calculation:
            logger.info("Not enough summaries for calculation.")
        return summary[0] if len(summary) > 0 else None

    async def get_current_month_summary(self) -> Summary | None:
        """Return a summary for the current month.

        Returns:
            Optional[Summary]: A summary or None if not supported.

        """
        summary = await self.get_summary(
            from_date=Arrow.now().floor("month").date(),
            to_date=Arrow.now().date(),
            summary_type=SummaryType.MONTHLY,
        )
        min_no_of_summaries_required_for_calculation = 2
        if len(summary) < min_no_of_summaries_required_for_calculation:
            logger.info("Not enough summaries for calculation.")
        return summary[0] if len(summary) > 0 else None

    async def get_current_year_summary(self) -> Summary | None:
        """Return a summary for the current year.

        Returns:
            Optional[Summary]: A summary or None if not supported.

        """
        summary = await self.get_summary(
            from_date=Arrow.now().floor("year").date(),
            to_date=Arrow.now().date(),
            summary_type=SummaryType.YEARLY,
        )
        min_no_of_summaries_required_for_calculation = 2
        if len(summary) < min_no_of_summaries_required_for_calculation:
            logger.info("Not enough summaries for calculation.")
        return summary[0] if len(summary) > 0 else None

    async def get_trips(
        self,
        from_date: date,
        to_date: date,
        full_route: bool = False,  # noqa : FBT001, FBT002
    ) -> list[Trip] | None:
        """Return information on all trips made between the provided dates.

        Args:
            from_date (date, required): The inclusive from date
            to_date (date, required): The inclusive to date
            full_route (bool, optional): Provide the full route
                                         information for each trip.

        Returns:
            Optional[list[Trip]]: A list of all trips or None if not supported.

        """
        ret: list[Trip] = []
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
            if resp.payload.trips:
                ret.extend(Trip(t, self._metric) for t in resp.payload.trips)

            offset = resp.payload.metadata.pagination.next_offset
            if offset is None:
                break

        return ret

    async def get_last_trip(self) -> Trip | None:
        """Return information on the last trip.

        Returns:
            Optional[Trip]: A trip model or None if not supported.

        """
        resp = await self._api.get_trips(
            self.vin,
            date.today() - timedelta(days=90),  # noqa : DTZ011
            date.today(),  # noqa : DTZ011
            summary=False,
            limit=1,
            offset=0,
            route=False,
        )

        if resp.payload is None:
            return None

        ret = next(iter(resp.payload.trips), None)
        return None if ret is None else Trip(ret, self._metric)

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

    async def send_next_charging_command(
        self, command: NextChargeSettings
    ) -> ElectricCommandResponseModel:
        """Send the next command to the vehicle.

        Args:
            command: NextChargeSettings command to send

        Returns:
            Model containing status of the command request

        """
        return await self._api.send_next_charging_command(self.vin, command=command)

    #
    # More get functionality depending on what we find
    #

    async def set_alias(
        self,
        value: bool,  # noqa : FBT001
    ) -> bool:
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

    def _dump_all(self) -> dict[str, Any]:
        """Dump data from all endpoints for debugging and further work."""
        dump: [str, Any] = {
            "vehicle_info": json.loads(self._vehicle_info.model_dump_json())
        }
        for name, data in self._endpoint_data.items():
            dump[name] = json.loads(data.model_dump_json())

        return censor_all(copy.deepcopy(dump))

    def _generate_daily_summaries(
        self, summary: list[_SummaryItemModel]
    ) -> list[Summary]:
        summary.sort(key=attrgetter("year", "month"))
        # Skip histograms with summary=None - a hollow Summary crashes
        # downstream when sensors read its properties (see #278).
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
            if histogram.summary is not None
        ]

    def _generate_weekly_summaries(
        self, summary: list[_SummaryItemModel]
    ) -> list[Summary]:
        ret: list[Summary] = []
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
                # ``add_with_none`` returns the sum, so we must capture it;
                # without the assignment ``build_hdc`` would stay at the
                # first histogram's hdc (or ``None`` if that was None).
                build_hdc = add_with_none(build_hdc, histogram.hdc)
                # histogram.summary (and the seed build_summary) may be None on
                # days where the Toyota API returned a partial payload. Seed with
                # the first non-None summary we see, then accumulate.
                if histogram.summary is None:
                    continue
                if build_summary is None:
                    build_summary = copy.copy(histogram.summary)
                else:
                    build_summary += histogram.summary

            end_date = Arrow(
                week_histograms[-1].year,
                week_histograms[-1].month,
                week_histograms[-1].day,
            )
            # Skip weeks where every histogram.summary was None - a hollow
            # Summary crashes downstream when sensors read its properties.
            if build_summary is None:
                continue
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
        self, summary: list[_SummaryItemModel], from_date: date, to_date: date
    ) -> list[Summary]:
        # Convert all the monthly responses from the payload to a summary response
        ret: list[Summary] = []
        summary.sort(key=attrgetter("year", "month"))
        for month in summary:
            # Skip months with summary=None - a hollow Summary crashes
            # downstream when sensors read its properties (see #278).
            if month.summary is None:
                continue
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

    def _generate_yearly_summaries(
        self, summary: list[_SummaryItemModel], to_date: date
    ) -> list[Summary]:
        summary.sort(key=attrgetter("year", "month"))
        ret: list[Summary] = []
        build_hdc = copy.copy(summary[0].hdc)
        build_summary = copy.copy(summary[0].summary)
        start_date = date(day=1, month=summary[0].month, year=summary[0].year)

        if len(summary) == 1:
            if build_summary is not None:
                ret.append(
                    Summary(build_summary, self._metric, start_date, to_date, build_hdc)
                )
        else:
            for month, next_month in zip(
                summary[1:], [*summary[2:], None], strict=False
            ):
                summary_month = date(day=1, month=month.month, year=month.year)
                # ``add_with_none`` returns the sum; capture it or ``build_hdc``
                # stays at the year's first month's hdc.
                build_hdc = add_with_none(build_hdc, month.hdc)
                # month.summary (and the seed build_summary) may be None when
                # the Toyota API returned partial data.
                if month.summary is not None:
                    if build_summary is None:
                        build_summary = copy.copy(month.summary)
                    else:
                        build_summary += month.summary

                if next_month is None or next_month.year != month.year:
                    end_date = min(
                        to_date, date(day=31, month=12, year=summary_month.year)
                    )
                    # Skip years where every month.summary was None - a hollow
                    # Summary crashes downstream when sensors read its properties.
                    if build_summary is not None:
                        ret.append(
                            Summary(
                                build_summary,
                                self._metric,
                                start_date,
                                end_date,
                                build_hdc,
                            )
                        )
                    if next_month:
                        start_date = date(
                            day=1, month=next_month.month, year=next_month.year
                        )
                        build_hdc = copy.copy(next_month.hdc)
                        build_summary = copy.copy(next_month.summary)

        return ret
