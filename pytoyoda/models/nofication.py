"""Models for vehicle notifications."""

from datetime import datetime

from pydantic import computed_field

from pytoyoda.models.endpoints.notifications import NotificationModel
from pytoyoda.utils.models import CustomAPIBaseModel


class Notification(CustomAPIBaseModel[NotificationModel]):
    """Notification."""

    def __init__(self, notification: NotificationModel, **kwargs: dict) -> None:
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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def category(self) -> str | None:
        """Category of notification.

        For example, ChargingAlert, RemoteCommand

        Returns:
            str: Category of notification

        """
        return self._data.category

    @computed_field  # type: ignore[prop-decorator]
    @property
    def read(self) -> datetime | None:
        """Notification has been read.

        Returns:
            datetime: Time notification read. None if not read.

        """
        return self._data.read_timestamp

    @computed_field  # type: ignore[prop-decorator]
    @property
    def message(self) -> str | None:
        """Notification message.

        Returns:
            str: Notification message

        """
        return self._data.message

    @computed_field  # type: ignore[prop-decorator]
    @property
    def type(self) -> str | None:
        """Type.

        For example, Alert

        Returns:
            str: Notification type

        """
        return self._data.type

    @computed_field  # type: ignore[prop-decorator]
    @property
    def date(self) -> datetime | None:
        """Notification Date.

        Returns:
            datetime: Time of notification

        """
        return self._data.notification_date
