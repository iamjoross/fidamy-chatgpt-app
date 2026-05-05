"""Async client for Fidamy quotation requests."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import ValidationError

from ..schemas import (
    ApplicantCaptureRequest,
    QuotationRequest,
    QuotationResponse,
)


class FidamyApiError(Exception):
    """Base class for Fidamy client errors."""


class FidamyApiTimeoutError(FidamyApiError):
    """Raised when the Fidamy API times out."""


class FidamyApiAuthError(FidamyApiError):
    """Raised when the Fidamy API rejects authentication."""


class FidamyApiResponseError(FidamyApiError):
    """Raised when the Fidamy API returns a non-success response."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class FidamyApiParseError(FidamyApiError):
    """Raised when the Fidamy API response cannot be normalized."""


class FidamyApiClient:
    """Single-purpose client for Fidamy quotation requests."""

    _quotation_path = "/quotes/preview"
    _intent_path = "/intents"
    _attribution_code = "fidamyagentic_d2c"
    _campaign_code = "springsale2026"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds

    async def quotation(self, payload: QuotationRequest) -> QuotationResponse:
        """Request a price quotation from the Fidamy API.

        The payload is validated by the caller as a `QuotationRequest` model.
        This method posts the normalized quotation payload and returns a
        `QuotationResponse` model representing the normalized response.
        """
        response_payload = await self._request(
            "POST",
            self._quotation_path,
            json=self._quotation_payload(payload),
        )
        return self._parse_quotation_response(payload, response_payload)

    async def create_intent(self, payload: ApplicantCaptureRequest) -> dict[str, Any]:
        """Create a purchase intent in the Fidamy system.

        The returned dictionary contains the raw API response payload. This is
        used by the server to build a capture result containing the intent URL.
        """
        response_payload = await self._request(
            "POST",
            self._intent_path,
            json=self._intent_payload(payload),
        )
        return response_payload

    def _headers(self) -> dict[str, str]:
        """Build the standard Fidamy API request headers."""
        return {
            "Accept": "application/json",
            "Authorization": f"ApiKey {self._api_key}",
            "Content-Type": "application/json",
        }

    def _quotation_payload(self, payload: QuotationRequest) -> dict[str, Any]:
        """Build the payload for a quotation request.

        Converts the normalized Pydantic model into the JSON shape expected by
        the Fidamy endpoint, including attribution and campaign metadata.
        """
        request_payload = payload.model_dump(by_alias=True, mode="json")
        request_payload["deviceMarketValue"] = str(request_payload["deviceMarketValue"])
        request_payload["attributionCode"] = self._attribution_code
        request_payload["campaignCode"] = self._campaign_code
        return request_payload

    def _intent_payload(self, payload: ApplicantCaptureRequest) -> dict[str, Any]:
        """Build the payload for an intent creation request.

        This payload formats the applicant data and selected plan data into the
        Fidamy journey format expected by the `/intents` endpoint.
        """
        coverage = "extended"
        if payload.selected_plan_label.strip().lower().startswith("basic"):
            coverage = "basic"
        elif payload.selected_plan_label.strip().lower().startswith("extended"):
            coverage = "extended"

        return {
            "attributionCode": self._attribution_code,
            "campaignCode": self._campaign_code,
            "journeyType": "express",
            "handoffChannel": "url",
            "product": {
                "coverage": coverage,
                "billingCycle": payload.selected_billing_period,
            },
            "insuredObject": {
                "serialNo": payload.serial_number,
                "imei": payload.imei,
                "deviceBrand": payload.device_brand,
                "deviceModel": payload.device_model,
                "deviceCategory": payload.device_category,
                "deviceMarketValue": payload.device_market_value,
            },
            "policyholder": {
                "firstName": payload.first_name,
                "lastName": payload.last_name,
                "birthday": self._format_birthday(payload.date_of_birth),
                "email": payload.email,
                "phoneNo": payload.phone_no,
                "phoneCountryCode": payload.phone_country_code,
                "address": {
                    "zipCode": payload.zip_code,
                    "street": payload.street,
                    "houseNo": payload.house_number,
                    "city": payload.city,
                    "residenceCountry": payload.country_of_residence,
                },
            },
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send an HTTP request to the Fidamy API and normalize failures."""
        url = f"{self._base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=json,
                )
        except httpx.TimeoutException as exc:
            raise FidamyApiTimeoutError("Fidamy quotation request timed out.") from exc
        except httpx.HTTPError as exc:
            raise FidamyApiResponseError(
                "Fidamy quotation request failed before a response was received."
            ) from exc

        if response.status_code in (401, 403):
            raise FidamyApiAuthError("Fidamy API rejected the provided API key.")

        if response.status_code >= 400:
            detail = self._response_text(response)
            raise FidamyApiResponseError(
                f"Fidamy API returned HTTP {response.status_code}: {detail}",
                status_code=response.status_code,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise FidamyApiParseError(
                "Fidamy API returned a non-JSON quotation response."
            ) from exc

        if not isinstance(payload, dict):
            raise FidamyApiParseError(
                "Fidamy API returned an unexpected quotation payload shape."
            )

        return payload

    def _parse_quotation_response(
        self,
        request_payload: QuotationRequest,
        response_payload: dict[str, Any],
    ) -> QuotationResponse:
        """Normalize the Fidamy response into a `QuotationResponse` model."""
        try:
            return QuotationResponse.model_validate(
                {
                    "deviceCategory": request_payload.device_category,
                    "deviceMarketValue": request_payload.device_market_value,
                    "quotation": response_payload,
                }
            )
        except ValidationError as exc:
            raise FidamyApiParseError(
                "Fidamy API returned quotation data that could not be normalized."
            ) from exc

    @staticmethod
    def _response_text(response: httpx.Response) -> str:
        """Extract and normalize response body text for error reporting."""
        text = response.text.strip()
        return text or "No response body provided."

    @staticmethod
    def _format_birthday(date_of_birth: str) -> str:
        """Convert dd-mm-yyyy birthdate strings into yyyy-mm-dd."""
        day, month, year = date_of_birth.split("-")
        return f"{year}-{month}-{day}"
