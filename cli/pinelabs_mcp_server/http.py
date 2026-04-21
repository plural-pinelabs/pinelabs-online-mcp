"""
Pine Labs MCP Server — HTTP transport runner.
"""

from __future__ import annotations

from pkg.pinelabs.server import new_pinelabs_mcp_server
from pkg.pinelabs.config import Settings


def run_http_server(
    settings: Settings,
    *,
    host: str = "0.0.0.0",  # noqa: S104 - server is intended to listen on all interfaces; override via --host
    port: int = 8000,
    read_only: bool = False,
    enabled_toolsets: list[str] | None = None,
) -> None:
    """Start the MCP server in HTTP transport mode."""
    mcp = new_pinelabs_mcp_server(
        settings,
        read_only=read_only,
        enabled_toolsets=enabled_toolsets,
    )
    mcp.run(transport="http", host=host, port=port)
