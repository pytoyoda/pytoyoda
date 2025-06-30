"""Toyota Connected Services API - Notification Models."""

# ruff: noqa: FA100

from datetime import datetime
from typing import Optional, Union
from uuid import UUID

from pydantic import Field

from pytoyoda.utils.models import CustomEndpointBaseModel


class _HeadersModel(CustomEndpointBaseModel):
    """Model representing HTTP headers in notifications.

    Attributes:
        content_type (Optional[str]): The Content-Type header value.

    """

    content_type: Optional[str] = Field(None, alias="Content-Type")


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

    message_id: Optional[str] = Field(alias="messageId", default=None)
    vin: Optional[str] = None
    notification_date: Optional[datetime] = Field(
        alias="notificationDate", default=None
    )
    is_read: Optional[bool] = Field(alias="isRead", default=None)
    read_timestamp: Optional[datetime] = Field(alias="readTimestamp", default=None)
    icon_url: Optional[str] = Field(alias="iconUrl", default=None)
    message: Optional[str] = None
    status: Optional[Union[int, str]] = None
    type: Optional[str] = None
    category: Optional[str] = None
    display_category: Optional[str] = Field(alias="displayCategory", default=None)


class _PayloadItemModel(CustomEndpointBaseModel):
    """Model representing an item in the notification response payload.

    Attributes:
        vin (str): The VIN (Vehicle Identification Number) associated with the
            notifications.
        notifications (list[NotificationModel]): List of notifications for the vehicle.

    """

    vin: Optional[str] = None
    notifications: Optional[list[NotificationModel]] = None


class NotificationResponseModel(CustomEndpointBaseModel):
    """Model representing a notification response.

    Attributes:
        guid (UUID): The GUID (Globally Unique Identifier) of the response.
        status_code (int): The status code of the response.
        headers (HeadersModel): The headers of the response.
        body (str): The body of the response.
        payload (list[PayloadItemModel]): The payload of the response.

    """

    guid: Optional[UUID] = None
    status_code: Optional[int] = Field(alias="statusCode", default=None)
    headers: Optional[_HeadersModel] = None
    body: Optional[str] = None
    payload: Optional[list[_PayloadItemModel]] = None
