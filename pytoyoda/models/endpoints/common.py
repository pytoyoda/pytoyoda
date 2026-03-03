"""Toyota Connected Services API - Common Endpoint Models."""

from typing import Any

from pydantic import Field

from pytoyoda.utils.models import CustomEndpointBaseModel


class UnitValueModel(CustomEndpointBaseModel):
    """Model representing a unit and a value.

    Can be reused several times within other models.

    Attributes:
        unit: The unit of measurement (e.g., "km", "C", "mph").
        value: The numerical value associated with the unit.

    """

    unit: str | None = None
    value: float | None = None


class _MessageModel(CustomEndpointBaseModel):
    """Model representing an error or status message.

    Attributes:
        description: Brief description of the message.
        detailed_description: More detailed explanation of the message.
        response_code: Code identifying the specific message type.

    """

    description: str | None = None
    detailed_description: str | None = Field(alias="detailedDescription", default=None)
    response_code: str | None = Field(alias="responseCode", default=None)


class _MessagesModel(CustomEndpointBaseModel):
    """Container model for multiple message objects.

    Attributes:
        messages: List of message objects.

    """

    messages: list[_MessageModel] | None = None


class StatusModel(CustomEndpointBaseModel):
    """Model representing the status of an endpoint response.

    Attributes:
        status: The status of the endpoint, which can be a string (e.g., "success")
            or a _MessagesModel object containing detailed messages.
        code: The HTTP status code or custom status code.
        errors: A list of error details if any occurred.
        message: A human-readable message summarizing the response status.

    """

    status: str | _MessagesModel | None = None
    code: int | None = None
    errors: list[Any] | None = None
    message: str | None = None
