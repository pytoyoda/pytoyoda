"""Client for connecting to Toyota Connected Services.

A client for connecting to MyT (Toyota Connected Services) and retrieving vehicle
information, sensor data, fuel level, driving statistics and more.

Example:
    ```python
    client = MyT(username="user@example.com", password="password", use_metric=True)
    await client.login()
    vehicles = await client.get_vehicles()
    for vehicle in vehicles:
        await vehicle.update()
        print(f"Dashboard: {vehicle.dashboard}")
    ```

"""

from __future__ import annotations

from loguru import logger

from pytoyoda.api import Api
from pytoyoda.controller import Controller
from pytoyoda.exceptions import ToyotaInvalidUsernameError, ToyotaLoginError
from pytoyoda.models.vehicle import Vehicle


class MyT:
    """Toyota Connected Services client.

    Provides a simple interface to access Toyota Connected Services data
    for vehicles associated with a Toyota account.

    Attributes:
        username: The email address used for Toyota account login
        password: The password used for Toyota account login
        use_metric: Whether to use metric units (True) or imperial units (False)

    """

    def __init__(
        self,
        username: str,
        password: str,
        use_metric: bool = True,  # noqa : FBT001, FBT002
        brand: str = "T",
        controller_class: type[Controller] = Controller,
    ) -> None:
        """Initialize the Toyota Connected Services client.

        Args:
            username: Email address for Toyota account login
            password: Password for Toyota account
            use_metric: Whether to use metric units (True) or imperial units (False)
            brand: Brand of the car (T for Toyota, L for Lexus)
            controller_class: Controller class to use for API communication

        Raises:
            ToyotaInvalidUsernameError: If username is invalid or missing @ symbol

        """
        if not username or "@" not in username:
            msg = "Invalid username format. Must be a valid email address."
            raise ToyotaInvalidUsernameError(msg)

        self._api = Api(
            controller_class(
                username=username,
                password=password,
                brand=brand,
            ),
        )
        self._use_metric = use_metric

        logger.debug("MyT client initialized for user: '{}'.", username)

    async def login(self) -> None:
        """Perform initial login to Toyota Connected Services.

        This should be called before making any API requests to ensure
        proper authentication. It will fetch and store access tokens
        for subsequent requests.

        Raises:
            ToyotaLoginError: If login fails for any reason

        """
        logger.debug("Performing initial login")
        try:
            await self._api.controller.login()
            logger.debug("Login successful")
        except ToyotaLoginError as error:
            logger.error("Login failed: '{}'.", str(error))
            raise

    async def get_vehicles(self) -> list[Vehicle | None]:
        """Retrieve all vehicles associated with the account.

        Returns:
            List of Vehicle objects associated with the account. Empty list if no
            vehicles are found.

        Raises:
            ToyotaLoginError: If not properly authenticated

        """
        logger.debug("Retrieving vehicles associated with account")

        vehicles = await self._api.get_vehicles()

        if not vehicles.payload:
            logger.info("No vehicles found for this account")
            return []

        logger.debug("Found {} vehicles", len(vehicles.payload))

        return [
            Vehicle(self._api, vehicle_data, metric=self._use_metric)
            for vehicle_data in vehicles.payload
        ]
