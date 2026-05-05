"""Compatibility entrypoint for the MCP server."""

from __future__ import annotations

from .app import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
