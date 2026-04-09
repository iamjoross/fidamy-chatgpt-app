"""Async client for Fidamy quotation requests."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import ValidationError

try:
    if __package__ and "." in __package__:
        from ..schemas import QuotationRequest, QuotationResponse
    else:
        from schemas import QuotationRequest, QuotationResponse
except ImportError:
    from schemas import QuotationRequest, QuotationResponse


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
        response_payload = await self._request(
            "POST",
            self._quotation_path,
            json=self._quotation_payload(payload),
        )
        return self._parse_quotation_response(payload, response_payload)

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"ApiKey {self._api_key}",
            "Content-Type": "application/json",
        }

    def _quotation_payload(self, payload: QuotationRequest) -> dict[str, Any]:
        request_payload = payload.model_dump(by_alias=True, mode="json")
        request_payload["deviceMarketValue"] = str(request_payload["deviceMarketValue"])
        request_payload["attributionCode"] = self._attribution_code
        request_payload["campaignCode"] = self._campaign_code
        return request_payload

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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
        text = response.text.strip()
        return text or "No response body provided."
