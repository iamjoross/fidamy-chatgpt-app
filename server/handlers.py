"""Application-specific tool handlers for the quotation MCP server.

This module validates incoming tool request payloads, routes requests to the
Fidamy API client, and converts backend results into MCP-compatible tool
responses. It keeps domain-specific logic separate from the MCP wiring in
`app.py` and reusable helpers in `mcp_helpers.py`.
"""

from __future__ import annotations

from typing import Any, TypeVar

import mcp.types as types
from pydantic import BaseModel, ValidationError

from .mcp_helpers import (
    build_call_error_result,
    build_tool_result,
    build_validation_error_result,
)
from .schemas import ApplicantCaptureRequest, CaptureFlowPromptRequest, QuotationRequest
from .services.fidamy_api import (
    FidamyApiAuthError,
    FidamyApiClient,
    FidamyApiParseError,
    FidamyApiResponseError,
    FidamyApiTimeoutError,
)
from .widgets import QuoteWidget, tool_invocation_meta

T = TypeVar("T", bound=BaseModel)


def _format_amount(amount: float) -> str:
    """Format a device value for user-facing quotation text."""
    return f"€{amount:,.2f}"


def _format_prompt_amount(amount: str | float) -> str:
    """Format prompt amounts while preserving non-numeric text."""
    try:
        return _format_amount(float(amount))
    except (TypeError, ValueError):
        return str(amount)


def _validate_payload(
    model: type[T], arguments: dict[str, Any] | None
) -> tuple[T | None, types.ServerResult | None]:
    """Validate request arguments against the given Pydantic model.

    Returns a tuple where the first element is the validated model instance or
    None on failure, and the second element is an MCP error response when
    validation fails.
    """
    try:
        return model.model_validate(arguments or {}), None
    except ValidationError as exc:
        return None, build_validation_error_result(exc)


async def capture_tool_handler(
    req: types.CallToolRequest,
    fidamy_client: FidamyApiClient,
) -> types.ServerResult:
    """Handle the applicant capture tool request.

    Validates the incoming arguments, submits the intent request to the
    Fidamy API, and returns either a successful tool result or a formatted
    MCP error response.
    """
    payload, error = _validate_payload(ApplicantCaptureRequest, req.params.arguments)
    if error:
        return error
    assert payload is not None

    try:
        intent_response = await fidamy_client.create_intent(payload)
    except FidamyApiAuthError as exc:
        return build_call_error_result(
            f"Authentication error while creating intent: {exc}"
        )
    except FidamyApiTimeoutError as exc:
        return build_call_error_result(f"Intent request timed out: {exc}")
    except (FidamyApiParseError, FidamyApiResponseError) as exc:
        return build_call_error_result(f"Unable to create intent: {exc}")

    return _capture_values_result(payload, intent_response)


async def prepare_capture_flow_handler(req: types.CallToolRequest) -> types.ServerResult:
    """Prepare the post-selection chat prompt for receipt-assisted capture."""
    payload, error = _validate_payload(
        CaptureFlowPromptRequest, req.params.arguments
    )
    if error:
        return error
    assert payload is not None

    prompt = _build_capture_flow_prompt(payload)
    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text=prompt)],
            structuredContent={"prompt": prompt},
        )
    )


async def quote_tool_handler(
    req: types.CallToolRequest,
    widget: QuoteWidget,
    fidamy_client: FidamyApiClient,
) -> types.ServerResult:
    """Handle the quotation tool request.

    Validates the incoming arguments, sends the quotation request to the
    Fidamy API, and returns a structured MCP tool result.
    """
    payload, error = _validate_payload(QuotationRequest, req.params.arguments)
    if error:
        return error
    assert payload is not None

    try:
        quotation = await fidamy_client.quotation(payload)
    except FidamyApiAuthError as exc:
        return build_call_error_result(
            f"Authentication error: {exc}",
            meta=tool_invocation_meta(widget),
        )
    except FidamyApiTimeoutError as exc:
        return build_call_error_result(
            f"Quotation request timed out: {exc}",
            meta=tool_invocation_meta(widget),
        )
    except (FidamyApiParseError, FidamyApiResponseError) as exc:
        return build_call_error_result(
            f"Unable to fetch quotation: {exc}",
            meta=tool_invocation_meta(widget),
        )

    return build_tool_result(
        widget,
        quotation.model_dump(by_alias=True, mode="json"),
        text=(
            "Here are the insurance options for your "
            f"{quotation.device_category.lower()} "
            f"({_format_amount(quotation.device_market_value)})."
        ),
        meta=tool_invocation_meta(widget),
    )


def _build_capture_flow_prompt(payload: CaptureFlowPromptRequest) -> str:
    """Build the receipt OCR follow-up instructions used by the widget."""
    selected_premium = _format_prompt_amount(payload.selected_premium)
    quoted_device_value = _format_prompt_amount(payload.device_market_value)

    return (
        "The user selected the "
        f"{payload.selected_plan_label} {payload.selected_billing_period} "
        f"plan at {selected_premium}. "
        f"The quoted device market value is {quoted_device_value}. "
        "If receipt OCR data was already extracted and verified earlier in the conversation, do not ask the user for a receipt again and do not restart the data intake flow. "
        "Use the verified OCR fields as already collected values. "
        "If all required applicant, address, and device identifier values are already verified, call `capture-applicant-values` immediately with the selected plan details instead of asking more intake questions. "
        "If only some verified OCR values are missing, ask only for those missing or invalid fields. "
        "If no receipt OCR data has been verified yet, first ask the user whether they have a receipt for the purchased item. "
        "If they have a receipt, ask them to upload the receipt image or document in chat before collecting details. "
        "Use ChatGPT vision/OCR on the uploaded receipt to extract any visible applicant name, email, phone, address, device brand, device model, serial number, IMEI, purchase price/current value, and purchase evidence. "
        "Normalize zipCode by removing all spaces, and normalize countryOfResidence to a two-letter ISO 3166-1 alpha-2 code, for example Netherlands, Nederland, or The Netherlands -> NL. "
        "When extracting device brand and model from a receipt product line, separate model information from storage, color, finish, and material descriptors. "
        "For example, parse 'Apple iPhone 15 Pro Max, 256GB Natural Titanium' as deviceBrand 'Apple' and deviceModel 'iPhone 15 Pro Max'; do not use 'Natural Titanium' as the model. "
        "After OCR, stop immediately: show all extracted fields you intend to use back to the user in a concise labeled list and ask them to verify that everything is correct or provide corrections. "
        "Do not ask any additional intake question, call any tool, generate a quote, or treat any OCR value as collected until the user explicitly verifies or corrects the OCR data. "
        "Do not expose unnecessary raw OCR text. "
        "If a field is unclear or sensitive and not confidently readable, do not guess; ask the user for that field directly. "
        "If the receipt purchase price or value differs from the quoted device market value, ask the user to confirm the correct current market value before submitting; do not silently change the selected plan or selected premium. "
        "If the user does not have a receipt, or if no receipt OCR capture was done at the beginning of the conversation, continue with the original manual data intake flow exactly: collect the required applicant and device details one by one in the order below. "
        "In all cases, collect only missing or invalid required details one by one, asking only one question per assistant message and waiting for the user's answer before asking the next field. "
        "If the user seems unsure about buying, do not collect details and offer to help them compare the available packages. "
        "Use soft-rotation phrasing for questions: rotate among a small set of polite openings and avoid repeating the exact same opening pattern in consecutive turns. "
        "Examples of acceptable openings to rotate: 'Could you share ...', 'May I have ...', 'Please provide ...', 'What is ...'. "
        "Validate each value immediately after the user provides it. "
        "If a value is invalid, explain briefly what is wrong and ask for the same field again; do not continue to the next field until valid. "
        "Infer deviceBrand from the conversation whenever it is obvious (for example: iPhone -> Apple, Galaxy -> Samsung, Pixel -> Google) and inject that inferred value directly in the final tool arguments. "
        "Only ask the user for device brand if it cannot be inferred confidently. "
        "For deviceModel, use the product family and model generation/name only; omit color or finish terms such as Natural Titanium, Black Titanium, Blue, Silver, Graphite, or Gold. "
        "Validation rules: email must be valid; phone number must be E.164 with country code (example +31612345678); extract phoneCountryCode and phoneNo from the validated phone number; date of birth must be dd-mm-yyyy and in the past; zipCode must contain no spaces; countryOfResidence must be a two-letter ISO 3166-1 alpha-2 code such as NL; IMEI must be 15 digits; serial number must be at least 5 characters; at least one of serialNumber or imei is required. "
        "Guardrails: do not ask multiple fields in one message, do not skip fields, and do not change any required formats. "
        "Use this exact order: first name, last name, email, phone number including country code, date of birth (dd-mm-yyyy), street, house number, zip code, city, country of residence, device brand (if not inferable), device model, then either serial number or IMEI. "
        "When verified OCR or earlier conversation already supplied a confirmed value for a field in that order, skip asking for that field; never re-collect confirmed OCR values after package selection. "
        "After collecting all values, call the MCP tool "
        "`capture-applicant-values` with arguments: "
        "{ firstName, lastName, email, phoneNumber, phoneCountryCode, phoneNo, dateOfBirth, street, houseNumber, "
        "zipCode, city, countryOfResidence, deviceBrand, deviceModel, serialNumber?, imei?, "
        f'deviceCategory: "{payload.device_category}", '
        f'deviceMarketValue: "{payload.device_market_value}", '
        f'selectedPlanLabel: "{payload.selected_plan_label}", '
        f'selectedBillingPeriod: "{payload.selected_billing_period}", '
        f'selectedPremium: "{selected_premium}" }}. '
        "After the tool returns, respond to the user with the exact checkout URL from the tool response (`url` or `intentUrl`) and do not omit it."
    )


def _capture_values_result(
    payload: ApplicantCaptureRequest,
    intent_response: dict[str, Any],
) -> types.ServerResult:
    """Build the MCP tool result for a successful applicant capture.

    Returns a text response and structured result data that contains the intent
    URL and raw intent payload from the Fidamy API.
    """
    intent_url = str(intent_response.get("url", "")).strip()
    device_id = payload.serial_number or payload.imei or "-"
    device_id_type = "serialNumber" if payload.serial_number else "imei"

    if intent_url:
        user_text = (
            "Your insurance is waiting for you. Please complete your purchase here:\n\n"
            f"[Get your insurance]({intent_url})\n"
            f"{intent_url}\n\n"
            "On the distribution flow you will confirm a few details and provide your payment information. "
            "The link is valid for 24 hours."
        )
    else:
        user_text = (
            "Captured applicant profile for "
            f"{payload.first_name} {payload.last_name}. "
            f"Contact: {payload.email}, {payload.phone_number}. "
            f"DOB: {payload.date_of_birth}. "
            f"Address: {payload.street} {payload.house_number}, "
            f"{payload.zip_code} {payload.city}, {payload.country_of_residence}. "
            f"Device: {payload.device_brand} ({device_id_type}: {device_id}). "
            f"Plan: {payload.selected_plan_label} {payload.selected_billing_period} "
            f"at {payload.selected_premium}. "
            "Intent request sent to Fidamy."
        )

    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text=user_text)],
            structuredContent={
                "url": intent_url,
                "intent": intent_response,
                "intentUrl": intent_url,
            },
        )
    )
