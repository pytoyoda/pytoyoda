"""Simple test of new API Changes."""

import asyncio
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from loguru import logger

from pytoyoda.client import MyT
from pytoyoda.models.summary import SummaryType

# from pytoyoda.models.endpoints.climate import ACOperations, ACParameters, ClimateSettingsModel  # noqa: E501
# from pytoyoda.models.endpoints.command import CommandType

logger.remove(0)
logger.add(sys.stderr, level="INFO")


# Set your username and password in a file inside the "sandbox" folder called "credentials.json" in the format: # noqa: E501
#   {
#       "username": "<username>",
#       "password": "<password>"
#   }


def load_credentials():
    """Load credentials from 'credentials.json'."""
    try:
        with open(Path(__file__).parent / "credentials.json", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return None


credentials = load_credentials()
if not credentials:
    raise ValueError(
        "Did you forget to set your username and password?"
        "Or supply the credentials file inside the 'sandbox' folder?"
    )

USERNAME = credentials["vecapetr@seznam.cz"]
PASSWORD = credentials["PetrVecera69"]

client = MyT(username=USERNAME, password=PASSWORD, use_metric=True)


async def get_information():
    """Test login and output from endpoints."""
    logger.info("Logging in...")
    await client.login()

    logger.info("Retrieving cars...")
    cars = await client.get_vehicles()

    for car in cars:
        # Send command to car
        # logger.info(await car.post_command(command=CommandType.DOOR_LOCK))
        # return
        # Get climate status
        # response = await car._api.get_climate_status(car.vin)
        # print(response)

        # Get current climate settings
        # settings = await car._api.get_climate_settings(car.vin)
        # print(settings)
        # climate_settings: ClimateSettingsModel = ClimateSettingsModel(
        #   settingsOn=True,
        #   temperature=21,
        #   temperatureUnit="C",
        #   acOperations=[ACOperations(
        #       categoryName="defrost",
        #       acParameters=[ACParameters(enabled=True, name="frontDefrost"),
        #       ACParameters(enabled=False, name="rearDefrost")])])
        # climate_settings = settings.payload
        # climate_settings.temperature = 20
        # response = await car._api.update_climate_settings(car.vin, climate_settings)  # noqa: E501
        # print(response)
        # return

        if car:
            await car.update()

            # Dashboard Information
            logger.info(
                f"Dashboard: {car.dashboard.model_dump_json(indent=4) if car.dashboard else None}"  # noqa: E501
            )
            # Electric Status Information
            logger.info(
                f"Electric Status: {car.electric_status.model_dump_json(indent=4) if car.electric_status else None}"  # noqa: E501
            )
            # Location Information
            logger.info(
                f"Location: {car.location.model_dump_json(indent=4) if car.location else None}"  # noqa: E501
            )
            # Lock Status
            logger.info(
                f"Lock Status: {car.lock_status.model_dump_json(indent=4) if car.lock_status else None}"  # noqa: E501
            )
            # Notifications
            logger.info(
                f"Notifications: {[x.model_dump_json(indent=4) for x in car.notifications] if car.notifications else None}"  # noqa: E501
            )
            # Service history
            logger.info(
                f"Latest service: {car.get_latest_service_history().model_dump_json(indent=4) if car.get_latest_service_history() else None}"  # noqa: E501
            )
            # Last trip
            logger.info(
                f"Last trip: {car.last_trip.model_dump_json(indent=4) if car.last_trip else None}"  # noqa: E501
            )
            # Daily summary
            logger.info(f"Daily summary: {await car.get_current_day_summary()}")
            # Summary
            summaries = await car.get_summary(
                date.today() - timedelta(days=6 * 30),
                date.today(),
                summary_type=SummaryType.MONTHLY,
            )
            logger.info("Monthly summaries:")
            for x in summaries:
                logger.info(x.model_dump_json(indent=4))

            # Trips
            # Uncommenting this can lead to a very long list of route positions
            # trips = await car.get_trips(date.today() - timedelta(days=1), date.today(), full_route=True)   # noqa: E501
            # logger.info(f"Trips: {[x.model_dump_json(indent=4) for x in trips] if trips else None}")   # noqa: E501

            # Dump all the information collected so far:
            # logger.info(pformat(car._dump_all()))


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(get_information())
loop.close()
