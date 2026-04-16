"""Tests for API documentation tools (get_api_documentation, list_pinelabs_apis)."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from pkg.pinelabs.api_docs_fetcher import APIDocsFetcher, OpenAPIParser
from pkg.pinelabs.api_docs import register_api_docs_tools
from pkg.pinelabs.utils.api_docs_config import API_DOCUMENTATION


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_OPENAPI_MARKDOWN = """\
# Create Order

Create a new order for payment processing.

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Create Order API",
    "description": "Creates a new payment order"
  },
  "servers": [
    {"url": "https://api.pluralpay.in/api"}
  ],
  "security": [{"bearerAuth": []}],
  "paths": {
    "/pay/v1/orders": {
      "post": {
        "summary": "Create order",
        "parameters": [
          {
            "name": "Authorization",
            "in": "header",
            "required": true,
            "schema": {"type": "string"},
            "description": "Bearer token"
          },
          {
            "name": "page",
            "in": "query",
            "required": false,
            "schema": {"type": "integer"},
            "description": "Page number"
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "required": ["amount", "merchant_order_reference"],
                "properties": {
                  "amount": {"type": "object"},
                  "merchant_order_reference": {"type": "string"}
                }
              },
              "examples": {
                "basic": {"value": {"amount": {"value": 1000, "currency": "INR"}}}
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Order created",
            "content": {
              "application/json": {
                "schema": {"type": "object"},
                "examples": {"success": {"value": {"order_id": "123"}}}
              }
            }
          }
        }
      }
    }
  }
}
```
"""

SAMPLE_BASIC_MARKDOWN = """\
# Get Payment Status

## Description

This API lets you check the current payment status.

Use `GET` method at `/pay/v1/payments/{paymentId}`.
"""

SAMPLE_NO_CONTENT = ""


class _FakeMCP:
    """Lightweight stub that captures tool registrations."""

    def __init__(self) -> None:
        self.tools: dict[str, object] = {}

    def tool(self, name: str, description: str):
        def decorator(fn):
            self.tools[name] = fn
            return fn
        return decorator


@pytest.fixture()
def fake_mcp() -> _FakeMCP:
    return _FakeMCP()


# ---------------------------------------------------------------------------
# OpenAPIParser tests
# ---------------------------------------------------------------------------


class TestOpenAPIParser:
    """Tests for the OpenAPIParser class."""

    def test_parse_full_openapi_spec(self):
        parser = OpenAPIParser(content=SAMPLE_OPENAPI_MARKDOWN)
        result = parser.extract_key_information()

        assert result["title"] == "Create Order"
        assert result["endpoint_info"]["base_url"] == "https://api.pluralpay.in/api"
        assert result["endpoint_info"]["path"] == "/pay/v1/orders"
        assert result["endpoint_info"]["method"] == "POST"
        assert result["authentication"]["required"] is True
        assert result["authentication"]["type"] == "Bearer"
        assert "Authorization" in result["headers"]
        assert "page" in result["query_parameters"]
        assert "amount" in result["request_body"]["properties"]
        assert "200" in result["responses"]
        assert result["content_type"] == "application/json"

    def test_parse_request_body_required_fields(self):
        parser = OpenAPIParser(content=SAMPLE_OPENAPI_MARKDOWN)
        result = parser.extract_key_information()

        assert "amount" in result["request_body"]["required_fields"]
        assert "merchant_order_reference" in result["request_body"]["required_fields"]

    def test_merchant_order_reference_enrichment(self):
        parser = OpenAPIParser(content=SAMPLE_OPENAPI_MARKDOWN)
        result = parser.extract_key_information()

        mor = result["request_body"]["properties"]["merchant_order_reference"]
        assert mor["format"] == "uuid"
        assert "GUID" in mor["description"]

    def test_parse_examples(self):
        parser = OpenAPIParser(content=SAMPLE_OPENAPI_MARKDOWN)
        result = parser.extract_key_information()

        assert result["examples"]["request_examples"]
        assert "200" in result["examples"]["response_examples"]

    def test_fallback_basic_info(self):
        parser = OpenAPIParser(content=SAMPLE_BASIC_MARKDOWN)
        result = parser.extract_key_information()

        assert result["title"] == "Get Payment Status"
        assert result["endpoint_info"]["method"] == "GET"
        assert result["endpoint_info"]["path"] == "/pay/v1/payments/{paymentId}"
        assert "payment status" in result["description"]

    def test_empty_content_returns_empty(self):
        parser = OpenAPIParser(content=SAMPLE_NO_CONTENT)
        result = parser.extract_key_information()
        assert result == {}

    def test_extract_path_parameters(self):
        params = OpenAPIParser._extract_path_parameters("/v1/orders/{orderId}/payments/{payId}")
        assert params == ["orderId", "payId"]

    def test_pick_method_priority(self):
        method, _ = OpenAPIParser._pick_method({"get": {}, "post": {}})
        assert method == "POST"

    def test_pick_method_single(self):
        method, _ = OpenAPIParser._pick_method({"delete": {"summary": "del"}})
        assert method == "DELETE"

    def test_pick_method_empty(self):
        method, _ = OpenAPIParser._pick_method({})
        assert method == "GET"

    def test_extract_title(self):
        assert OpenAPIParser._extract_title("# My API Title\n\nSome content") == "My API Title"
        assert OpenAPIParser._extract_title("No title here") == ""

    def test_invalid_json_in_markdown(self):
        bad_md = "# Test\n\n```json\n{invalid json}\n```\n"
        parser = OpenAPIParser(content=bad_md)
        result = parser.extract_key_information()
        # Falls back to basic info since JSON is invalid
        assert result["title"] == "Test"

    def test_openapi_no_paths(self):
        md = '# Test\n\n```json\n{"openapi": "3.0.0", "paths": {}}\n```\n'
        parser = OpenAPIParser(content=md)
        result = parser.extract_key_information()
        # Falls back to basic info
        assert result["title"] == "Test"


# ---------------------------------------------------------------------------
# APIDocsFetcher tests
# ---------------------------------------------------------------------------


class TestAPIDocsFetcher:
    """Tests for the APIDocsFetcher class."""

    @pytest.mark.asyncio
    async def test_fetch_cache_hit(self, tmp_path, monkeypatch):
        """When a cached file exists, it should be read from disk."""
        monkeypatch.setattr("pkg.pinelabs.api_docs_fetcher._MD_FILES_DIR", str(tmp_path))

        # Write a cached file
        cached = tmp_path / "orders-create.md"
        cached.write_text(SAMPLE_OPENAPI_MARKDOWN, encoding="utf-8")

        result = await APIDocsFetcher.fetch(
            "https://developer.pinelabsonline.com/reference/orders-create.md"
        )

        assert result is not None
        assert result["content"]["raw_markdown"] == SAMPLE_OPENAPI_MARKDOWN
        assert result["parsed_data"]["title"] == "Create Order"

    @pytest.mark.asyncio
    async def test_fetch_cache_miss(self, tmp_path, monkeypatch):
        """When file not cached, should fetch via HTTP and cache it."""
        monkeypatch.setattr("pkg.pinelabs.api_docs_fetcher._MD_FILES_DIR", str(tmp_path))

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_OPENAPI_MARKDOWN

        with patch("pkg.pinelabs.api_docs_fetcher.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            result = await APIDocsFetcher.fetch(
                "https://developer.pinelabsonline.com/reference/orders-create.md"
            )

        assert result is not None
        assert result["parsed_data"]["title"] == "Create Order"
        # File should now be cached
        assert (tmp_path / "orders-create.md").exists()

    @pytest.mark.asyncio
    async def test_fetch_http_error(self, tmp_path, monkeypatch):
        """HTTP error should return None."""
        monkeypatch.setattr("pkg.pinelabs.api_docs_fetcher._MD_FILES_DIR", str(tmp_path))

        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        with patch("pkg.pinelabs.api_docs_fetcher.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            result = await APIDocsFetcher.fetch(
                "https://developer.pinelabsonline.com/reference/nonexistent.md"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_network_error(self, tmp_path, monkeypatch):
        """Network exception should return None."""
        monkeypatch.setattr("pkg.pinelabs.api_docs_fetcher._MD_FILES_DIR", str(tmp_path))

        import httpx

        with patch("pkg.pinelabs.api_docs_fetcher.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = httpx.ConnectError("Connection refused")
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            result = await APIDocsFetcher.fetch(
                "https://developer.pinelabsonline.com/reference/orders-create.md"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_empty_filename(self):
        """URL with no filename should return None."""
        result = await APIDocsFetcher.fetch("https://developer.pinelabsonline.com/")
        assert result is None


# ---------------------------------------------------------------------------
# Tool registration tests
# ---------------------------------------------------------------------------


class TestAPIDocsTools:
    """Tests for the registered MCP tools."""

    @pytest.fixture(autouse=True)
    def _register(self, fake_mcp):
        register_api_docs_tools(fake_mcp)
        self.mcp = fake_mcp

    @pytest.mark.asyncio
    async def test_list_pinelabs_apis_no_filter(self):
        fn = self.mcp.tools["list_pinelabs_apis"]
        result = json.loads(await fn())

        assert result["total"] == len(API_DOCUMENTATION)
        assert len(result["apis"]) == len(API_DOCUMENTATION)
        assert "search" not in result

    @pytest.mark.asyncio
    async def test_list_pinelabs_apis_with_search(self):
        fn = self.mcp.tools["list_pinelabs_apis"]
        result = json.loads(await fn(search="order"))

        assert result["search"] == "order"
        assert result["total"] > 0
        for api in result["apis"]:
            assert (
                "order" in api["name"].lower()
                or "order" in api["description"].lower()
            )

    @pytest.mark.asyncio
    async def test_list_pinelabs_apis_no_match(self):
        fn = self.mcp.tools["list_pinelabs_apis"]
        result = json.loads(await fn(search="zzz_no_match_zzz"))

        assert result["total"] == 0
        assert result["apis"] == []

    @pytest.mark.asyncio
    async def test_get_api_documentation_invalid_name(self):
        fn = self.mcp.tools["get_api_documentation"]
        result = json.loads(await fn(api_name="nonexistent_api"))

        assert "error" in result
        assert "nonexistent_api" in result["error"]
        assert "available_apis" in result

    @pytest.mark.asyncio
    async def test_get_api_documentation_success(self):
        fn = self.mcp.tools["get_api_documentation"]

        mock_data = {
            "content": {
                "url": "https://example.com/test.md",
                "fetched_at": "2026-01-01T00:00:00+00:00",
                "raw_markdown": SAMPLE_OPENAPI_MARKDOWN,
                "file_path": "md_files/test.md",
            },
            "parsed_data": {
                "title": "Create Order",
                "endpoint_info": {"method": "POST", "path": "/pay/v1/orders"},
            },
        }

        with patch.object(APIDocsFetcher, "fetch", new_callable=AsyncMock, return_value=mock_data):
            result = json.loads(await fn(api_name="create_order"))

        assert result["api_name"] == "create_order"
        assert result["parsed_specification"]["title"] == "Create Order"
        assert "raw_markdown_preview" in result
        assert result["documentation_url"].endswith("/reference/orders-create")

    @pytest.mark.asyncio
    async def test_get_api_documentation_fetch_failure(self):
        fn = self.mcp.tools["get_api_documentation"]

        with patch.object(APIDocsFetcher, "fetch", new_callable=AsyncMock, return_value=None):
            result = json.loads(await fn(api_name="create_order"))

        assert "error" in result
        assert "Could not fetch" in result["error"]


# ---------------------------------------------------------------------------
# Config completeness
# ---------------------------------------------------------------------------


class TestAPIDocsConfig:
    """Verify the API documentation catalog."""

    def test_all_entries_have_required_keys(self):
        for name, info in API_DOCUMENTATION.items():
            assert "url" in info, f"{name} missing 'url'"
            assert "description" in info, f"{name} missing 'description'"
            assert info["url"].startswith("https://"), f"{name} URL is not HTTPS"
            assert info["url"].endswith(".md"), f"{name} URL doesn't end with .md"

    def test_catalog_not_empty(self):
        assert len(API_DOCUMENTATION) >= 60
