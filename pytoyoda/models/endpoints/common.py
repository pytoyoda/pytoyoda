"""Toyota Connected Services API - Common Endpoint Models."""

# ruff: noqa: FA100

from typing import Any, Optional, Union

from pydantic import Field

from pytoyoda.utils.models import CustomEndpointBaseModel


class UnitValueModel(CustomEndpointBaseModel):
    """Model representing a unit and a value.

    Can be reused several times within other models.

    Attributes:
        unit: The unit of measurement (e.g., "km", "C", "mph").
        value: The numerical value associated with the unit.

    """

    unit: Optional[str] = None
    value: Optional[float] = None


class _MessageModel(CustomEndpointBaseModel):
    """Model representing an error or status message.

    Attributes:
        description: Brief description of the message.
        detailed_description: More detailed explanation of the message.
        response_code: Code identifying the specific message type.

    """

    description: Optional[str] = None
    detailed_description: Optional[str] = Field(
        alias="detailedDescription", default=None
    )
    response_code: Optional[str] = Field(alias="responseCode", default=None)


class _MessagesModel(CustomEndpointBaseModel):
    """Container model for multiple message objects.

    Attributes:
        messages: List of message objects.

    """

    messages: Optional[list[_MessageModel]] = None


class StatusModel(CustomEndpointBaseModel):
    """Model representing the status of an endpoint response.

    Attributes:
        status: The status of the endpoint, which can be a string (e.g., "success")
            or a _MessagesModel object containing detailed messages.
        code: The HTTP status code or custom status code.
        errors: A list of error details if any occurred.
        message: A human-readable message summarizing the response status.

    """

    status: Optional[Union[str, _MessagesModel]] = None
    code: Optional[int] = None
    errors: Optional[list[Any]] = None
    message: Optional[str] = None
