"""
Pine Labs API Documentation MCP tools.

Provides:
1. get_api_documentation — Fetch and parse docs for a specific API
2. list_pinelabs_apis — List all available API names with descriptions
"""

import json
import logging
from typing import Optional

from fastmcp import FastMCP

from pkg.pinelabs.api_docs_fetcher import APIDocsFetcher
from pkg.pinelabs.utils.api_docs_config import API_DOCUMENTATION

logger = logging.getLogger("pinelabs-mcp-server.api_docs")


def register_api_docs_tools(mcp: FastMCP) -> None:
    """Register API documentation tools on the FastMCP server."""

    @mcp.tool(
        name="get_api_documentation",
        description=(
            "Fetch Pine Labs API documentation for a specific "
            "API. Returns parsed OpenAPI specification. Use "
            "'list_pinelabs_apis' first to discover available names."
        ),
    )
    async def get_api_documentation(api_name: str) -> str:
        """Fetch structured docs for the given Pine Labs API."""
        if api_name not in API_DOCUMENTATION:
            available = sorted(API_DOCUMENTATION.keys())
            return json.dumps(
                {
                    "error": f"API '{api_name}' not found.",
                    "available_apis": available,
                },
                indent=2,
            )

        api_info = API_DOCUMENTATION[api_name]
        api_data = await APIDocsFetcher.fetch(api_info["url"])

        if not api_data:
            return json.dumps(
                {
                    "error": (
                        "Could not fetch documentation from "
                        f"{api_info['url']}."
                    ),
                },
                indent=2,
            )

        raw_content = api_data.get(
            "content", {},
        ).get("raw_markdown", "")
        parsed = api_data.get("parsed_data", {})

        doc_url = api_info["url"]
        if doc_url.endswith(".md"):
            doc_url = doc_url[:-3]

        result = {
            "api_name": api_name,
            "description": api_info["description"],
            "documentation_url": doc_url,
            "raw_markdown_preview": (
                raw_content[:2000]
                + ("..." if len(raw_content) > 2000 else "")
            ),
            "parsed_specification": parsed,
        }

        return json.dumps(
            result, indent=2, ensure_ascii=False,
        )

    @mcp.tool(
        name="list_pinelabs_apis",
        description=(
            "List all available Pine Labs APIs with descriptions. "
            "Optionally pass a search keyword to filter results."
        ),
    )
    async def list_pinelabs_apis(
        search: Optional[str] = None,
    ) -> str:
        """List available Pine Labs APIs."""
        if search:
            needle = search.lower()
            matching = {
                name: info
                for name, info in API_DOCUMENTATION.items()
                if needle in name.lower()
                or needle in info["description"].lower()
            }
        else:
            matching = API_DOCUMENTATION

        apis = [
            {"name": name, "description": info["description"]}
            for name, info in matching.items()
        ]

        result = {"total": len(apis), "apis": apis}
        if search:
            result["search"] = search

        return json.dumps(result, indent=2)
