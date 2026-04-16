"""
Toolset management for Pine Labs MCP Server.

Groups tools by resource type with read-only mode and selective
enablement support.
"""

from __future__ import annotations

from typing import Callable

from fastmcp import FastMCP


# A tool registrar is a function that registers tools on a FastMCP instance.
# Signature: (mcp, client) -> None  (or (mcp,) -> None for doc tools)
ToolRegistrar = Callable[..., None]


class Toolset:
    """A group of related tools (e.g. 'payment_links', 'orders')."""

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description
        self.enabled = False
        self.read_only = False
        self._read_registrars: list[ToolRegistrar] = []
        self._write_registrars: list[ToolRegistrar] = []

    def add_read_tools(self, *registrars: ToolRegistrar) -> "Toolset":
        self._read_registrars.extend(registrars)
        return self

    def add_write_tools(self, *registrars: ToolRegistrar) -> "Toolset":
        self._write_registrars.extend(registrars)
        return self

    def register_tools(self, mcp: FastMCP, *args) -> None:
        """Register all enabled tools on the FastMCP server."""
        if not self.enabled:
            return
        for reg in self._read_registrars:
            reg(mcp, *args)
        if not self.read_only:
            for reg in self._write_registrars:
                reg(mcp, *args)


class ToolsetGroup:
    """Manages multiple toolsets with enable/disable and read-only support."""

    def __init__(self, read_only: bool = False) -> None:
        self.toolsets: dict[str, Toolset] = {}
        self.read_only = read_only

    def add_toolset(self, ts: Toolset) -> None:
        if self.read_only:
            ts.read_only = True
        self.toolsets[ts.name] = ts

    def enable_toolset(self, name: str) -> None:
        if name not in self.toolsets:
            raise ValueError(f"toolset '{name}' does not exist")
        self.toolsets[name].enabled = True

    def enable_toolsets(self, names: list[str]) -> None:
        """Enable the given toolsets, or all if the list is empty."""
        if not names:
            for ts in self.toolsets.values():
                ts.enabled = True
            return
        for name in names:
            self.enable_toolset(name)

    def register_tools(self, mcp: FastMCP, *args) -> None:
        for ts in self.toolsets.values():
            ts.register_tools(mcp, *args)
