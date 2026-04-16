"""
Pine Labs MCP Server — stdio transport runner.
"""

from __future__ import annotations

from pkg.pinelabs.server import new_pinelabs_mcp_server
from pkg.pinelabs.config import Settings


def run_stdio_server(
    settings: Settings,
    *,
    read_only: bool = False,
    enabled_toolsets: list[str] | None = None,
) -> None:
    """Start the MCP server in stdio transport mode."""
    mcp = new_pinelabs_mcp_server(
        settings,
        read_only=read_only,
        enabled_toolsets=enabled_toolsets,
    )
    mcp.run(transport="stdio")
