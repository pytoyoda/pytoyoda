"""Toyota Connected Services API - Account Models."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class _TermsActivityModel(CustomEndpointBaseModel):
    """Model for terms and conditions activity."""

    time_stamp: datetime | None = Field(alias="timeStamp", default=None)
    version: str | None = None


class _AdditionalAttributesModel(CustomEndpointBaseModel):
    """Model for additional account attributes."""

    is_terms_accepted: bool | None = Field(alias="isTermsAccepted", default=None)
    terms_activity: list[_TermsActivityModel] | None = Field(
        alias="termsActivity", default=None
    )


class _EmailModel(CustomEndpointBaseModel):
    email_address: str | None = Field(alias="emailAddress", default=None)
    email_type: str | None = Field(alias="emailType", default=None)
    email_verified: bool | None = Field(alias="emailVerified", default=None)
    verification_date: datetime | None = Field(alias="verificationDate", default=None)


class _PhoneNumberModel(CustomEndpointBaseModel):
    """Model for phone number information."""

    country_code: int | None = Field(alias="countryCode", default=None)
    phone_number: int | None = Field(alias="phoneNumber", default=None)
    phone_verified: bool | None = Field(alias="phoneVerified", default=None)
    verification_date: datetime | None = Field(alias="verificationDate", default=None)


class _CustomerModel(CustomEndpointBaseModel):
    """Model for customer information."""

    account_status: str | None = Field(alias="accountStatus", default=None)
    additional_attributes: _AdditionalAttributesModel | None = Field(
        alias="additionalAttributes", default=None
    )
    create_date: datetime | None = Field(alias="createDate", default=None)
    create_source: str | None = Field(alias="createSource", default=None)
    customer_type: str | None = Field(alias="customerType", default=None)
    emails: list[_EmailModel] | None = None
    first_name: str | None = Field(alias="firstName", default=None)
    forge_rock_id: UUID | None = Field(alias="forgerockId", default=None)
    guid: UUID | None = None
    is_cp_migrated: bool | None = Field(alias="isCpMigrated", default=None)
    last_name: str | None = Field(alias="lastName", default=None)
    last_update_date: datetime | None = Field(alias="lastUpdateDate", default=None)
    last_update_source: str | None = Field(alias="lastUpdateSource", default=None)
    phone_numbers: list[_PhoneNumberModel] | None = Field(
        alias="phoneNumbers", default=None
    )
    preferred_language: str | None = Field(alias="preferredLanguage", default=None)
    signup_type: str | None = Field(alias="signupType", default=None)
    ui_language: str | None = Field(alias="uiLanguage", default=None)


class AccountModel(CustomEndpointBaseModel):
    """Model representing an account.

    Attributes:
        customer (_CustomerModel): The customer associated with the account.

    """

    customer: _CustomerModel | None = None


class AccountResponseModel(StatusModel):
    """Model representing an account response.

    Inherits from StatusModel.

    Attributes:
        payload (Optional[AccountModel]): The account payload.
            Defaults to None.

    """

    payload: AccountModel | None = None
