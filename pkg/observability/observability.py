"""
Observability for Pine Labs MCP Server.

Thin wrapper holding a logger instance.
"""

from __future__ import annotations

import logging


class Observability:
    """Holds observability dependencies (logger)."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("pinelabs-mcp-server")
