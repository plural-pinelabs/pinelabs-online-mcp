"""
MCP server factory.

Creates a FastMCP server, registers all tools, returns it.
"""

from __future__ import annotations

from fastmcp import FastMCP

from pkg.pinelabs.client import PineLabsClient
from pkg.pinelabs.config import Settings
from pkg.pinelabs.tools import register_all_tools


def new_pinelabs_mcp_server(
    settings: Settings,
    *,
    read_only: bool = False,
    enabled_toolsets: list[str] | None = None,
) -> FastMCP:
    """Create and configure the Pine Labs MCP server.

    Args:
        settings: Application settings.
        read_only: If True, only register read tools.
        enabled_toolsets: If set, only register these toolsets.

    Returns:
        Configured FastMCP server ready to run.
    """
    mcp = FastMCP("pinelabs-mcp-server")

    client = PineLabsClient(
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        base_url=settings.base_url,
        token_url=settings.token_url,
        timeout=settings.http_timeout,
    )

    register_all_tools(
        mcp,
        client,
        read_only=read_only,
        enabled_toolsets=enabled_toolsets,
    )

    return mcp
