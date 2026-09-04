"""Utilities for manipulating returns for log output tasks."""

from __future__ import annotations

import json
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from httpx import Response


class SensitiveDataType(Enum):
    """Types of sensitive data that need special handling."""

    STRING = auto()
    FLOAT = auto()


# Default set of sensitive keys that should be censored
DEFAULT_SENSITIVE_KEYS = {
    "vin",
    "uuid",
    "guid",
    "x-guid",
    "authorization",
    "latitude",
    "longitude",
    "link",
    "emergencycontact",
    "remoteuserguid",
    "subscriberguid",
    "contractid",
    "imei",
    "katashiki_code",
    "subscriptionid",
    "cookie",
    "x-tme-token",
    "id",
    "subscription_id",
    "phone_number",
    "phone_numbers",
    "email_address",
    "emails",
    "first_name",
    "lastname",
    "euicc_id",
    "contract_id",
    "start_lat",
    "start_lon",
    "end_lat",
    "end_lon",
    "lat",
    "lon",
}


def censor_string(string: str | None) -> str | None:
    """Censor a string by replacing all characters except the first two with asterisks.

    Args:
        string: The string to be censored

    Returns:
        The censored string with all but first two characters replaced by asterisks

    Examples:
        >>> censor_string("abc123")
        "ab****"
        >>> censor_string("")
        ""

    """
    return string[:2] + "*" * (len(string) - 2) if string else string


def get_sensitive_data_type(
    value: str | float | dict | list | None, key: str, to_censor: set[str]
) -> SensitiveDataType | None:
    """Determine the type of sensitive data handling needed.

    Args:
        value: The value to check
        key: The key associated with the value
        to_censor: Set of keys that should be censored

    Returns:
        The type of sensitive data, or None if not sensitive

    """
    key_lower = key.lower()
    if key_lower in to_censor:
        if isinstance(value, str):
            return SensitiveDataType.STRING
        if isinstance(value, float):
            return SensitiveDataType.FLOAT
    return None


def censor_value(
    value: str | float | dict | list | None, key: str, to_censor: set[str]
) -> str | float | dict | list | None:
    """Censor sensitive values in a given data structure.

    Args:
        value: The value to be censored
        key: The key associated with the value
        to_censor: A set of keys to identify values that need to be censored

    Returns:
        The censored value

    """
    # Sensitive fields usually sit under non-sensitive keys (vehicle_info,
    # payload, ...), so containers are always walked regardless of their key.
    if isinstance(value, dict):
        return censor_all(value, to_censor)
    if isinstance(value, list):
        return [censor_value(item, key, to_censor) for item in value]

    data_type = get_sensitive_data_type(value, key, to_censor)

    if data_type == SensitiveDataType.STRING:
        return censor_string(value)
    if data_type == SensitiveDataType.FLOAT:
        return round(value)

    return value


def censor_all(
    dictionary: dict[str, Any], to_censor: set[str] | None = None
) -> dict[str, Any]:
    """Censor sensitive values in a dictionary.

    Args:
        dictionary: The dictionary to be censored
        to_censor: A set of keys to identify values that need to be censored,
                  defaults to a predefined set of sensitive keys

    Returns:
        The censored dictionary with sensitive values masked

    """
    if to_censor is None:
        to_censor = DEFAULT_SENSITIVE_KEYS

    return {k: censor_value(v, k, to_censor) for k, v in dictionary.items()}


def format_httpx_response(response: Response) -> str:
    """Format an HTTPX response into a readable string representation.

    Args:
        response: The HTTPX response object to format

    Returns:
        A formatted multi-line string representing the request and response

    """
    return (
        f"Request:\n"
        f"  Method : {response.request.method}\n"
        f"  URL    : {response.request.url}\n"
        f"  Headers: {response.request.headers}\n"
        f"  Body   : {response.request.content.decode('utf-8')}\n"
        f"Response:\n"
        f"  Status : ({response.status_code}, {response.reason_phrase})\n"
        f"  Headers: {response.headers}\n"
        f"  Content: {response.content.decode('utf-8')}"
    )


def format_httpx_response_json(response: Response) -> str:
    """Format an HTTPX response into a JSON string representation.

    Args:
        response: The HTTPX response object to format

    Returns:
        A JSON string representation of the request and response

    """
    try:
        content = response.json() if response.content else ""
    except json.JSONDecodeError:
        content = response.content.decode("utf-8") if response.content else ""

    response_data = {
        "request": {
            "method": response.request.method,
            "url": str(response.request.url),
            "headers": response.request.headers.multi_items(),
            "content": response.request.content.decode("utf-8"),
        },
        "response": {
            "status": response.status_code,
            "headers": response.headers.multi_items(),
            "content": content,
        },
    }

    return json.dumps(response_data)
