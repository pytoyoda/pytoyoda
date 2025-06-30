"""Models for vehicle service history."""

# ruff: noqa: FA100

from datetime import date
from typing import Any, Optional, TypeVar, Union

from pydantic import computed_field

from pytoyoda.const import KILOMETERS_UNIT, MILES_UNIT
from pytoyoda.models.endpoints.service_history import ServiceHistoryModel
from pytoyoda.utils.conversions import convert_distance
from pytoyoda.utils.models import CustomAPIBaseModel

T = TypeVar(
    "T",
    bound=Union[ServiceHistoryModel, bool],
)


class ServiceHistory(CustomAPIBaseModel[type[T]]):
    """ServiceHistory."""

    def __init__(
        self,
        service_history: Optional[ServiceHistoryModel] = None,
        metric: bool = True,  # noqa : FBT001, FBT002
        **kwargs: dict,
    ) -> None:
        """Initialise ServiceHistory."""
        data = {
            "service_history": service_history,
            "metric": metric,
        }
        super().__init__(data=data, **kwargs)  # type: ignore[reportArgumentType, arg-type]

        self._service_history: Optional[ServiceHistoryModel] = service_history or None
        self._distance_unit: str = KILOMETERS_UNIT if metric else MILES_UNIT

    @computed_field  # type: ignore[prop-decorator]
    @property
    def service_date(self) -> Optional[date]:
        """The date of the service.

        Returns:
            date: The date of the service.

        """
        return self._service_history.service_date if self._service_history else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def customer_created_record(self) -> Optional[bool]:
        """Indication whether it is an entry created by the user.

        Returns:
            bool: Indicator for customer created record

        """
        return (
            self._service_history.customer_created_record
            if self._service_history
            else None
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def odometer(self) -> Optional[float]:
        """Odometer distance at the time of servicing.

        Returns:
            Optional[float]: Odometer distance at the time of servicing
                in the current selected units

        """
        if (
            self._service_history is not None
            and self._service_history.unit is not None
            and self._service_history.mileage is not None
        ):
            return convert_distance(
                self._distance_unit,
                self._service_history.unit,
                self._service_history.mileage,
            )
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def notes(self) -> Optional[Any]:  # noqa : ANN401
        """Additional notes about the service.

        Returns:
            Any: Additional notes about the service

        """
        return self._service_history.notes if self._service_history else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def operations_performed(self) -> Optional[Any]:  # noqa : ANN401
        """The operations performed during the service.

        Returns:
            Any: The operations performed during the service

        """
        return (
            self._service_history.operations_performed
            if self._service_history
            else None
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ro_number(self) -> Optional[Any]:  # noqa : ANN401
        """The RO (Repair Order) number associated with the service.

        Returns:
            Any: The RO (Repair Order) number associated with the service

        """
        return self._service_history.ro_number if self._service_history else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def service_category(self) -> Optional[str]:
        """The category of the service.

        Returns:
            str: The category of the service.

        """
        return self._service_history.service_category if self._service_history else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def service_provider(self) -> Optional[str]:
        """The service provider.

        Returns:
            str: The service provider

        """
        return self._service_history.service_provider if self._service_history else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def servicing_dealer(self) -> Optional[Any]:  # noqa : ANN401
        """Dealer that performed the service.

        Returns:
            Any: The dealer that performed the service

        """
        return self._service_history.servicing_dealer if self._service_history else None
