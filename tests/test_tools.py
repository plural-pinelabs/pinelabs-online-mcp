"""Tests for payment link and order MCP tools."""

import json
from unittest.mock import AsyncMock

import pytest

from pkg.pinelabs.client import PineLabsClient, PineLabsAPIError
from pkg.pinelabs.payment_links import register_payment_link_tools
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

def _mock_headers(token="test-token"):
    """Return a mock Authorization header dict."""
    return {"authorization": f"Bearer {token}"}


def _make_mcp_and_register_payment_tools(client):
    """Create a FakeMCP, register tools, return the captured tool functions."""
    mcp = _FakeMCP()
    register_payment_link_tools(mcp, client)
    return mcp.tools


def _make_mcp_and_register_order_tools(client):
    """Create a FakeMCP, register order tools, return the captured tool functions."""
    mcp = _FakeMCP()
    register_order_tools(mcp, client)
    return mcp.tools


# ---------------------------------------------------------------------------
# create_payment_link
# ---------------------------------------------------------------------------

class TestCreatePaymentLink:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.post = AsyncMock(return_value={"payment_link_id": "pl-new", "status": "CREATED"})
        return c

    @pytest.mark.asyncio
    async def test_success_minimal(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_email="a@b.com",
        )
        data = json.loads(result)
        assert data["payment_link_id"] == "pl-new"
        assert data["status"] == "CREATED"
        client.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_success_full(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["create_payment_link"](
            amount_value=100000,
            currency="INR",
            customer_email="test@example.com",
            customer_first_name="John",
            customer_last_name="Doe",
            customer_mobile="9876543210",
            customer_country_code="+91",
            customer_id="cust-123",
            description="Test order",
            expire_by="2026-06-01T10:00Z",
            allowed_payment_methods=["CARD", "UPI"],
            billing_address1="123 St",
            billing_city="Mumbai",
            billing_state="MH",
            billing_country="India",
            billing_pincode="400001",
            billing_full_name="John Doe",
            shipping_address1="456 Ave",
            shipping_city="Delhi",
            shipping_state="DL",
            shipping_country="India",
            shipping_pincode="110001",
            shipping_full_name="John Doe",
        )
        data = json.loads(result)
        assert data["status"] == "CREATED"

    @pytest.mark.asyncio
    async def test_missing_auth(self, client):
        client.post = AsyncMock(
            side_effect=RuntimeError("Client credentials not configured")
        )
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_email="a@b.com",
        )
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_missing_email_and_mobile(self, client):
        """Customer requires at least email or mobile — returns validation error."""
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
        )
        data = json.loads(result)
        assert "error" in data
        assert data["code"] == "VALIDATION_ERROR"
        assert "email" in data["error"].lower() or "mobile" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_invalid_payment_method(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_email="a@b.com",
            allowed_payment_methods=["BITCOIN"],
        )
        data = json.loads(result)
        assert "error" in data
        assert "Invalid payment method" in data["error"]

    @pytest.mark.asyncio
    async def test_api_error(self, client):
        client.post = AsyncMock(
            side_effect=PineLabsAPIError(400, "BAD", "Bad request")
        )
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_email="a@b.com",
        )
        data = json.loads(result)
        assert data["error"] == "Bad request"
        assert data["code"] == "BAD"
        assert data["status_code"] == 400

    @pytest.mark.asyncio
    async def test_unexpected_error(self, client):
        client.post = AsyncMock(side_effect=RuntimeError("connection lost"))
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_email="a@b.com",
        )
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()
        assert "connection lost" not in data["error"]

    @pytest.mark.asyncio
    async def test_with_mobile_only(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_mobile="9876543210",
        )
        data = json.loads(result)
        assert data["status"] == "CREATED"

    @pytest.mark.asyncio
    async def test_invalid_merchant_ref(self, client):
        """merchant_payment_link_reference with unsafe chars triggers validation error."""
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_email="a@b.com",
            merchant_payment_link_reference="ref/with;bad chars",
        )
        data = json.loads(result)
        assert "error" in data
        assert data["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_invalid_expire_by(self, client):
        """An invalid expire_by string triggers validation error."""
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_email="a@b.com",
            expire_by="not-a-date",
        )
        data = json.loads(result)
        assert "error" in data
        assert data["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_with_product_details(self, client):
        """Product code and amount create product_details in the request."""
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_email="a@b.com",
            product_code="redmi_10",
            product_amount=45000,
        )
        data = json.loads(result)
        assert data["status"] == "CREATED"
        # Verify the request payload included product_details
        call_args = client.post.call_args
        payload = call_args[0][1]
        assert "product_details" in payload
        assert payload["product_details"][0]["product_code"] == "redmi_10"

    @pytest.mark.asyncio
    async def test_with_cart_coupon_discount(self, client):
        """cart_coupon_discount_amount should be included in the request."""
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50000,
            customer_email="a@b.com",
            cart_coupon_discount_amount=5000,
        )
        data = json.loads(result)
        assert data["status"] == "CREATED"
        call_args = client.post.call_args
        payload = call_args[0][1]
        assert "cart_coupon_discount_amount" in payload

    @pytest.mark.asyncio
    async def test_pydantic_validation_error(self, client):
        """Invalid amount value should trigger pydantic validation error."""
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["create_payment_link"](
            amount_value=-100,
            customer_email="a@b.com",
        )
        data = json.loads(result)
        assert "error" in data
        assert data["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_amount_validation_error(self, client):
        """Amount below minimum (100) is caught by the except block in Step 5."""
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["create_payment_link"](
            amount_value=50,
            customer_email="a@b.com",
        )
        data = json.loads(result)
        assert "error" in data
        assert data["code"] == "VALIDATION_ERROR"
        assert data["status_code"] == 422


# ---------------------------------------------------------------------------
# get_payment_link_by_id
# ---------------------------------------------------------------------------

class TestGetPaymentLinkById:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.get = AsyncMock(return_value={"payment_link_id": "pl-123", "status": "CREATED"})
        return c

    @pytest.mark.asyncio
    async def test_success(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["get_payment_link_by_id"](payment_link_id="pl-123")
        data = json.loads(result)
        assert data["payment_link_id"] == "pl-123"

    @pytest.mark.asyncio
    async def test_missing_auth(self, client):
        client.get = AsyncMock(
            side_effect=RuntimeError("Client credentials not configured")
        )
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["get_payment_link_by_id"](payment_link_id="pl-123")
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_id_too_long(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["get_payment_link_by_id"](payment_link_id="x" * 51)
        data = json.loads(result)
        assert "error" in data
        assert "at most 50 characters" in data["error"]

    @pytest.mark.asyncio
    async def test_empty_id(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["get_payment_link_by_id"](payment_link_id="")
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_api_error(self, client):
        client.get = AsyncMock(
            side_effect=PineLabsAPIError(404, "NOT_FOUND", "Not found")
        )
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["get_payment_link_by_id"](payment_link_id="pl-bad")
        data = json.loads(result)
        assert data["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_unexpected_error(self, client):
        client.get = AsyncMock(side_effect=RuntimeError("timeout"))
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["get_payment_link_by_id"](payment_link_id="pl-123")
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()
        assert "timeout" not in data["error"]


# ---------------------------------------------------------------------------
# get_payment_link_by_merchant_reference
# ---------------------------------------------------------------------------

class TestGetPaymentLinkByMerchantRef:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.get = AsyncMock(return_value={"merchant_ref": "ref-001", "status": "CREATED"})
        return c

    @pytest.mark.asyncio
    async def test_success(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["get_payment_link_by_merchant_reference"](
            merchant_payment_link_reference="ref-001"
        )
        data = json.loads(result)
        assert data["merchant_ref"] == "ref-001"

    @pytest.mark.asyncio
    async def test_missing_auth(self, client):
        client.get = AsyncMock(
            side_effect=RuntimeError("Client credentials not configured")
        )
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["get_payment_link_by_merchant_reference"](
            merchant_payment_link_reference="ref-001"
        )
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_ref_too_long(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["get_payment_link_by_merchant_reference"](
            merchant_payment_link_reference="x" * 51
        )
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_empty_ref(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["get_payment_link_by_merchant_reference"](
            merchant_payment_link_reference=""
        )
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_api_error(self, client):
        client.get = AsyncMock(
            side_effect=PineLabsAPIError(404, "NOT_FOUND", "Not found")
        )
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["get_payment_link_by_merchant_reference"](
            merchant_payment_link_reference="ref-bad"
        )
        data = json.loads(result)
        assert data["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_unexpected_error(self, client):
        client.get = AsyncMock(side_effect=RuntimeError("boom"))
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["get_payment_link_by_merchant_reference"](
            merchant_payment_link_reference="ref-001"
        )
        data = json.loads(result)
        assert "error" in data


# ---------------------------------------------------------------------------
# cancel_payment_link
# ---------------------------------------------------------------------------

class TestCancelPaymentLink:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.put = AsyncMock(return_value={"payment_link_id": "pl-123", "status": "CANCELLED"})
        return c

    @pytest.mark.asyncio
    async def test_success(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["cancel_payment_link"](payment_link_id="pl-123")
        data = json.loads(result)
        assert data["status"] == "CANCELLED"

    @pytest.mark.asyncio
    async def test_missing_auth(self, client):
        client.put = AsyncMock(
            side_effect=RuntimeError("Client credentials not configured")
        )
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["cancel_payment_link"](payment_link_id="pl-123")
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_id_too_long(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["cancel_payment_link"](payment_link_id="x" * 51)
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_empty_id(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["cancel_payment_link"](payment_link_id="")
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_api_error(self, client):
        client.put = AsyncMock(
            side_effect=PineLabsAPIError(409, "CONFLICT", "Cannot cancel")
        )
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["cancel_payment_link"](payment_link_id="pl-123")
        data = json.loads(result)
        assert data["code"] == "CONFLICT"

    @pytest.mark.asyncio
    async def test_unexpected_error(self, client):
        client.put = AsyncMock(side_effect=RuntimeError("connection refused"))
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["cancel_payment_link"](payment_link_id="pl-123")
        data = json.loads(result)
        assert "error" in data


# ---------------------------------------------------------------------------
# resend_payment_link_notification
# ---------------------------------------------------------------------------

class TestResendPaymentLinkNotification:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.patch = AsyncMock(return_value={"payment_link_id": "pl-123", "status": "CREATED"})
        return c

    @pytest.mark.asyncio
    async def test_success(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["resend_payment_link_notification"](payment_link_id="pl-123")
        data = json.loads(result)
        assert data["status"] == "CREATED"

    @pytest.mark.asyncio
    async def test_missing_auth(self, client):
        client.patch = AsyncMock(
            side_effect=RuntimeError("Client credentials not configured")
        )
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["resend_payment_link_notification"](payment_link_id="pl-123")
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_id_too_long(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["resend_payment_link_notification"](payment_link_id="x" * 51)
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_empty_id(self, client):
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["resend_payment_link_notification"](payment_link_id="")
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_api_error(self, client):
        client.patch = AsyncMock(
            side_effect=PineLabsAPIError(400, "EXPIRED", "Link expired")
        )
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["resend_payment_link_notification"](payment_link_id="pl-123")
        data = json.loads(result)
        assert data["code"] == "EXPIRED"

    @pytest.mark.asyncio
    async def test_unexpected_error(self, client):
        client.patch = AsyncMock(side_effect=RuntimeError("network down"))
        tools = _make_mcp_and_register_payment_tools(client)
        result = await tools["resend_payment_link_notification"](payment_link_id="pl-123")
        data = json.loads(result)
        assert "error" in data


# ---------------------------------------------------------------------------
# get_order_by_order_id
# ---------------------------------------------------------------------------

class TestGetOrderByOrderId:
    @pytest.fixture
    def client(self):
        c = PineLabsClient(base_url="https://fake.test/api", token_url="https://fake.test/api/auth/v1/token", client_id="test-id", client_secret="test-secret")
        c.get = AsyncMock(return_value={"order_id": "ord-1", "status": "PROCESSED"})
        return c

    @pytest.mark.asyncio
    async def test_success(self, client):
        tools = _make_mcp_and_register_order_tools(client)
        result = await tools["get_order_by_order_id"](order_id="ord-1")
        data = json.loads(result)
        assert data["order_id"] == "ord-1"
        assert data["status"] == "PROCESSED"

    @pytest.mark.asyncio
    async def test_missing_auth(self, client):
        client.get = AsyncMock(
            side_effect=RuntimeError("Client credentials not configured")
        )
        tools = _make_mcp_and_register_order_tools(client)
        result = await tools["get_order_by_order_id"](order_id="ord-1")
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_api_error(self, client):
        client.get = AsyncMock(
            side_effect=PineLabsAPIError(404, "NOT_FOUND", "Order not found")
        )
        tools = _make_mcp_and_register_order_tools(client)
        result = await tools["get_order_by_order_id"](order_id="ord-bad")
        data = json.loads(result)
        assert data["code"] == "NOT_FOUND"
        assert data["status_code"] == 404

    @pytest.mark.asyncio
    async def test_unexpected_error(self, client):
        client.get = AsyncMock(side_effect=RuntimeError("dns failure"))
        tools = _make_mcp_and_register_order_tools(client)
        result = await tools["get_order_by_order_id"](order_id="ord-1")
        data = json.loads(result)
        assert "error" in data
        assert "internal error" in data["error"].lower()
        assert "dns failure" not in data["error"]

    @pytest.mark.asyncio
    async def test_invalid_order_id(self, client):
        """Order ID with unsafe characters triggers validation error."""
        tools = _make_mcp_and_register_order_tools(client)
        result = await tools["get_order_by_order_id"](order_id="ord/bad;id")
        data = json.loads(result)
        assert "error" in data
        assert data["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_empty_order_id(self, client):
        """Empty order ID triggers validation error."""
        tools = _make_mcp_and_register_order_tools(client)
        result = await tools["get_order_by_order_id"](order_id="")
        data = json.loads(result)
        assert "error" in data
