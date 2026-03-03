"""Toyota Connected Services API - Endpoint Model."""

from datetime import datetime
from typing import Any

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class VehicleHealthModel(CustomEndpointBaseModel):
    r"""Model representing the health status of a vehicle.

    Attributes:
        quantity_of_eng_oil_icon (Optional[list[Any]], optional):
        The quantity of engine oil icon. Defaults to None.
        vin (str): The VIN (Vehicle Identification Number) of the vehicle.
        warning (Optional[list[Any]]): The warning information. Defaults to None.
        wng_last_upd_time (datetime): The timestamp of the last warning update.

    """

    quantity_of_eng_oil_icon: list[Any] | None = Field(alias="quantityOfEngOilIcon")
    vin: str | None
    warning: list[Any] | None
    wng_last_upd_time: datetime | None = Field(alias="wnglastUpdTime")


class VehicleHealthResponseModel(StatusModel):
    r"""Model representing a vehicle health response.

    Inherits from StatusModel.

    Attributes:
        payload (Optional[VehicleHealthModel], optional): The vehicle health payload.
            Defaults to None.

    """

    payload: VehicleHealthModel | None = None
