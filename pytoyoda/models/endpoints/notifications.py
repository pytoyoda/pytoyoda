"""Toyota Connected Services API - Notification Models."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from pytoyoda.utils.models import CustomEndpointBaseModel


class _HeadersModel(CustomEndpointBaseModel):
    """Model representing HTTP headers in notifications.

    Attributes:
        content_type (Optional[str]): The Content-Type header value.

    """

    content_type: str | None = Field(None, alias="Content-Type")


class NotificationModel(CustomEndpointBaseModel):
    """Model representing a notification.

    Attributes:
        message_id (str): The ID of the notification message.
        vin (str): The VIN (Vehicle Identification Number) associated with the
            notification.
        notification_date (datetime): The datetime of the notification.
        is_read (bool): Indicates whether the notification has been read.
        read_timestamp (datetime): The timestamp when the notification was read.
        icon_url (str): The URL of the notification icon.
        message (str): The content of the notification message.
        status (Union[int, str]): The status of the notification.
        type (str): The type of the notification.
        category (str): The category of the notification.
        display_category (str): The display category of the notification.

    """

    message_id: str | None = Field(alias="messageId", default=None)
    vin: str | None = None
    notification_date: datetime | None = Field(alias="notificationDate", default=None)
    is_read: bool | None = Field(alias="isRead", default=None)
    read_timestamp: datetime | None = Field(alias="readTimestamp", default=None)
    icon_url: str | None = Field(alias="iconUrl", default=None)
    message: str | None = None
    status: int | str | None = None
    type: str | None = None
    category: str | None = None
    display_category: str | None = Field(alias="displayCategory", default=None)


class _PayloadItemModel(CustomEndpointBaseModel):
    """Model representing an item in the notification response payload.

    Attributes:
        vin (str): The VIN (Vehicle Identification Number) associated with the
            notifications.
        notifications (list[NotificationModel]): List of notifications for the vehicle.

    """

    vin: str | None = None
    notifications: list[NotificationModel] | None = None


class NotificationResponseModel(CustomEndpointBaseModel):
    """Model representing a notification response.

    Attributes:
        guid (UUID): The GUID (Globally Unique Identifier) of the response.
        status_code (int): The status code of the response.
        headers (HeadersModel): The headers of the response.
        body (str): The body of the response.
        payload (list[PayloadItemModel]): The payload of the response.

    """

    guid: UUID | None = None
    status_code: int | None = Field(alias="statusCode", default=None)
    headers: _HeadersModel | None = None
    body: str | None = None
    payload: list[_PayloadItemModel] | None = None
