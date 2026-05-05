"""Input and response models for the quotation tool."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DEVICE_CATEGORIES = (
    "Smartphone",
    "Laptop",
    "Smartwatch",
    "Wearable",
    "Camera",
)

DeviceCategory = Literal[
    "Smartphone",
    "Laptop",
    "Smartwatch",
    "Wearable",
    "Camera",
]


class QuotationRequest(BaseModel):
    """Validated input for quotation requests."""

    device_category: DeviceCategory = Field(
        ...,
        alias="deviceCategory",
        description=(
            "Choose the exact supported device category inferred from the user's "
            "device: Smartphone, Laptop, Smartwatch, Wearable, or Camera."
        ),
    )
    device_market_value: float = Field(
        ...,
        alias="deviceMarketValue",
        description="The current market value of the device.",
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class QuotationResponse(BaseModel):
    """Normalized quotation data returned to widgets."""

    device_category: str = Field(..., alias="deviceCategory")
    device_market_value: float = Field(..., alias="deviceMarketValue")
    quotation: dict[str, Any] = Field(
        default_factory=dict,
        description="Normalized quotation payload from Fidamy.",
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class ApplicantCaptureRequest(BaseModel):
    """Validated input for captured applicant details."""

    first_name: str = Field(
        ...,
        alias="firstName",
        description="Applicant first name.",
    )
    last_name: str = Field(
        ...,
        alias="lastName",
        description="Applicant last name.",
    )
    email: str = Field(
        ...,
        alias="email",
        description="Applicant email address.",
    )
    phone_number: str = Field(
        ...,
        alias="phoneNumber",
        description="Applicant phone number including country code (for example +31612345678).",
    )
    phone_country_code: str = Field(
        ...,
        alias="phoneCountryCode",
        description="Phone country code extracted from phoneNumber (for example +31).",
    )
    phone_no: str = Field(
        ...,
        alias="phoneNo",
        description="Local phone number without country code (for example 612345678).",
    )
    date_of_birth: str = Field(
        ...,
        alias="dateOfBirth",
        description="Applicant date of birth in dd-mm-yyyy format.",
        pattern=r"^\d{2}-\d{2}-\d{4}$",
    )
    street: str = Field(
        ...,
        alias="street",
        description="Street name of residence address.",
    )
    house_number: str = Field(
        ...,
        alias="houseNumber",
        description="House number of residence address.",
    )
    zip_code: str = Field(
        ...,
        alias="zipCode",
        description="ZIP/postal code of residence address.",
    )
    city: str = Field(
        ...,
        alias="city",
        description="City of residence address.",
    )
    country_of_residence: str = Field(
        ...,
        alias="countryOfResidence",
        description="Country of residence.",
    )
    device_brand: str = Field(
        ...,
        alias="deviceBrand",
        description="Brand of the insured device.",
    )
    device_model: str = Field(
        ...,
        alias="deviceModel",
        description="Model of the insured device (for example iPhone 17).",
    )
    device_category: DeviceCategory = Field(
        ...,
        alias="deviceCategory",
        description="Category of the insured device.",
    )
    device_market_value: str = Field(
        ...,
        alias="deviceMarketValue",
        description="Current market value of the device as text.",
    )
    serial_number: str | None = Field(
        default=None,
        alias="serialNumber",
        description="Device serial number.",
    )
    imei: str | None = Field(
        default=None,
        alias="imei",
        description="Device IMEI number.",
    )
    selected_plan_label: str = Field(
        ...,
        alias="selectedPlanLabel",
        description="Selected insurance plan label.",
    )
    selected_billing_period: Literal["monthly", "yearly"] = Field(
        ...,
        alias="selectedBillingPeriod",
        description="Selected insurance billing period.",
    )
    selected_premium: str = Field(
        ...,
        alias="selectedPremium",
        description="Selected premium amount, formatted as text.",
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator(
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "date_of_birth",
        "street",
        "house_number",
        "zip_code",
        "city",
        "country_of_residence",
        "device_brand",
        "device_model",
        "phone_country_code",
        "phone_no",
        "selected_plan_label",
        "selected_premium",
        mode="before",
    )
    @classmethod
    def normalize_required_strings(cls, value: object) -> str:
        text = str(value).strip() if value is not None else ""
        if not text:
            raise ValueError("This field is required and cannot be empty.")
        return text

    @field_validator("serial_number", "imei", mode="before")
    @classmethod
    def normalize_optional_identifiers(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Email must be a valid email address.")
        return value

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        if not value.startswith("+") or not value[1:].isdigit():
            raise ValueError(
                "Phone number must include country code in E.164 format (example: +31612345678)."
            )
        if len(value) < 8 or len(value) > 16:
            raise ValueError("Phone number must be between 8 and 16 characters.")
        return value

    @field_validator("phone_country_code")
    @classmethod
    def validate_phone_country_code(cls, value: str) -> str:
        if not value.startswith("+") or not value[1:].isdigit():
            raise ValueError("phoneCountryCode must start with + and contain digits.")
        if len(value) < 2 or len(value) > 5:
            raise ValueError("phoneCountryCode must be between 2 and 5 characters.")
        return value

    @field_validator("phone_no")
    @classmethod
    def validate_phone_no(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("phoneNo must contain digits only.")
        if len(value) < 4:
            raise ValueError("phoneNo must contain at least 4 digits.")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: str) -> str:
        try:
            parsed = datetime.strptime(value, "%d-%m-%Y").date()
        except ValueError as exc:
            raise ValueError(
                "dateOfBirth must be a valid date in dd-mm-yyyy format."
            ) from exc
        if parsed >= date.today():
            raise ValueError("dateOfBirth must be in the past.")
        return value

    @field_validator("imei")
    @classmethod
    def validate_imei(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.isdigit() or len(value) != 15:
            raise ValueError("IMEI must be a 15-digit numeric string.")
        return value

    @field_validator("serial_number")
    @classmethod
    def validate_serial_number(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) < 5:
            raise ValueError("serialNumber must be at least 5 characters.")
        return value

    @field_validator("device_market_value")
    @classmethod
    def validate_device_market_value(cls, value: str) -> str:
        try:
            numeric = float(value)
        except ValueError as exc:
            raise ValueError("deviceMarketValue must be numeric text.") from exc
        if numeric <= 0:
            raise ValueError("deviceMarketValue must be greater than zero.")
        return value

    @model_validator(mode="after")
    def ensure_device_identifier(self) -> "ApplicantCaptureRequest":
        if not (self.serial_number or self.imei):
            raise ValueError("Either serialNumber or imei must be provided.")
        return self


QUOTATION_TOOL_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "deviceCategory": {
            "type": "string",
            "enum": list(DEVICE_CATEGORIES),
            "description": (
                "Choose the exact supported device category inferred from the user's "
                "device: Smartphone, Laptop, Smartwatch, Wearable, or Camera."
            ),
        },
        "deviceMarketValue": {
            "type": "number",
            "description": "The current market value of the device.",
        },
    },
    "required": ["deviceCategory", "deviceMarketValue"],
    "additionalProperties": False,
}

APPLICANT_CAPTURE_TOOL_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "firstName": {
            "type": "string",
            "description": "Applicant first name.",
        },
        "lastName": {
            "type": "string",
            "description": "Applicant last name.",
        },
        "email": {
            "type": "string",
            "format": "email",
            "description": "Applicant email address.",
        },
        "phoneNumber": {
            "type": "string",
            "pattern": "^\\+[1-9]\\d{6,14}$",
            "description": "Applicant phone number including country code (for example +31612345678).",
        },
        "phoneCountryCode": {
            "type": "string",
            "pattern": "^\\+[1-9]\\d{0,3}$",
            "description": "Phone country code (for example +31).",
        },
        "phoneNo": {
            "type": "string",
            "pattern": "^\\d{4,14}$",
            "description": "Local phone number without country code.",
        },
        "dateOfBirth": {
            "type": "string",
            "pattern": "^\\d{2}-\\d{2}-\\d{4}$",
            "description": "Applicant date of birth in dd-mm-yyyy format.",
        },
        "street": {
            "type": "string",
            "description": "Street name of residence address.",
        },
        "houseNumber": {
            "type": "string",
            "description": "House number of residence address.",
        },
        "zipCode": {
            "type": "string",
            "description": "ZIP/postal code of residence address.",
        },
        "city": {
            "type": "string",
            "description": "City of residence address.",
        },
        "countryOfResidence": {
            "type": "string",
            "description": "Country of residence.",
        },
        "deviceBrand": {
            "type": "string",
            "description": "Brand of the insured device.",
        },
        "deviceModel": {
            "type": "string",
            "description": "Model of the insured device (for example iPhone 17).",
        },
        "deviceCategory": {
            "type": "string",
            "enum": list(DEVICE_CATEGORIES),
            "description": "Category of the insured device.",
        },
        "deviceMarketValue": {
            "type": "string",
            "description": "Current market value of the device as text.",
        },
        "serialNumber": {
            "type": "string",
            "minLength": 5,
            "description": "Device serial number. Provide either serialNumber or imei.",
        },
        "imei": {
            "type": "string",
            "pattern": "^\\d{15}$",
            "description": "Device IMEI number. Provide either imei or serialNumber.",
        },
        "selectedPlanLabel": {
            "type": "string",
            "description": "Selected insurance plan label.",
        },
        "selectedBillingPeriod": {
            "type": "string",
            "enum": ["monthly", "yearly"],
            "description": "Selected insurance billing period.",
        },
        "selectedPremium": {
            "type": "string",
            "description": "Selected premium amount, formatted as text.",
        },
    },
    "required": [
        "firstName",
        "lastName",
        "email",
        "phoneNumber",
        "phoneCountryCode",
        "phoneNo",
        "dateOfBirth",
        "street",
        "houseNumber",
        "zipCode",
        "city",
        "countryOfResidence",
        "deviceBrand",
        "deviceModel",
        "deviceCategory",
        "deviceMarketValue",
        "selectedPlanLabel",
        "selectedBillingPeriod",
        "selectedPremium",
    ],
    "additionalProperties": False,
}

# Backwards-compatible alias while the rest of the server is migrated.
QuotationInput = QuotationRequest
