"""Tests for tools/checkout_orders.py — create_order tool."""

import json
from unittest.mock import AsyncMock

import pytest

from pkg.pinelabs.client import PineLabsAPIError
from pkg.pinelabs.checkout_orders import register_checkout_order_tools


@pytest.fixture()
def tool(fake_mcp, mock_client):
    register_checkout_order_tools(fake_mcp, mock_client)
    return fake_mcp.tools["create_order"]


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestCreateOrderHappyPath:
    @pytest.mark.asyncio
    async def test_minimal_required_fields(self, tool, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={
            "token": "tok-abc",
            "order_id": "v1-123-aa-xyz",
            "redirect_url": "https://checkout.example/tok-abc",
            "response_code": 200,
            "response_message": "Order Creation Successful.",
        })

        result = json.loads(await tool(
            merchant_order_reference="order-001",
            amount_value=1100,
        ))
        assert result["order_id"] == "v1-123-aa-xyz"
        assert result["redirect_url"] == "https://checkout.example/tok-abc"
        mock_client.post.assert_awaited_once()

        # Verify the API path used
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/checkout/v1/orders"

    @pytest.mark.asyncio
    async def test_full_params(self, tool, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={
            "token": "tok-full",
            "order_id": "v1-456-aa-full",
            "redirect_url": "https://checkout.example/tok-full",
            "response_code": 200,
            "response_message": "Order Creation Successful.",
        })

        result = json.loads(await tool(
            merchant_order_reference="order-full",
            amount_value=5000,
            currency="INR",
            integration_mode="IFRAME",
            pre_auth=False,
            allowed_payment_methods=["CARD", "UPI", "NETBANKING"],
            notes="Test order",
            callback_url="https://example.com/success",
            failure_callback_url="https://example.com/failure",
            customer_email="test@example.com",
            customer_first_name="Kevin",
            customer_last_name="Bob",
            customer_mobile="9876543210",
            customer_country_code="91",
            customer_id="123456",
            billing_address1="10 Downing Street",
            billing_city="Westminster",
            billing_country="UK",
            billing_pincode="51524036",
            shipping_address1="10 Downing Street",
            shipping_city="Westminster",
            shipping_country="UK",
            shipping_pincode="51524036",
            merchant_metadata={"key1": "DD"},
        ))
        assert result["order_id"] == "v1-456-aa-full"

        # Verify request payload structure
        payload = mock_client.post.call_args[0][1]
        assert payload["merchant_order_reference"] == "order-full"
        assert payload["order_amount"]["value"] == 5000
        assert payload["integration_mode"] == "IFRAME"
        assert payload["purchase_details"]["customer"]["email_id"] == "test@example.com"
        assert payload["purchase_details"]["merchant_metadata"]["key1"] == "DD"

    @pytest.mark.asyncio
    async def test_with_product_code(self, tool, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={
            "order_id": "v1-emi-order",
            "response_code": 200,
        })

        result = json.loads(await tool(
            merchant_order_reference="emi-order",
            amount_value=120000,
            product_code="redm_1",
            product_amount=120000,
        ))
        assert result["order_id"] == "v1-emi-order"

        payload = mock_client.post.call_args[0][1]
        assert payload["product"][0]["product_code"] == "redm_1"
        assert payload["product"][0]["product_amount"]["value"] == 120000


# ---------------------------------------------------------------------------
# API error
# ---------------------------------------------------------------------------

class TestCreateOrderAPIError:
    @pytest.mark.asyncio
    async def test_bad_request(self, tool, mock_client) -> None:
        mock_client.post = AsyncMock(
            side_effect=PineLabsAPIError(400, "INVALID_REQUEST", "Amount must be an Integer")
        )

        result = json.loads(await tool(
            merchant_order_reference="order-bad",
            amount_value=1100,
        ))
        assert result["code"] == "INVALID_REQUEST"
        assert result["status_code"] == 400

    @pytest.mark.asyncio
    async def test_unauthorized(self, tool, mock_client) -> None:
        mock_client.post = AsyncMock(
            side_effect=PineLabsAPIError(401, "UNAUTHORIZED", "Unauthorized")
        )

        result = json.loads(await tool(
            merchant_order_reference="order-unauth",
            amount_value=1100,
        ))
        assert result["code"] == "UNAUTHORIZED"
        assert result["status_code"] == 401

    @pytest.mark.asyncio
    async def test_duplicate_request(self, tool, mock_client) -> None:
        mock_client.post = AsyncMock(
            side_effect=PineLabsAPIError(422, "DUPLICATE_REQUEST", "Duplicate Merchant Reference ID received")
        )

        result = json.loads(await tool(
            merchant_order_reference="order-dup",
            amount_value=1100,
        ))
        assert result["code"] == "DUPLICATE_REQUEST"
        assert result["status_code"] == 422


# ---------------------------------------------------------------------------
# Unexpected error
# ---------------------------------------------------------------------------

class TestCreateOrderUnexpectedError:
    @pytest.mark.asyncio
    async def test_runtime_error(self, tool, mock_client) -> None:
        mock_client.post = AsyncMock(side_effect=RuntimeError("crash"))

        result = json.loads(await tool(
            merchant_order_reference="order-crash",
            amount_value=1100,
        ))
        assert result["code"] == "INTERNAL_ERROR"
        assert result["status_code"] == 500
        assert "internal error" in result["error"].lower()


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

class TestCreateOrderValidation:
    @pytest.mark.asyncio
    async def test_empty_merchant_reference(self, tool) -> None:
        result = json.loads(await tool(
            merchant_order_reference="",
            amount_value=1100,
        ))
        assert result["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_merchant_reference_too_long(self, tool) -> None:
        result = json.loads(await tool(
            merchant_order_reference="x" * 51,
            amount_value=1100,
        ))
        assert result["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_merchant_reference_unsafe_chars(self, tool) -> None:
        result = json.loads(await tool(
            merchant_order_reference="order/../hack",
            amount_value=1100,
        ))
        assert result["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_amount_too_low(self, tool) -> None:
        result = json.loads(await tool(
            merchant_order_reference="order-low",
            amount_value=50,
        ))
        assert result["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_amount_too_high(self, tool) -> None:
        result = json.loads(await tool(
            merchant_order_reference="order-high",
            amount_value=200_000_000,
        ))
        assert result["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_invalid_payment_method(self, tool) -> None:
        result = json.loads(await tool(
            merchant_order_reference="order-pm",
            amount_value=1100,
            allowed_payment_methods=["BITCOIN"],
        ))
        assert result["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_invalid_integration_mode(self, tool) -> None:
        result = json.loads(await tool(
            merchant_order_reference="order-mode",
            amount_value=1100,
            integration_mode="POPUP",
        ))
        assert result["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_valid_payment_methods_case_insensitive(self, tool, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={"order_id": "v1-ok", "response_code": 200})
        result = json.loads(await tool(
            merchant_order_reference="order-case",
            amount_value=1100,
            allowed_payment_methods=["card", "upi"],
        ))
        assert "order_id" in result

    @pytest.mark.asyncio
    async def test_valid_integration_mode_case_insensitive(self, tool, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={"order_id": "v1-ok", "response_code": 200})
        result = json.loads(await tool(
            merchant_order_reference="order-iframe",
            amount_value=1100,
            integration_mode="iframe",
        ))
        assert "order_id" in result

    @pytest.mark.asyncio
    async def test_with_tpv_bank_details_rejected(self, tool, mock_client) -> None:
        """Bank account details are no longer accepted as tool parameters (security: PII/DPDP compliance).
        TPV orders must use a separate secure server-side flow."""
        # Verify that bank_account_number, bank_ifsc_code, bank_name are NOT accepted
        import inspect
        sig = inspect.signature(tool)
        params = set(sig.parameters.keys())
        assert "bank_account_number" not in params
        assert "bank_ifsc_code" not in params
        assert "bank_name" not in params
