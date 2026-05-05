"""Reusable MCP server helpers for Python widget-based apps.

This module encapsulates common MCP server wiring for the OpenAI Apps SDK
Python examples. It provides helper functions to build tool metadata,
resource definitions, transport security settings, and request handlers
that are compatible with the `mcp` package's `FastMCP` helper.
"""

from __future__ import annotations

import os
from typing import Any, Awaitable, Callable

import mcp.types as types
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import AnyUrl, ValidationError

CallToolHandler = Callable[[types.CallToolRequest], Awaitable[types.ServerResult]]

__all__ = [
    "split_env_list",
    "build_transport_security_settings",
    "build_tool",
    "build_resource",
    "build_resource_template",
    "build_validation_error_result",
    "build_call_error_result",
    "build_tool_result",
    "build_unknown_tool_result",
    "make_read_resource_handler",
    "make_call_tool_handler",
    "CallToolHandler",
]


def split_env_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def build_transport_security_settings() -> TransportSecuritySettings:
    """Build TCP transport security settings for an MCP server.

    The Python `mcp` SDK enforces DNS rebinding protection by default. When
    running locally behind tunnels such as ngrok, this helper will set explicit
    allowed hosts and origins from the environment.
    """
    allowed_hosts = split_env_list(os.getenv("MCP_ALLOWED_HOSTS"))
    allowed_origins = split_env_list(os.getenv("MCP_ALLOWED_ORIGINS"))
    if not allowed_hosts and not allowed_origins:
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


def build_tool(
    name: str,
    title: str,
    description: str,
    input_schema: Any,
    *,
    meta: dict[str, Any] | None = None,
    annotations: types.ToolAnnotations | None = None,
) -> types.Tool:
    """Create a reusable MCP tool definition.

    The returned `types.Tool` object is consumed by the `FastMCP` helper
    through `mcp._mcp_server.list_tools()`.
    """
    return types.Tool(
        name=name,
        title=title,
        description=description,
        inputSchema=input_schema,
        _meta=meta,
        annotations=annotations,
    )


def build_resource(
    widget: Any,
    mime_type: str,
    description_fn: Callable[[Any], str],
    meta_fn: Callable[[Any], dict[str, Any]],
) -> types.Resource:
    """Build an MCP resource object for widget markup.

    Resources are returned by `mcp._mcp_server.list_resources()` and provide
    the metadata needed by the Apps SDK to render HTML widgets.
    """
    return types.Resource(
        name=widget.title,
        title=widget.title,
        uri=AnyUrl(widget.template_uri),
        description=description_fn(widget),
        mimeType=mime_type,
        _meta=meta_fn(widget),
    )


def build_resource_template(
    widget: Any,
    mime_type: str,
    description_fn: Callable[[Any], str],
    meta_fn: Callable[[Any], dict[str, Any]],
) -> types.ResourceTemplate:
    """Build an MCP resource template object for a widget.

    Resource templates are returned by `mcp._mcp_server.list_resource_templates()`
    and allow clients to discover widget markup by URI template.
    """
    return types.ResourceTemplate(
        name=widget.title,
        title=widget.title,
        uriTemplate=widget.template_uri,
        description=description_fn(widget),
        mimeType=mime_type,
        _meta=meta_fn(widget),
    )


def build_validation_error_result(exc: ValidationError) -> types.ServerResult:
    """Convert a Pydantic validation error into an MCP server error result.

    This helper is intended for tool request payload validation failures.
    """
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


def build_call_error_result(
    message: str, *, meta: dict[str, Any] | None = None
) -> types.ServerResult:
    """Build a generic MCP call tool error response.

    The returned `types.ServerResult` wraps a `types.CallToolResult` and
    marks it as an error so the client can display the failure to the user.
    """
    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text=message)],
            _meta=meta,
            isError=True,
        )
    )


def build_tool_result(
    widget: Any,
    structured_content: dict[str, Any] | None = None,
    *,
    text: str | None = None,
    meta: dict[str, Any] | None = None,
) -> types.ServerResult:
    """Build a successful MCP tool response with optional structured content.

    This helper is used by tool handlers to return user-facing text and
    any structured payload that the front-end widget or Apps SDK may consume.
    """
    return types.ServerResult(
        types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=text
                    if text is not None
                    else getattr(widget, "response_text", "Tool completed."),
                )
            ],
            structuredContent=structured_content,
            _meta=meta,
        )
    )


def build_unknown_tool_result(tool_name: str) -> types.ServerResult:
    """Return a standardized error result for an unrecognized tool request."""
    return build_call_error_result(f"Unknown tool: {tool_name}")


def make_read_resource_handler(
    widget_lookup: dict[str, Any],
    mime_type: str,
    meta_fn: Callable[[Any], dict[str, Any]],
    *,
    fallback_widget: Any | None = None,
) -> Callable[[types.ReadResourceRequest], Awaitable[types.ServerResult]]:
    """Create a reusable handler for MCP read resource requests.

    The returned handler is compatible with `mcp._mcp_server.request_handlers`
    and resolves a local widget registry into `types.ReadResourceResult`
    contents. A fallback widget can be supplied for generic `ui://widget/...`
    requests that may arrive from the Apps SDK.

    """

    async def _handler(req: types.ReadResourceRequest) -> types.ServerResult:
        widget = widget_lookup.get(str(req.params.uri))
        if widget is None and fallback_widget is not None:
            if str(req.params.uri).startswith("ui://widget/"):
                widget = fallback_widget

        if widget is None:
            return types.ServerResult(
                types.ReadResourceResult(
                    contents=[],
                    _meta={"error": f"Unknown resource: {req.params.uri}"},
                )
            )

        contents: list[types.TextResourceContents | types.BlobResourceContents] = [
            types.TextResourceContents(
                uri=AnyUrl(widget.template_uri),
                mimeType=mime_type,
                text=widget.html,
                _meta=meta_fn(widget),
            )
        ]
        return types.ServerResult(types.ReadResourceResult(contents=contents))

    return _handler


def make_call_tool_handler(
    handlers: dict[str, CallToolHandler],
) -> Callable[[types.CallToolRequest], Awaitable[types.ServerResult]]:
    """Create a reusable dispatch handler for MCP tool invocation requests.

    The returned handler resolves a tool name to a specific async handler
    and returns a standard `types.ServerResult` for the MCP runtime.
    """

    async def _handler(req: types.CallToolRequest) -> types.ServerResult:
        tool_handler = handlers.get(req.params.name)
        if tool_handler is None:
            return build_unknown_tool_result(req.params.name)
        return await tool_handler(req)

    return _handler
