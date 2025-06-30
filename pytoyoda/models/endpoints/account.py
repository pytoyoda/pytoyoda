"""Toyota Connected Services API - Account Models."""

# ruff: noqa: FA100

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class _TermsActivityModel(CustomEndpointBaseModel):
    """Model for terms and conditions activity."""

    time_stamp: Optional[datetime] = Field(alias="timeStamp")
    version: Optional[str]


class _AdditionalAttributesModel(CustomEndpointBaseModel):
    """Model for additional account attributes."""

    is_terms_accepted: Optional[bool] = Field(alias="isTermsAccepted")
    terms_activity: Optional[list[_TermsActivityModel]] = Field(
        alias="termsActivity", default=None
    )


class _EmailModel(CustomEndpointBaseModel):
    email_address: Optional[str] = Field(alias="emailAddress")
    email_type: Optional[str] = Field(alias="emailType")
    email_verified: Optional[bool] = Field(alias="emailVerified")
    verification_date: Optional[datetime] = Field(alias="verificationDate")


class _PhoneNumberModel(CustomEndpointBaseModel):
    """Model for phone number information."""

    country_code: Optional[int] = Field(alias="countryCode")
    phone_number: Optional[int] = Field(alias="phoneNumber")
    phone_verified: Optional[bool] = Field(alias="phoneVerified")
    verification_date: Optional[datetime] = Field(alias="verificationDate")


class _CustomerModel(CustomEndpointBaseModel):
    """Model for customer information."""

    account_status: Optional[str] = Field(alias="accountStatus")
    additional_attributes: Optional[_AdditionalAttributesModel] = Field(
        alias="additionalAttributes"
    )
    create_date: Optional[datetime] = Field(alias="createDate")
    create_source: Optional[str] = Field(alias="createSource")
    customer_type: Optional[str] = Field(alias="customerType")
    emails: Optional[list[_EmailModel]]
    first_name: Optional[str] = Field(alias="firstName")
    forge_rock_id: Optional[UUID] = Field(alias="forgerockId")
    guid: Optional[UUID]
    is_cp_migrated: Optional[bool] = Field(alias="isCpMigrated")
    last_name: Optional[str] = Field(alias="lastName")
    last_update_date: Optional[datetime] = Field(alias="lastUpdateDate")
    last_update_source: Optional[str] = Field(alias="lastUpdateSource")
    phone_numbers: Optional[list[_PhoneNumberModel]] = Field(alias="phoneNumbers")
    preferred_language: Optional[str] = Field(alias="preferredLanguage")
    signup_type: Optional[str] = Field(alias="signupType")
    ui_language: Optional[str] = Field(alias="uiLanguage")


class AccountModel(CustomEndpointBaseModel):
    """Model representing an account.

    Attributes:
        customer (_CustomerModel): The customer associated with the account.

    """

    customer: Optional[_CustomerModel]


class AccountResponseModel(StatusModel):
    """Model representing an account response.

    Inherits from StatusModel.

    Attributes:
        payload (Optional[AccountModel]): The account payload.
            Defaults to None.

    """

    payload: Optional[AccountModel] = None
