"""Input and response models for the quotation tool."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

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

# Backwards-compatible alias while the rest of the server is migrated.
QuotationInput = QuotationRequest
