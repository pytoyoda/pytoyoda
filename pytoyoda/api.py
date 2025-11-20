"""Toyota Connected Services API."""

from datetime import date, datetime, timezone
from typing import Any, TypeVar, Union
from uuid import uuid4

from loguru import logger

from pytoyoda.const import (
    VEHICLE_ASSOCIATION_ENDPOINT,
    VEHICLE_CLIMATE_CONTROL_ENDPOINT,
    VEHICLE_CLIMATE_SETTINGS_ENDPOINT,
    VEHICLE_CLIMATE_STATUS_ENDPOINT,
    VEHICLE_CLIMATE_STATUS_REFRESH_ENDPOINT,
    VEHICLE_COMMAND_ENDPOINT,
    VEHICLE_GLOBAL_REMOTE_ELECTRIC_CONTROL_ENDPOINT,
    VEHICLE_GLOBAL_REMOTE_ELECTRIC_REALTIME_STATUS_ENDPOINT,
    VEHICLE_GLOBAL_REMOTE_ELECTRIC_STATUS_ENDPOINT,
    VEHICLE_GLOBAL_REMOTE_STATUS_ENDPOINT,
    VEHICLE_GUID_ENDPOINT,
    VEHICLE_HEALTH_STATUS_ENDPOINT,
    VEHICLE_LOCATION_ENDPOINT,
    VEHICLE_NOTIFICATION_HISTORY_ENDPOINT,
    VEHICLE_SERVICE_HISTORY_ENDPONT,
    VEHICLE_TELEMETRY_ENDPOINT,
    VEHICLE_TRIPS_ENDPOINT,
)
from pytoyoda.controller import Controller
from pytoyoda.models.endpoints.climate import (
    ClimateControlModel,
    ClimateSettingsModel,
    ClimateSettingsResponseModel,
    ClimateStatusResponseModel,
)
from pytoyoda.models.endpoints.command import CommandType, RemoteCommandModel
from pytoyoda.models.endpoints.common import StatusModel
from pytoyoda.models.endpoints.electric import ElectricResponseModel, NextChargeSettings
from pytoyoda.models.endpoints.location import LocationResponseModel
from pytoyoda.models.endpoints.notifications import NotificationResponseModel
from pytoyoda.models.endpoints.service_history import ServiceHistoryResponseModel
from pytoyoda.models.endpoints.status import RemoteStatusResponseModel
from pytoyoda.models.endpoints.telemetry import TelemetryResponseModel
from pytoyoda.models.endpoints.trips import TripsResponseModel
from pytoyoda.models.endpoints.vehicle_guid import VehiclesResponseModel
from pytoyoda.models.endpoints.vehicle_health import VehicleHealthResponseModel

# Type variable for generic model handling
T = TypeVar(
    "T",
    bound=Union[
        StatusModel,
        ElectricResponseModel,
        LocationResponseModel,
        NotificationResponseModel,
        ServiceHistoryResponseModel,
        RemoteStatusResponseModel,
        TelemetryResponseModel,
        TripsResponseModel,
        VehiclesResponseModel,
        VehicleHealthResponseModel,
    ],
)


class Api:
    """API for Toyota Connected Services.

    This class provides access to Toyota Connected Services endpoints to
    retrieve and manipulate vehicle data.

    """

    def __init__(self, controller: Controller) -> None:
        """Initialize the API with a controller for communication.

        Args:
            controller: A controller instance to manage the API communication

        """
        self.controller = controller

    async def _request_and_parse(
        self,
        model: type[T],
        method: str,
        endpoint: str,
        **kwargs,  # noqa : ANN003
    ) -> T:
        """Parse requests and responses using Pydantic models.

        Args:
            model: Pydantic model class to parse response into
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to request method

        Returns:
            Parsed response data as specified model instance

        """
        response = await self.controller.request_json(
            method=method, endpoint=endpoint, **kwargs
        )
        parsed_response = model(**response)
        logger.debug(f"Parsed '{model.__name__}': {parsed_response}")
        return parsed_response

    async def _create_standard_headers(self) -> dict[str, str]:
        """Create standard headers for API requests.

        Returns:
            Dictionary with standard headers

        """
        return {
            "datetime": str(int(datetime.now(timezone.utc).timestamp() * 1000)),
            "x-correlationid": str(uuid4()),
            "Content-Type": "application/json",
        }

    # Vehicle Management

    async def set_vehicle_alias(self, alias: str, guid: str, vin: str) -> Any:  # noqa :ANN401
        """Set a nickname/alias for a vehicle.

        Args:
            alias: New nickname for the vehicle
            guid: Global unique identifier for the vehicle
            vin: Vehicle Identification Number

        Returns:
            Raw response from the API

        """
        return await self.controller.request_raw(
            method="PUT",
            endpoint=VEHICLE_ASSOCIATION_ENDPOINT,
            vin=vin,
            headers=await self._create_standard_headers(),
            body={"guid": guid, "vin": vin, "nickName": alias},
        )

    async def get_vehicles(self) -> VehiclesResponseModel:
        """Get a list of vehicles registered with the Toyota account.

        Returns:
            Model containing vehicle information

        """
        return await self._request_and_parse(
            VehiclesResponseModel, "GET", VEHICLE_GUID_ENDPOINT
        )

    # Vehicle Status and Information

    async def get_location(self, vin: str) -> LocationResponseModel:
        """Get the last known location of a vehicle.

        Only updates when car is parked.
        Includes latitude and longitude if supported.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Model containing location information

        """
        return await self._request_and_parse(
            LocationResponseModel, "GET", VEHICLE_LOCATION_ENDPOINT, vin=vin
        )

    async def get_vehicle_health_status(self, vin: str) -> VehicleHealthResponseModel:
        """Get the latest health status of a vehicle.

        Includes engine oil quantity and dashboard warning lights if supported.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Model containing vehicle health information

        """
        return await self._request_and_parse(
            VehicleHealthResponseModel, "GET", VEHICLE_HEALTH_STATUS_ENDPOINT, vin=vin
        )

    async def get_remote_status(self, vin: str) -> RemoteStatusResponseModel:
        """Get general information about a vehicle.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Model containing general vehicle status

        """
        return await self._request_and_parse(
            RemoteStatusResponseModel,
            "GET",
            VEHICLE_GLOBAL_REMOTE_STATUS_ENDPOINT,
            vin=vin,
        )

    async def get_vehicle_electric_status(self, vin: str) -> ElectricResponseModel:
        """Get the latest electric status of a vehicle.

        Includes current battery level, EV range, fuel level, and charging status.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Model containing electric vehicle information

        """
        return await self._request_and_parse(
            ElectricResponseModel,
            "GET",
            VEHICLE_GLOBAL_REMOTE_ELECTRIC_STATUS_ENDPOINT,
            vin=vin,
        )

    async def refresh_electric_realtime_status(self, vin: str) -> StatusModel:
        """Update realtime SOC.

        Only requests a updated soc

        Args:
            vin: Vehicle Identification Number

        Returns:
            Model containing status of the refresh request

        """
        return await self._request_and_parse(
            StatusModel,
            "POST",
            VEHICLE_GLOBAL_REMOTE_ELECTRIC_REALTIME_STATUS_ENDPOINT,
            vin=vin,
        )

    async def get_telemetry(self, vin: str) -> TelemetryResponseModel:
        """Get the latest telemetry data for a vehicle.

        Includes current fuel level, distance to empty, and odometer.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Model containing telemetry information

        """
        return await self._request_and_parse(
            TelemetryResponseModel, "GET", VEHICLE_TELEMETRY_ENDPOINT, vin=vin
        )

    # Notifications and History

    async def get_notifications(self, vin: str) -> NotificationResponseModel:
        """Get all available notifications for a vehicle.

        Includes message text, notification date, read flag, and date read.
        Note: No way to mark notifications as read or limit the response.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Model containing notification information

        """
        return await self._request_and_parse(
            NotificationResponseModel,
            "GET",
            VEHICLE_NOTIFICATION_HISTORY_ENDPOINT,
            vin=vin,
        )

    async def get_service_history(self, vin: str) -> ServiceHistoryResponseModel:
        """Get the service history for a vehicle.

        Includes service category, date, and dealer information.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Model containing service history information

        """
        return await self._request_and_parse(
            ServiceHistoryResponseModel, "GET", VEHICLE_SERVICE_HISTORY_ENDPONT, vin=vin
        )

    # Climate Control

    async def get_climate_status(self, vin: str) -> ClimateStatusResponseModel:
        """Get the current climate control status.

        Note: Only returns data if climate control is on. If off,
        it returns status == 0 and all other fields are None.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Model containing climate status information

        """
        return await self._request_and_parse(
            ClimateStatusResponseModel,
            "GET",
            VEHICLE_CLIMATE_STATUS_ENDPOINT,
            vin=vin,
        )

    async def refresh_climate_status(self, vin: str) -> StatusModel:
        """Request an update to the climate status from the vehicle.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Model containing status of the refresh request

        """
        return await self._request_and_parse(
            StatusModel, "POST", VEHICLE_CLIMATE_STATUS_REFRESH_ENDPOINT, vin=vin
        )

    async def get_climate_settings(self, vin: str) -> ClimateSettingsResponseModel:
        """Get the current climate control settings.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Model containing climate settings information

        """
        return await self._request_and_parse(
            ClimateSettingsResponseModel,
            "GET",
            VEHICLE_CLIMATE_SETTINGS_ENDPOINT,
            vin=vin,
        )

    async def update_climate_settings(
        self, vin: str, settings: ClimateSettingsModel
    ) -> StatusModel:
        """Update the climate control settings for a vehicle.

        Args:
            vin: Vehicle Identification Number
            settings: New climate control settings

        Returns:
            Model containing status of the update request

        """
        return await self._request_and_parse(
            StatusModel,
            "PUT",
            VEHICLE_CLIMATE_SETTINGS_ENDPOINT,
            vin=vin,
            body=settings.model_dump(exclude_unset=True, by_alias=True),
        )

    async def send_climate_control_command(
        self, vin: str, command: ClimateControlModel
    ) -> StatusModel:
        """Send a control command to the climate system.

        Args:
            vin: Vehicle Identification Number
            command: Climate control command to send

        Returns:
            Model containing status of the command request

        """
        return await self._request_and_parse(
            StatusModel,
            "POST",
            VEHICLE_CLIMATE_CONTROL_ENDPOINT,
            vin=vin,
            body=command.model_dump(exclude_unset=True, by_alias=True),
        )

    # Trip Data

    async def get_trips(  # noqa: PLR0913
        self,
        vin: str,
        from_date: date,
        to_date: date,
        route: bool = False,  # noqa : FBT001, FBT002
        summary: bool = True,  # noqa : FBT001, FBT002
        limit: int = 5,
        offset: int = 0,
    ) -> TripsResponseModel:
        """Get a list of trips for a vehicle within a date range.

        Args:
            vin: Vehicle Identification Number
            from_date: Start date for trip data (inclusive, cannot be in future)
            to_date: End date for trip data (inclusive, cannot be in future)
            route: If True, returns route coordinates for each trip
            summary: If True, returns monthly and daily trip summaries
            limit: Maximum number of trips to return (max 50)
            offset: Starting offset for pagination

        Returns:
            Model containing trip information

        """
        endpoint = VEHICLE_TRIPS_ENDPOINT.format(
            from_date=from_date,
            to_date=to_date,
            route=route,
            summary=summary,
            limit=limit,
            offset=offset,
        )
        return await self._request_and_parse(
            TripsResponseModel, "GET", endpoint, vin=vin
        )

    # Remote Commands

    async def send_command(
        self, vin: str, command: CommandType, beeps: int = 0
    ) -> StatusModel:
        """Send a remote command to a vehicle.

        Args:
            vin: Vehicle Identification Number
            command: Type of command to send
            beeps: Number of beeps for commands that support it

        Returns:
            Model containing status of the command request

        """
        remote_command = RemoteCommandModel(beep_count=beeps, command=command)
        return await self._request_and_parse(
            StatusModel,
            "POST",
            VEHICLE_COMMAND_ENDPOINT,
            vin=vin,
            body=remote_command.model_dump(exclude_unset=True, by_alias=True),
        )

    async def send_next_charging_command(
        self, vin: str, command: NextChargeSettings
    ) -> ElectricResponseModel:
        """Send the next charging start/end time to the vehicle.

        Args:
            vin: Vehicle Identification Number
            command: NextChargeSettings command to send

        Returns:
            Model containing status of the command request

        """
        return await self._request_and_parse(
            ElectricResponseModel,
            "POST",
            VEHICLE_GLOBAL_REMOTE_ELECTRIC_CONTROL_ENDPOINT,
            vin=vin,
            body=command.model_dump(exclude_none=True, by_alias=True),
        )
