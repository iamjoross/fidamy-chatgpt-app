"""Application wiring for the quotation MCP server."""

from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from dotenv import load_dotenv
from pydantic import AnyUrl, ValidationError

try:
    if __package__:
        from .schemas import (
            QUOTATION_TOOL_INPUT_SCHEMA,
            QuotationRequest,
            QuotationResponse,
        )
    else:
        from schemas import (
            QUOTATION_TOOL_INPUT_SCHEMA,
            QuotationRequest,
            QuotationResponse,
        )
except ImportError:
    from schemas import QUOTATION_TOOL_INPUT_SCHEMA, QuotationRequest, QuotationResponse

try:
    from .services.fidamy_api import (
        FidamyApiAuthError,
        FidamyApiClient,
        FidamyApiParseError,
        FidamyApiResponseError,
        FidamyApiTimeoutError,
    )
    from .widgets import (
        MIME_TYPE,
        WIDGETS,
        WIDGETS_BY_ID,
        WIDGETS_BY_URI,
        QuoteWidget,
        resource_description,
        tool_invocation_meta,
        tool_meta,
    )
except ImportError:
    from services.fidamy_api import (
        FidamyApiAuthError,
        FidamyApiClient,
        FidamyApiParseError,
        FidamyApiResponseError,
        FidamyApiTimeoutError,
    )
    from widgets import (
        MIME_TYPE,
        WIDGETS,
        WIDGETS_BY_ID,
        WIDGETS_BY_URI,
        QuoteWidget,
        resource_description,
        tool_invocation_meta,
        tool_meta,
    )


ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")

FIDEMY_BASE_URL = os.getenv("FIDEMY_BASE_URL")
FIDEMY_API_KEY = os.getenv("FIDEMY_API_KEY")
FIDEMY_TIMEOUT_SECONDS = float(os.getenv("FIDEMY_TIMEOUT_SECONDS", "10"))

missing_env = [
    name
    for name, value in (
        ("FIDEMY_BASE_URL", FIDEMY_BASE_URL),
        ("FIDEMY_API_KEY", FIDEMY_API_KEY),
    )
    if not value
]
if missing_env:
    raise RuntimeError(
        "Missing required environment variables: "
        + ", ".join(missing_env)
        + ". Set them before starting the server."
    )

fidamy_client = FidamyApiClient(
    base_url=str(FIDEMY_BASE_URL),
    api_key=str(FIDEMY_API_KEY),
    timeout_seconds=FIDEMY_TIMEOUT_SECONDS,
)


def _split_env_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _transport_security_settings() -> TransportSecuritySettings:
    allowed_hosts = _split_env_list(os.getenv("MCP_ALLOWED_HOSTS"))
    allowed_origins = _split_env_list(os.getenv("MCP_ALLOWED_ORIGINS"))
    if not allowed_hosts and not allowed_origins:
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


mcp = FastMCP(
    name="quote-server",
    stateless_http=True,
    transport_security=_transport_security_settings(),
)


@mcp._mcp_server.list_tools()
async def _list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name=widget.identifier,
            title=widget.title,
            description=widget.title,
            inputSchema=deepcopy(QUOTATION_TOOL_INPUT_SCHEMA),
            _meta=tool_meta(widget),
            annotations=ToolAnnotations(
                destructiveHint=False,
                openWorldHint=False,
                readOnlyHint=True,
            ),
        )
        for widget in WIDGETS
    ]


@mcp._mcp_server.list_resources()
async def _list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            name=widget.title,
            title=widget.title,
            uri=AnyUrl(widget.template_uri),
            description=resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=tool_meta(widget),
        )
        for widget in WIDGETS
    ]


@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> list[types.ResourceTemplate]:
    return [
        types.ResourceTemplate(
            name=widget.title,
            title=widget.title,
            uriTemplate=widget.template_uri,
            description=resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=tool_meta(widget),
        )
        for widget in WIDGETS
    ]


async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    widget = WIDGETS_BY_URI.get(str(req.params.uri))
    if widget is None:
        return types.ServerResult(
            types.ReadResourceResult(
                contents=[],
                _meta={"error": f"Unknown resource: {req.params.uri}"},
            )
        )

    contents = [
        types.TextResourceContents(
            uri=AnyUrl(widget.template_uri),
            mimeType=MIME_TYPE,
            text=widget.html,
            _meta=tool_meta(widget),
        )
    ]

    return types.ServerResult(types.ReadResourceResult(contents=contents))


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    widget = WIDGETS_BY_ID.get(req.params.name)
    if widget is None:
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Unknown tool: {req.params.name}",
                    )
                ],
                isError=True,
            )
        )

    arguments = req.params.arguments or {}
    try:
        payload = QuotationRequest.model_validate(arguments)
    except ValidationError as exc:
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Input validation error: {exc.errors()}",
                    )
                ],
                isError=True,
            )
        )

    try:
        quotation = await fidamy_client.quotation(payload)
    except FidamyApiAuthError as exc:
        return _tool_error_result(widget, f"Authentication error: {exc}")
    except FidamyApiTimeoutError as exc:
        return _tool_error_result(widget, f"Quotation request timed out: {exc}")
    except (FidamyApiParseError, FidamyApiResponseError) as exc:
        return _tool_error_result(widget, f"Unable to fetch quotation: {exc}")
    print(3, quotation)
    return _tool_result(widget, quotation)


def _tool_result(
    widget: QuoteWidget, quotation: QuotationResponse
) -> types.ServerResult:
    return types.ServerResult(
        types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=(
                        f"{widget.response_text} "
                        f"Generated a quotation for {quotation.device_category}."
                    ),
                )
            ],
            structuredContent=quotation.model_dump(by_alias=True, mode="json"),
            _meta=tool_invocation_meta(widget),
        )
    )


def _tool_error_result(widget: QuoteWidget, message: str) -> types.ServerResult:
    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text=message)],
            _meta=tool_invocation_meta(widget),
            isError=True,
        )
    )


mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource


app = mcp.streamable_http_app()

try:
    from starlette.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
except Exception:
    pass
