"""Simple test for raw data of different API endpoints."""

import asyncio
import json
import sys
from pathlib import Path
from pprint import pformat

from endpoints_to_test import ENDPOINTS_TO_TEST
from loguru import logger

from pytoyoda.client import MyT
from pytoyoda.models.vehicle import Vehicle

logger.remove(0)
logger.add(sys.stderr, level="INFO")
logger.add(f"{Path(__file__).parent / 'endpoint_tester.log'}", level="INFO")

# Set your brand here
# Use "T" for Toyota or "L" for Lexus
BRAND = "T"


async def test_endpoint(myt: MyT, vehicle: Vehicle, method: str, endpoint: str) -> None:
    """Test a specific API endpoint for a given vehicle.

    Args:
        myt (MyT): An instance of the MyT client used to make API requests.
        vehicle (Vehicle): The vehicle object containing the VIN to test against.
        method (str): The HTTP method to use for the request (e.g., 'GET').
        endpoint (str): The API endpoint to test.

    Returns:
        None: This function does not return any value. It logs the results of the test.

    """
    logger.info(f"Testing Endpoint: {endpoint}")
    try:
        response = await myt._api.controller.request_raw(
            method,
            endpoint,
            vin=vehicle.vin,
            headers={"X-device-timezone": "Europe/Berlin"},
        )
    except Exception as e:
        logger.error(f"EXCEPTION:\n{e}")
        return
    if response:
        logger.info(f"Status: {response.status_code},{response.reason_phrase}")
        logger.info(f"Headers:\n{pformat(response.headers, indent=2)}")
        logger.info(f"{endpoint} response:")
        try:
            j = json.loads(response.content.decode("utf-8"))
            logger.info(f"{pformat(j, indent=2)}")
        except Exception:
            r = response.content.decode("utf-8")
            logger.error(
                f"ERROR:\nError trying to decode data into json for: {pformat(r, indent=2)}"  # noqa: E501
            )
    else:
        logger.error(f"FAILED:\n{response.reason_phrase}({response.status_code}")


def load_credentials():
    """Load credentials from 'credentials.json'.

    This function attempts to read a JSON file containing user credentials
    for the MyT client. If the file does not exist or contains invalid JSON,
    it returns None.

    Returns:
        dict or None: A dictionary containing the username and password if
        successfully loaded, otherwise None.

    """
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

USERNAME = credentials["username"]
PASSWORD = credentials["password"]

client = MyT(username=USERNAME, password=PASSWORD, use_metric=True, brand=BRAND)


async def main():
    """Log in and test API endpoints.

    This function logs into the MyT client, retrieves the vehicles associated
    with the account, and tests predefined API endpoints for each vehicle.

    Returns:
        None: This function does not return any value. It performs logging
        and endpoint testing.

    """
    logger.info("Logging in...")
    await client.login()

    logger.info("Retrieving cars...")
    cars = await client.get_vehicles()
    assert len(cars) > 0

    for car in cars:
        if car:
            for url in ENDPOINTS_TO_TEST:
                await test_endpoint(client, car, "GET", url.strip())


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(main())
loop.close()
