"""Toyota Connected Services API - Account Models."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class _TermsActivityModel(CustomEndpointBaseModel):
    """Model for terms and conditions activity."""

    time_stamp: datetime | None = Field(alias="timeStamp")
    version: str | None


class _AdditionalAttributesModel(CustomEndpointBaseModel):
    """Model for additional account attributes."""

    is_terms_accepted: bool | None = Field(alias="isTermsAccepted")
    terms_activity: list[_TermsActivityModel] | None = Field(
        alias="termsActivity", default=None
    )


class _EmailModel(CustomEndpointBaseModel):
    email_address: str | None = Field(alias="emailAddress")
    email_type: str | None = Field(alias="emailType")
    email_verified: bool | None = Field(alias="emailVerified")
    verification_date: datetime | None = Field(alias="verificationDate")


class _PhoneNumberModel(CustomEndpointBaseModel):
    """Model for phone number information."""

    country_code: int | None = Field(alias="countryCode")
    phone_number: int | None = Field(alias="phoneNumber")
    phone_verified: bool | None = Field(alias="phoneVerified")
    verification_date: datetime | None = Field(alias="verificationDate")


class _CustomerModel(CustomEndpointBaseModel):
    """Model for customer information."""

    account_status: str | None = Field(alias="accountStatus")
    additional_attributes: _AdditionalAttributesModel | None = Field(
        alias="additionalAttributes"
    )
    create_date: datetime | None = Field(alias="createDate")
    create_source: str | None = Field(alias="createSource")
    customer_type: str | None = Field(alias="customerType")
    emails: list[_EmailModel] | None
    first_name: str | None = Field(alias="firstName")
    forge_rock_id: UUID | None = Field(alias="forgerockId")
    guid: UUID | None
    is_cp_migrated: bool | None = Field(alias="isCpMigrated")
    last_name: str | None = Field(alias="lastName")
    last_update_date: datetime | None = Field(alias="lastUpdateDate")
    last_update_source: str | None = Field(alias="lastUpdateSource")
    phone_numbers: list[_PhoneNumberModel] | None = Field(alias="phoneNumbers")
    preferred_language: str | None = Field(alias="preferredLanguage")
    signup_type: str | None = Field(alias="signupType")
    ui_language: str | None = Field(alias="uiLanguage")


class AccountModel(CustomEndpointBaseModel):
    """Model representing an account.

    Attributes:
        customer (_CustomerModel): The customer associated with the account.

    """

    customer: _CustomerModel | None


class AccountResponseModel(StatusModel):
    """Model representing an account response.

    Inherits from StatusModel.

    Attributes:
        payload (Optional[AccountModel]): The account payload.
            Defaults to None.

    """

    payload: AccountModel | None = None
