"""Tests for tools/orders.py — get_order_by_order_id."""

import json
from unittest.mock import AsyncMock

import pytest

from pkg.pinelabs.client import PineLabsClient, PineLabsAPIError
from pkg.pinelabs.orders import register_order_tools


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
    register_order_tools(mcp, client)
    return mcp.tools


# ---------------------------------------------------------------------------
# get_order_by_order_id
# ---------------------------------------------------------------------------

class TestGetOrderByOrderId:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.get = AsyncMock(return_value={
            "order_id": "v1-4405071524-aa-qlAtAf",
            "status": "PROCESSED",
            "type": "CHARGE",
            "order_amount": {"value": 50000, "currency": "INR"},
        })
        return c

    # -- Happy path --
    @pytest.mark.asyncio
    async def test_success(self, client):
        tools = _make_tools(client)
        result = await tools["get_order_by_order_id"](
            order_id="v1-4405071524-aa-qlAtAf",
        )
        data = json.loads(result)
        assert data["order_id"] == "v1-4405071524-aa-qlAtAf"
        assert data["status"] == "PROCESSED"
        client.get.assert_awaited_once()
        call_args = client.get.call_args
        assert "/pay/v1/orders/v1-4405071524-aa-qlAtAf" == call_args[0][0]

    # -- Missing auth --
    @pytest.mark.asyncio
    async def test_missing_auth(self, client):
        client.get = AsyncMock(
            side_effect=RuntimeError("Client credentials not configured")
        )
        tools = _make_tools(client)
        result = await tools["get_order_by_order_id"](
            order_id="v1-4405071524-aa-qlAtAf",
        )
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()

    # -- API error --
    @pytest.mark.asyncio
    async def test_api_error(self, client):
        client.get = AsyncMock(
            side_effect=PineLabsAPIError(404, "NOT_FOUND", "Order not found")
        )
        tools = _make_tools(client)
        result = await tools["get_order_by_order_id"](
            order_id="v1-4405071524-aa-qlAtAf",
        )
        data = json.loads(result)
        assert data["error"] == "Order not found"
        assert data["code"] == "NOT_FOUND"
        assert data["status_code"] == 404

    # -- Unexpected error (generic) --
    @pytest.mark.asyncio
    async def test_unexpected_error(self, client):
        client.get = AsyncMock(side_effect=RuntimeError("connection reset"))
        tools = _make_tools(client)
        result = await tools["get_order_by_order_id"](
            order_id="v1-4405071524-aa-qlAtAf",
        )
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()
        # Must NOT expose raw exception text
        assert "connection reset" not in data["error"]

    # -- Input validation --
    @pytest.mark.asyncio
    async def test_empty_order_id(self, client):
        tools = _make_tools(client)
        result = await tools["get_order_by_order_id"](order_id="")
        data = json.loads(result)
        assert "error" in data
        assert "order_id" in data["error"]

    @pytest.mark.asyncio
    async def test_invalid_order_id_special_chars(self, client):
        tools = _make_tools(client)
        result = await tools["get_order_by_order_id"](
            order_id="../../../etc/passwd",
        )
        data = json.loads(result)
        assert "error" in data
        assert "invalid characters" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_injection_attempt_rejected(self, client):
        tools = _make_tools(client)
        result = await tools["get_order_by_order_id"](
            order_id="v1-test; DROP TABLE orders",
        )
        data = json.loads(result)
        assert "error" in data
        assert "invalid characters" in data["error"].lower()
