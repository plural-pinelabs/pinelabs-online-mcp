"""
Pine Labs API Documentation Fetcher & OpenAPI Parser.

Fetches markdown documentation from the Pine Labs developer portal,
caches it locally in ``md_files/``, and extracts structured API
information (endpoint, method, headers, request/response schemas)
from embedded OpenAPI JSON blocks.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import UTC, datetime
from typing import Any

import httpx

logger = logging.getLogger("pinelabs-mcp-server.api_docs_fetcher")

_MD_FILES_DIR = "md_files"
_FETCH_TIMEOUT = 10


class APIDocsFetcher:
    """Fetches and caches Pine Labs developer-portal markdown files."""

    @staticmethod
    async def fetch(url: str) -> dict[str, Any] | None:
        try:
            filename = url.split("/")[-1]
            if not filename:
                logger.error("Could not extract filename from URL: %s", url)
                return None

            os.makedirs(_MD_FILES_DIR, exist_ok=True)
            file_path = os.path.join(_MD_FILES_DIR, filename)

            if os.path.exists(file_path):
                logger.info("Using cached file: %s", file_path)
                with open(file_path, "r", encoding="utf-8") as fh:
                    raw_content = fh.read()
            else:
                logger.info("Fetching documentation from: %s", url)
                try:
                    async with httpx.AsyncClient(timeout=_FETCH_TIMEOUT) as client:
                        response = await client.get(url)
                except httpx.HTTPError as exc:
                    logger.error("Request failed for %s: %s", url, exc)
                    return None

                if response.status_code != 200:
                    logger.error("HTTP %s for %s", response.status_code, url)
                    return None

                raw_content = response.text
                try:
                    with open(file_path, "w", encoding="utf-8") as fh:
                        fh.write(raw_content)
                except OSError as exc:
                    logger.error("Failed to save file %s: %s", file_path, exc)

            parser = OpenAPIParser(content=raw_content)
            parsed_data = parser.extract_key_information()

            return {
                "content": {
                    "url": url,
                    "fetched_at": datetime.now(UTC).isoformat(),
                    "raw_markdown": raw_content,
                    "file_path": file_path,
                },
                "parsed_data": parsed_data,
            }
        except Exception:
            logger.exception("Error fetching documentation from %s", url)
            return None


class OpenAPIParser:
    """Extract structured API details from Pine Labs markdown documentation."""

    def __init__(self, *, content: str) -> None:
        self._content = content

    @staticmethod
    def _extract_openapi_json(content: str) -> dict[str, Any]:
        match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON in markdown: %s", exc)
            return {}

    @staticmethod
    def _extract_path_parameters(path: str) -> list[str]:
        return re.findall(r"\{([^}]+)\}", path)

    @staticmethod
    def _pick_method(methods: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        for m in ("post", "get", "put", "patch", "delete"):
            if m in methods:
                return m.upper(), methods[m]
        if methods:
            key = next(iter(methods))
            return key.upper(), methods[key]
        return "GET", {}

    @staticmethod
    def _extract_title(content: str) -> str:
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1).strip() if match else ""

    def extract_key_information(self) -> dict[str, Any]:
        content = self._content
        if not content:
            return {}

        spec = self._extract_openapi_json(content)
        if not spec:
            return self._extract_basic_info(content)

        try:
            servers = spec.get("servers", [])
            base_url = servers[0]["url"] if servers else ""

            paths = spec.get("paths", {})
            if not paths:
                return self._extract_basic_info(content)

            main_path = next(iter(paths))
            http_method, method_info = self._pick_method(paths[main_path])
            path_params = self._extract_path_parameters(main_path)

            headers: dict[str, Any] = {}
            query_params: dict[str, Any] = {}
            for param in method_info.get("parameters", []):
                info = {
                    "description": param.get("description", ""),
                    "required": param.get("required", False),
                    "type": param.get("schema", {}).get("type", "string"),
                }
                location = param.get("in")
                if location == "header":
                    headers[param["name"]] = info
                elif location == "query":
                    query_params[param["name"]] = info

            request_body_info: dict[str, Any] = {}
            request_examples: dict[str, Any] = {}
            if http_method in ("POST", "PUT", "PATCH"):
                rb = method_info.get("requestBody", {})
                json_content = rb.get("content", {}).get("application/json", {})
                schema = json_content.get("schema", {})
                properties = schema.get("properties", {})

                if "merchant_order_reference" in properties:
                    properties["merchant_order_reference"].update({
                        "type": "string",
                        "format": "uuid",
                        "description": (
                            "Enter a unique GUID/UUID string as identifier for "
                            "the order request."
                        ),
                    })

                request_body_info = {
                    "required_fields": schema.get("required", []),
                    "properties": properties,
                }
                examples = json_content.get("examples", {})
                if examples:
                    request_examples = examples

            response_info: dict[str, Any] = {}
            response_examples: dict[str, Any] = {}
            for status_code, resp_data in method_info.get("responses", {}).items():
                resp_json = resp_data.get("content", {}).get("application/json", {})
                response_info[status_code] = {
                    "description": resp_data.get("description", ""),
                    "schema": resp_json.get("schema", {}),
                }
                ex = resp_json.get("examples", {})
                if ex:
                    response_examples[status_code] = ex

            security = spec.get("security", [])
            auth_required = bool(security)

            title = (
                self._extract_title(content)
                or spec.get("info", {}).get("title", "API Documentation")
            )
            description = spec.get("info", {}).get("description", "")

            return {
                "title": title,
                "description": description,
                "endpoint_info": {
                    "base_url": base_url,
                    "path": main_path,
                    "full_url": base_url + main_path,
                    "method": http_method,
                    "path_parameters": path_params,
                },
                "authentication": {
                    "required": auth_required,
                    "type": "Bearer" if auth_required else None,
                },
                "headers": headers,
                "query_parameters": query_params,
                "request_body": request_body_info,
                "responses": response_info,
                "examples": {
                    "request_examples": request_examples,
                    "response_examples": response_examples,
                },
                "content_type": "application/json",
            }
        except Exception:
            logger.exception("Error extracting API information")
            return self._extract_basic_info(content)

    def _extract_basic_info(self, content: str) -> dict[str, Any]:
        title = self._extract_title(content) or "API Documentation"

        method_match = re.search(
            r"\b(GET|POST|PUT|DELETE|PATCH)\b", content, re.IGNORECASE
        )
        method = method_match.group(1).upper() if method_match else "POST"

        path_match = re.search(r"`(/[a-zA-Z0-9_/{}.-]+)`", content)
        path = path_match.group(1) if path_match else "/api/endpoint"

        description = ""
        desc_lines: list[str] = []
        in_desc = False
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.lower().startswith("## description"):
                in_desc = True
                continue
            if in_desc and stripped.startswith("##"):
                break
            if in_desc and stripped:
                desc_lines.append(stripped)
        if desc_lines:
            description = " ".join(desc_lines)

        return {
            "title": title,
            "description": description,
            "endpoint_info": {"method": method, "path": path},
        }
