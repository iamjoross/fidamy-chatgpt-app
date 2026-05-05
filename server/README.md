# ChatGPT App MCP server (Python)

This directory packages the Python MCP server for the `chatgpt-app` demo using the official `mcp` package and `FastMCP` helper. It exposes widget markup as resources and tool definitions for the OpenAI Apps SDK.

The code is split into small modules:

- `app.py` wires `FastMCP`, request handlers, and the Starlette-compatible ASGI app.
- `mcp_helpers.py` contains reusable MCP helper factories for tools, resources, transport security, and handler dispatch.
- `handlers.py` implements tool-specific business logic for the capture and quote flows.
- `widgets.py` defines widget metadata and widget HTML/template URIs.
- `schemas.py` holds the Pydantic input models and JSON schemas used by tool definitions.
- `main.py` is the runnable server entrypoint.

### Services

The `services/` directory contains external API client integrations:

- `fidamy_api.py` provides an async HTTP client (`FidamyApiClient`) for the Fidamy insurance quotation API. It handles:
  - **Quotation requests** (`/quotes/preview`) – fetches pricing options for a device
  - **Intent creation** (`/intents`) – initiates a purchase journey after plan selection
  - Request/response normalization using Pydantic models from `schemas.py`
  - Error handling with specific exception types (`FidamyApiError`, `FidamyApiTimeoutError`, etc.)

## Prerequisites

- Python 3.10+
- A virtual environment (recommended)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **Heads up:** There is a similarly named package named `modelcontextprotocol`
> on PyPI that is unrelated to the official MCP SDK. The requirements file
> installs the official `mcp` distribution with its FastAPI extra so that the
> `mcp.server.fastmcp` module is available. If you previously installed the
> other project, run `pip uninstall modelcontextprotocol` before reinstalling
> the requirements.

## Important

The Python MCP SDK enforces DNS rebinding protection. When tunneling (for example via ngrok), allow your tunnel host before starting any Python server:

```bash
export MCP_ALLOWED_HOSTS="<custom_endpoint>.ngrok-free.app"
export MCP_ALLOWED_ORIGINS="https://<custom_endpoint>.ngrok-free.app"
```

## Run the server

```bash
./server/.venv/bin/python server/main.py
```

Or use Uvicorn directly for live reload:

```bash
./server/.venv/bin/uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

This boots the ASGI app on `http://127.0.0.1:8000`.

## MCP endpoints

- `GET /mcp` exposes the SSE stream.
- `POST /mcp/messages?sessionId=...` accepts follow-up messages for an active session.

## Notes

- The server registers tools and resources via `FastMCP`.
- `mcp_helpers.py` centralizes tool/resource construction and request dispatch.
- `handlers.py` returns structured tool results and handles error cases consistently.

## Next steps

Use this server as a starting point when wiring in real data, authentication, or localization support. The structure demonstrates how to:

1. Register reusable UI resources that load static HTML bundles.
2. Associate tools with widgets and tool invocation metadata.
3. Return structured JSON along with user-facing confirmation text.
