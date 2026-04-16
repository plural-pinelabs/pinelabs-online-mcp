"""Tests for MCP API tools in tools/mcp_api.py."""

import json
from unittest.mock import AsyncMock

import pytest

from pkg.pinelabs.client import PineLabsClient, PineLabsAPIError
from pkg.pinelabs.mcp_api import register_mcp_api_tools


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeMCP:
    """Minimal MCP stub that captures registered tool functions."""

    def __init__(self):
        self.tools = {}

    def tool(self, name, description):
        def decorator(fn):
            self.tools[name] = fn
            return fn
        return decorator



def _make_tools(client):
    mcp = _FakeMCP()
    register_mcp_api_tools(mcp, client)
    return mcp.tools


# ---------------------------------------------------------------------------
# get_payment_link_details
# ---------------------------------------------------------------------------

class TestGetPaymentLinkDetails:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.get = AsyncMock(return_value={"data": [{"id": "pl-1", "status": "ACTIVE"}]})
        return c

    @pytest.mark.asyncio
    async def test_success_minimal(self, client):
        tools = _make_tools(client)
        result = await tools["get_payment_link_details"](
            merchant_id="merchant-123",
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
        )
        data = json.loads(result)
        assert "data" in data
        client.get.assert_awaited_once()
        call_args = client.get.call_args
        assert call_args[0][0] == "/mcp/v1/payment-link/details"
        assert call_args[1]["extra_headers"] == {"merchant-id": "merchant-123"}
        params = call_args[1]["params"]
        assert params["start_date"] == "2024-10-01T00:00:00"
        assert params["end_date"] == "2024-10-09T23:59:59"

    @pytest.mark.asyncio
    async def test_success_with_pagination(self, client):
        tools = _make_tools(client)
        result = await tools["get_payment_link_details"](
            merchant_id="merchant-123",
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
            page=2,
            per_page=10,
        )
        data = json.loads(result)
        assert "data" in data
        params = client.get.call_args[1]["params"]
        assert params["page"] == "2"
        assert params["per_page"] == "10"

    @pytest.mark.asyncio
    async def test_api_error(self, client):
        client.get = AsyncMock(side_effect=PineLabsAPIError(400, "BAD_REQUEST", "Invalid request"))
        tools = _make_tools(client)
        result = await tools["get_payment_link_details"](
            merchant_id="merchant-123",
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
        )
        data = json.loads(result)
        assert data["code"] == "BAD_REQUEST"

    @pytest.mark.asyncio
    async def test_unexpected_error(self, client):
        client.get = AsyncMock(side_effect=RuntimeError("boom"))
        tools = _make_tools(client)
        result = await tools["get_payment_link_details"](
            merchant_id="merchant-123",
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
        )
        data = json.loads(result)
        assert data["code"] == "INTERNAL_ERROR"


# ---------------------------------------------------------------------------
# get_order_details
# ---------------------------------------------------------------------------

class TestGetOrderDetails:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.get = AsyncMock(return_value={"data": [{"order_id": "ord-1"}]})
        return c

    @pytest.mark.asyncio
    async def test_success_minimal(self, client):
        tools = _make_tools(client)
        result = await tools["get_order_details"](
            merchant_id="merchant-123",
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
        )
        data = json.loads(result)
        assert "data" in data
        call_args = client.get.call_args
        assert call_args[0][0] == "/mcp/v1/order/details"
        assert call_args[1]["extra_headers"] == {"merchant-id": "merchant-123"}

    @pytest.mark.asyncio
    async def test_api_error(self, client):
        client.get = AsyncMock(side_effect=PineLabsAPIError(500, "SERVER_ERROR", "Server error"))
        tools = _make_tools(client)
        result = await tools["get_order_details"](
            merchant_id="merchant-123",
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
        )
        data = json.loads(result)
        assert data["code"] == "SERVER_ERROR"


# ---------------------------------------------------------------------------
# get_refund_order_details
# ---------------------------------------------------------------------------

class TestGetRefundOrderDetails:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.get = AsyncMock(return_value={"data": [{"refund_id": "ref-1"}]})
        return c

    @pytest.mark.asyncio
    async def test_success_minimal(self, client):
        tools = _make_tools(client)
        result = await tools["get_refund_order_details"](
            merchant_id="merchant-123",
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
        )
        data = json.loads(result)
        assert "data" in data
        call_args = client.get.call_args
        assert call_args[0][0] == "/mcp/v1/refund/order/details"
        assert call_args[1]["extra_headers"] == {"merchant-id": "merchant-123"}

    @pytest.mark.asyncio
    async def test_success_with_pagination(self, client):
        tools = _make_tools(client)
        result = await tools["get_refund_order_details"](
            merchant_id="merchant-123",
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
            page=1,
            per_page=20,
        )
        data = json.loads(result)
        assert "data" in data


# ---------------------------------------------------------------------------
# search_transaction
# ---------------------------------------------------------------------------

class TestSearchTransaction:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.get = AsyncMock(return_value={"transaction_id": "txn-456", "status": "SUCCESS"})
        return c

    @pytest.mark.asyncio
    async def test_success(self, client):
        tools = _make_tools(client)
        result = await tools["search_transaction"](
            merchant_id="merchant-123",
            transaction_id="txn-456",
        )
        data = json.loads(result)
        assert data["transaction_id"] == "txn-456"
        call_args = client.get.call_args
        assert call_args[0][0] == "/mcp/v1/search/transaction/txn-456"
        assert call_args[1]["extra_headers"] == {"merchant-id": "merchant-123"}

    @pytest.mark.asyncio
    async def test_api_error(self, client):
        client.get = AsyncMock(side_effect=PineLabsAPIError(404, "NOT_FOUND", "Transaction not found"))
        tools = _make_tools(client)
        result = await tools["search_transaction"](
            merchant_id="merchant-123",
            transaction_id="txn-999",
        )
        data = json.loads(result)
        assert data["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_unexpected_error(self, client):
        client.get = AsyncMock(side_effect=RuntimeError("boom"))
        tools = _make_tools(client)
        result = await tools["search_transaction"](
            merchant_id="merchant-123",
            transaction_id="txn-456",
        )
        data = json.loads(result)
        assert data["code"] == "INTERNAL_ERROR"


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

class TestMcpApiValidation:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.get = AsyncMock(return_value={})
        return c

    # -- merchant_id validation --

    @pytest.mark.asyncio
    async def test_empty_merchant_id(self, client):
        tools = _make_tools(client)
        result = await tools["get_payment_link_details"](
            merchant_id="",
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
        )
        data = json.loads(result)
        assert data["code"] == "VALIDATION_ERROR"
        assert "merchant_id" in data["error"]

    @pytest.mark.asyncio
    async def test_merchant_id_with_special_chars(self, client):
        tools = _make_tools(client)
        result = await tools["get_order_details"](
            merchant_id="../../etc/passwd",
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
        )
        data = json.loads(result)
        assert data["code"] == "VALIDATION_ERROR"

    # -- date range validation --

    @pytest.mark.asyncio
    async def test_invalid_date_format(self, client):
        tools = _make_tools(client)
        result = await tools["get_payment_link_details"](
            merchant_id="merchant-123",
            start_date="not-a-date",
            end_date="2024-10-09T23:59:59",
        )
        data = json.loads(result)
        assert data["code"] == "VALIDATION_ERROR"
        assert "ISO 8601" in data["error"]

    @pytest.mark.asyncio
    async def test_end_date_before_start_date(self, client):
        tools = _make_tools(client)
        result = await tools["get_refund_order_details"](
            merchant_id="merchant-123",
            start_date="2024-10-09T23:59:59",
            end_date="2024-10-01T00:00:00",
        )
        data = json.loads(result)
        assert data["code"] == "VALIDATION_ERROR"
        assert "end_date" in data["error"]

    @pytest.mark.asyncio
    async def test_date_range_exceeds_60_days(self, client):
        tools = _make_tools(client)
        result = await tools["get_order_details"](
            merchant_id="merchant-123",
            start_date="2024-01-01T00:00:00",
            end_date="2024-06-01T00:00:00",
        )
        data = json.loads(result)
        assert data["code"] == "VALIDATION_ERROR"
        assert "60 days" in data["error"]

    # -- pagination validation --

    @pytest.mark.asyncio
    async def test_page_zero(self, client):
        tools = _make_tools(client)
        result = await tools["get_payment_link_details"](
            merchant_id="merchant-123",
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
            page=0,
        )
        data = json.loads(result)
        assert data["code"] == "VALIDATION_ERROR"
        assert "page" in data["error"]

    @pytest.mark.asyncio
    async def test_per_page_zero(self, client):
        tools = _make_tools(client)
        result = await tools["get_payment_link_details"](
            merchant_id="merchant-123",
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
            per_page=0,
        )
        data = json.loads(result)
        assert data["code"] == "VALIDATION_ERROR"
        assert "per_page" in data["error"]

    @pytest.mark.asyncio
    async def test_per_page_exceeds_max(self, client):
        tools = _make_tools(client)
        result = await tools["get_payment_link_details"](
            merchant_id="merchant-123",
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
            per_page=101,
        )
        data = json.loads(result)
        assert data["code"] == "VALIDATION_ERROR"

    # -- path param validation --

    @pytest.mark.asyncio
    async def test_empty_transaction_id(self, client):
        tools = _make_tools(client)
        result = await tools["search_transaction"](
            merchant_id="merchant-123",
            transaction_id="",
        )
        data = json.loads(result)
        assert data["code"] == "VALIDATION_ERROR"
        assert "transaction_id" in data["error"]

    @pytest.mark.asyncio
    async def test_transaction_id_with_slashes(self, client):
        tools = _make_tools(client)
        result = await tools["search_transaction"](
            merchant_id="merchant-123",
            transaction_id="../../etc",
        )
        data = json.loads(result)
        assert data["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

class TestToolRegistration:
    def test_all_five_tools_registered(self):
        client = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        tools = _make_tools(client)
        expected_tools = {
            "get_payment_link_details",
            "get_order_details",
            "get_refund_order_details",
            "search_transaction",
        }
        assert set(tools.keys()) == expected_tools
