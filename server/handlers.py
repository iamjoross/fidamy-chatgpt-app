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
from .schemas import ApplicantCaptureRequest, QuotationRequest
from .services.fidamy_api import (
    FidamyApiAuthError,
    FidamyApiClient,
    FidamyApiParseError,
    FidamyApiResponseError,
    FidamyApiTimeoutError,
)
from .widgets import QuoteWidget, tool_invocation_meta

T = TypeVar("T", bound=BaseModel)


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
            f"{widget.response_text} "
            f"Generated a quotation for {quotation.device_category}."
        ),
        meta=tool_invocation_meta(widget),
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
