"""Models for vehicle notifications."""

from datetime import datetime
from typing import Optional

from pydantic import computed_field

from pytoyoda.models.endpoints.notifications import NotificationModel
from pytoyoda.utils.models import CustomAPIBaseModel


class Notification(CustomAPIBaseModel[NotificationModel]):
    """Notification."""

    def __init__(self, notification: NotificationModel, **kwargs):
        """Initialize Notification model.

        Args:
            notification (NotificationModel): Contains current notification
                information
            **kwargs: Additional keyword arguments passed to the parent class

        """
        super().__init__(
            data=notification,
            **kwargs,
        )

    @computed_field
    @property
    def category(self) -> str:
        """Category of notification.

        For example, ChargingAlert, RemoteCommand

        Returns:
            str: Category of notification

        """
        return self._data.category

    @computed_field
    @property
    def read(self) -> Optional[datetime]:
        """Notification has been read.

        Returns:
            datetime: Time notification read. None if not read.

        """
        return self._data.read_timestamp

    @computed_field
    @property
    def message(self) -> str:
        """Notification message.

        Returns:
            str: Notification message

        """
        return self._data.message

    @computed_field
    @property
    def type(self) -> str:
        """Type.

        For example, Alert

        Returns:
            str: Notification type

        """
        return self._data.type

    @computed_field
    @property
    def date(self) -> datetime:
        """Notification Date.

        Returns:
            datetime: Time of notification

        """
        return self._data.notification_date
