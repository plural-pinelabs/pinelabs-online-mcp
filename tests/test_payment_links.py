"""Tests for tools/payment_links.py — all payment link tools."""

import json
from unittest.mock import AsyncMock

import pytest

from pkg.pinelabs.client import PineLabsClient, PineLabsAPIError
from pkg.pinelabs.payment_links import register_payment_link_tools


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
    register_payment_link_tools(mcp, client)
    return mcp.tools


# ---------------------------------------------------------------------------
# create_payment_link
# ---------------------------------------------------------------------------

class TestCreatePaymentLink:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.post = AsyncMock(return_value={
            "payment_link_id": "pl-v1-123-aa-xyz",
            "status": "CREATED",
            "short_url": "https://pay.pine.test/abc",
        })
        return c

    # -- Happy path --
    @pytest.mark.asyncio
    async def test_success_minimal(self, client):
        tools = _make_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_email="test@example.com",
        )
        data = json.loads(result)
        assert data["payment_link_id"] == "pl-v1-123-aa-xyz"
        assert data["status"] == "CREATED"
        client.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_success_with_customer(self, client):
        tools = _make_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_email="test@example.com",
            customer_first_name="John",
        )
        data = json.loads(result)
        assert data["status"] == "CREATED"

    # -- Missing auth --
    @pytest.mark.asyncio
    async def test_missing_auth(self, client):
        client.post = AsyncMock(
            side_effect=RuntimeError("Client credentials not configured")
        )
        tools = _make_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_email="test@example.com",
        )
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()

    # -- API error --
    @pytest.mark.asyncio
    async def test_api_error(self, client):
        client.post = AsyncMock(
            side_effect=PineLabsAPIError(400, "BAD_REQUEST", "Invalid amount")
        )
        tools = _make_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_email="test@example.com",
        )
        data = json.loads(result)
        assert data["error"] == "Invalid amount"
        assert data["code"] == "BAD_REQUEST"
        assert data["status_code"] == 400

    # -- Unexpected error --
    @pytest.mark.asyncio
    async def test_unexpected_error(self, client):
        client.post = AsyncMock(side_effect=RuntimeError("network down"))
        tools = _make_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_email="test@example.com",
        )
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()
        assert "network down" not in data["error"]

    # -- Input validation --
    @pytest.mark.asyncio
    async def test_invalid_payment_method(self, client):
        tools = _make_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_email="test@example.com",
            allowed_payment_methods=["INVALID_METHOD"],
        )
        data = json.loads(result)
        assert "error" in data
        assert "Invalid payment method" in data["error"]


# ---------------------------------------------------------------------------
# get_payment_link_by_id
# ---------------------------------------------------------------------------

class TestGetPaymentLinkById:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.get = AsyncMock(return_value={
            "payment_link_id": "pl-v1-123-aa-xyz",
            "status": "CREATED",
            "amount": {"value": 50000, "currency": "INR"},
        })
        return c

    # -- Happy path --
    @pytest.mark.asyncio
    async def test_success(self, client):
        tools = _make_tools(client)
        result = await tools["get_payment_link_by_id"](
            payment_link_id="pl-v1-123-aa-xyz",
        )
        data = json.loads(result)
        assert data["payment_link_id"] == "pl-v1-123-aa-xyz"

    # -- Missing auth --
    @pytest.mark.asyncio
    async def test_missing_auth(self, client):
        client.get = AsyncMock(
            side_effect=RuntimeError("Client credentials not configured")
        )
        tools = _make_tools(client)
        result = await tools["get_payment_link_by_id"](
            payment_link_id="pl-v1-123-aa-xyz",
        )
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()

    # -- API error --
    @pytest.mark.asyncio
    async def test_api_error(self, client):
        client.get = AsyncMock(
            side_effect=PineLabsAPIError(404, "NOT_FOUND", "Payment link not found")
        )
        tools = _make_tools(client)
        result = await tools["get_payment_link_by_id"](
            payment_link_id="pl-v1-123-aa-xyz",
        )
        data = json.loads(result)
        assert data["error"] == "Payment link not found"
        assert data["code"] == "NOT_FOUND"

    # -- Unexpected error --
    @pytest.mark.asyncio
    async def test_unexpected_error(self, client):
        client.get = AsyncMock(side_effect=RuntimeError("timeout"))
        tools = _make_tools(client)
        result = await tools["get_payment_link_by_id"](
            payment_link_id="pl-v1-123-aa-xyz",
        )
        data = json.loads(result)
        assert "internal error" in data["error"].lower()

    # -- Input validation --
    @pytest.mark.asyncio
    async def test_empty_payment_link_id(self, client):
        tools = _make_tools(client)
        result = await tools["get_payment_link_by_id"](payment_link_id="")
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_payment_link_id_too_long(self, client):
        tools = _make_tools(client)
        result = await tools["get_payment_link_by_id"](
            payment_link_id="x" * 51,
        )
        data = json.loads(result)
        assert "error" in data
        assert "50 characters" in data["error"]


# ---------------------------------------------------------------------------
# get_payment_link_by_merchant_reference
# ---------------------------------------------------------------------------

class TestGetPaymentLinkByMerchantReference:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.get = AsyncMock(return_value={
            "payment_link_id": "pl-v1-123-aa-xyz",
            "status": "CREATED",
        })
        return c

    # -- Happy path --
    @pytest.mark.asyncio
    async def test_success(self, client):
        tools = _make_tools(client)
        result = await tools["get_payment_link_by_merchant_reference"](
            merchant_payment_link_reference="ref-abc-123",
        )
        data = json.loads(result)
        assert data["payment_link_id"] == "pl-v1-123-aa-xyz"

    # -- Missing auth --
    @pytest.mark.asyncio
    async def test_missing_auth(self, client):
        client.get = AsyncMock(
            side_effect=RuntimeError("Client credentials not configured")
        )
        tools = _make_tools(client)
        result = await tools["get_payment_link_by_merchant_reference"](
            merchant_payment_link_reference="ref-abc-123",
        )
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()

    # -- API error --
    @pytest.mark.asyncio
    async def test_api_error(self, client):
        client.get = AsyncMock(
            side_effect=PineLabsAPIError(404, "NOT_FOUND", "Not found")
        )
        tools = _make_tools(client)
        result = await tools["get_payment_link_by_merchant_reference"](
            merchant_payment_link_reference="ref-abc-123",
        )
        data = json.loads(result)
        assert data["error"] == "Not found"

    # -- Unexpected error --
    @pytest.mark.asyncio
    async def test_unexpected_error(self, client):
        client.get = AsyncMock(side_effect=RuntimeError("oops"))
        tools = _make_tools(client)
        result = await tools["get_payment_link_by_merchant_reference"](
            merchant_payment_link_reference="ref-abc-123",
        )
        data = json.loads(result)
        assert "internal error" in data["error"].lower()

    # -- Input validation --
    @pytest.mark.asyncio
    async def test_reference_too_long(self, client):
        tools = _make_tools(client)
        result = await tools["get_payment_link_by_merchant_reference"](
            merchant_payment_link_reference="x" * 51,
        )
        data = json.loads(result)
        assert "error" in data
        assert "50 characters" in data["error"]


# ---------------------------------------------------------------------------
# cancel_payment_link
# ---------------------------------------------------------------------------

class TestCancelPaymentLink:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.put = AsyncMock(return_value={
            "payment_link_id": "pl-v1-123-aa-xyz",
            "status": "CANCELLED",
        })
        return c

    # -- Happy path --
    @pytest.mark.asyncio
    async def test_success(self, client):
        tools = _make_tools(client)
        result = await tools["cancel_payment_link"](
            payment_link_id="pl-v1-123-aa-xyz",
        )
        data = json.loads(result)
        assert data["status"] == "CANCELLED"

    # -- Missing auth --
    @pytest.mark.asyncio
    async def test_missing_auth(self, client):
        client.put = AsyncMock(
            side_effect=RuntimeError("Client credentials not configured")
        )
        tools = _make_tools(client)
        result = await tools["cancel_payment_link"](
            payment_link_id="pl-v1-123-aa-xyz",
        )
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()

    # -- API error --
    @pytest.mark.asyncio
    async def test_api_error(self, client):
        client.put = AsyncMock(
            side_effect=PineLabsAPIError(422, "INVALID_STATE", "Already paid")
        )
        tools = _make_tools(client)
        result = await tools["cancel_payment_link"](
            payment_link_id="pl-v1-123-aa-xyz",
        )
        data = json.loads(result)
        assert data["error"] == "Already paid"

    # -- Unexpected error --
    @pytest.mark.asyncio
    async def test_unexpected_error(self, client):
        client.put = AsyncMock(side_effect=RuntimeError("err"))
        tools = _make_tools(client)
        result = await tools["cancel_payment_link"](
            payment_link_id="pl-v1-123-aa-xyz",
        )
        data = json.loads(result)
        assert "internal error" in data["error"].lower()

    # -- Input validation --
    @pytest.mark.asyncio
    async def test_empty_payment_link_id(self, client):
        tools = _make_tools(client)
        result = await tools["cancel_payment_link"](payment_link_id="")
        data = json.loads(result)
        assert "error" in data


# ---------------------------------------------------------------------------
# resend_payment_link_notification
# ---------------------------------------------------------------------------

class TestResendPaymentLinkNotification:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.patch = AsyncMock(return_value={
            "payment_link_id": "pl-v1-123-aa-xyz",
            "status": "CREATED",
        })
        return c

    # -- Happy path --
    @pytest.mark.asyncio
    async def test_success(self, client):
        tools = _make_tools(client)
        result = await tools["resend_payment_link_notification"](
            payment_link_id="pl-v1-123-aa-xyz",
        )
        data = json.loads(result)
        assert data["status"] == "CREATED"

    # -- Missing auth --
    @pytest.mark.asyncio
    async def test_missing_auth(self, client):
        client.patch = AsyncMock(
            side_effect=RuntimeError("Client credentials not configured")
        )
        tools = _make_tools(client)
        result = await tools["resend_payment_link_notification"](
            payment_link_id="pl-v1-123-aa-xyz",
        )
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()

    # -- API error --
    @pytest.mark.asyncio
    async def test_api_error(self, client):
        client.patch = AsyncMock(
            side_effect=PineLabsAPIError(404, "NOT_FOUND", "Link not found")
        )
        tools = _make_tools(client)
        result = await tools["resend_payment_link_notification"](
            payment_link_id="pl-v1-123-aa-xyz",
        )
        data = json.loads(result)
        assert data["error"] == "Link not found"

    # -- Unexpected error --
    @pytest.mark.asyncio
    async def test_unexpected_error(self, client):
        client.patch = AsyncMock(side_effect=RuntimeError("err"))
        tools = _make_tools(client)
        result = await tools["resend_payment_link_notification"](
            payment_link_id="pl-v1-123-aa-xyz",
        )
        data = json.loads(result)
        assert "internal error" in data["error"].lower()

    # -- Input validation --
    @pytest.mark.asyncio
    async def test_empty_payment_link_id(self, client):
        tools = _make_tools(client)
        result = await tools["resend_payment_link_notification"](
            payment_link_id="",
        )
        data = json.loads(result)
        assert "error" in data
