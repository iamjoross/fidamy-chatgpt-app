"""Application wiring for the quotation MCP server."""

from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from dotenv import load_dotenv

from .handlers import capture_tool_handler, quote_tool_handler
from .mcp_helpers import (
    build_resource,
    build_resource_template,
    build_tool,
    build_transport_security_settings,
    make_call_tool_handler,
    make_read_resource_handler,
)
from .schemas import (
    APPLICANT_CAPTURE_TOOL_INPUT_SCHEMA,
    QUOTATION_TOOL_INPUT_SCHEMA,
)
from .services.fidamy_api import FidamyApiClient
from .widgets import (
    MIME_TYPE,
    WIDGETS,
    WIDGETS_BY_ID,
    WIDGETS_BY_URI,
    resource_description,
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


mcp = FastMCP(
    name="quote-server",
    stateless_http=True,
    transport_security=build_transport_security_settings(),
)

CAPTURE_TOOL_NAME = "capture-applicant-values"
CAPTURE_TOOL_TITLE = "Capture applicant values"


@mcp._mcp_server.list_tools()
async def _list_tools() -> list[types.Tool]:
    return [
        build_tool(
            name="quote",
            title=WIDGETS_BY_ID["quote"].title,
            description=WIDGETS_BY_ID["quote"].title,
            input_schema=deepcopy(QUOTATION_TOOL_INPUT_SCHEMA),
            meta=tool_meta(WIDGETS_BY_ID["quote"]),
            annotations=ToolAnnotations(
                destructiveHint=False,
                openWorldHint=False,
                readOnlyHint=True,
            ),
        ),
        build_tool(
            name=CAPTURE_TOOL_NAME,
            title=CAPTURE_TOOL_TITLE,
            description=(
                "Capture applicant personal details, address, device identifiers, "
                "and selected plan details for the next application step."
            ),
            input_schema=deepcopy(APPLICANT_CAPTURE_TOOL_INPUT_SCHEMA),
            annotations=ToolAnnotations(
                destructiveHint=False,
                openWorldHint=False,
                readOnlyHint=False,
            ),
        ),
    ]


@mcp._mcp_server.list_resources()
async def _list_resources() -> list[types.Resource]:
    return [
        build_resource(widget, MIME_TYPE, resource_description, tool_meta)
        for widget in WIDGETS
    ]


@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> list[types.ResourceTemplate]:
    return [
        build_resource_template(widget, MIME_TYPE, resource_description, tool_meta)
        for widget in WIDGETS
    ]


_read_resource_handler = make_read_resource_handler(
    WIDGETS_BY_URI,
    MIME_TYPE,
    tool_meta,
    fallback_widget=WIDGETS_BY_ID.get("quote"),
)


async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    return await _read_resource_handler(req)


async def _handle_capture_tool(req: types.CallToolRequest) -> types.ServerResult:
    return await capture_tool_handler(req, fidamy_client)


async def _handle_quote_tool(req: types.CallToolRequest) -> types.ServerResult:
    return await quote_tool_handler(req, WIDGETS_BY_ID["quote"], fidamy_client)


_call_tool_handler = make_call_tool_handler(
    {
        CAPTURE_TOOL_NAME: _handle_capture_tool,
        WIDGETS_BY_ID["quote"].identifier: _handle_quote_tool,
    }
)


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    return await _call_tool_handler(req)


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
