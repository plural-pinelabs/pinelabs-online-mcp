"""Tests for tools/upi_intent_qr.py."""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from mcp.types import ImageContent, TextContent
from pydantic import ValidationError

from pkg.pinelabs.client import PineLabsAPIError
from pkg.pinelabs.upi_intent_qr import (
    _build_purchase_details,
    _is_allowed_image_url,
    _sanitize_validation_error,
    register_upi_intent_qr_tools,
)


@pytest.fixture()
def tool(fake_mcp, mock_client):
    register_upi_intent_qr_tools(fake_mcp, mock_client)
    return fake_mcp.tools["create_upi_intent_payment_with_qr"]


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestSanitizeValidationError:
    def test_formats_validation_error(self) -> None:
        try:
            from pkg.pinelabs.models.payment_links import Amount
            Amount(value=-1, currency="INR")
        except ValidationError as e:
            result = _sanitize_validation_error(e)
            parsed = json.loads(result)
            assert isinstance(parsed, list)

    def test_formats_non_validation_error(self) -> None:
        result = _sanitize_validation_error(ValueError("some error"))
        assert result == "some error"


class TestIsAllowedImageUrl:
    def test_allows_amazonaws_domain(self) -> None:
        assert _is_allowed_image_url("https://s3.ap-south-1.amazonaws.com/bucket/qr.png") is True

    def test_allows_pinepg_subdomain(self) -> None:
        assert _is_allowed_image_url("https://assets.pinepg.in/image.png") is True

    def test_allows_pluralpay_domain(self) -> None:
        assert _is_allowed_image_url("https://cdn.pluralpay.in/qr.png") is True

    def test_blocks_arbitrary_domain(self) -> None:
        assert _is_allowed_image_url("https://evil.com/steal.png") is False

    def test_blocks_http_scheme(self) -> None:
        assert _is_allowed_image_url("http://s3.ap-south-1.amazonaws.com/qr.png") is False

    def test_blocks_ftp_scheme(self) -> None:
        assert _is_allowed_image_url("ftp://s3.ap-south-1.amazonaws.com/qr.png") is False

    def test_blocks_empty_url(self) -> None:
        assert _is_allowed_image_url("") is False

    def test_blocks_malformed_url(self) -> None:
        assert _is_allowed_image_url("not-a-url") is False


class TestBuildPurchaseDetails:
    def test_returns_none_when_all_none(self) -> None:
        result = _build_purchase_details(
            customer_email=None, customer_first_name=None, customer_last_name=None,
            customer_mobile=None, customer_country_code=None, customer_id=None,
            billing_address1=None, billing_address2=None, billing_address3=None,
            billing_city=None, billing_state=None, billing_country=None,
            billing_pincode=None, billing_full_name=None,
            shipping_address1=None, shipping_address2=None, shipping_address3=None,
            shipping_city=None, shipping_state=None, shipping_country=None,
            shipping_pincode=None, shipping_full_name=None,
            merchant_metadata=None,
        )
        assert result is None

    def test_builds_with_customer_email(self) -> None:
        result = _build_purchase_details(
            customer_email="test@example.com", customer_first_name="John",
            customer_last_name=None, customer_mobile=None,
            customer_country_code=None, customer_id=None,
            billing_address1=None, billing_address2=None, billing_address3=None,
            billing_city=None, billing_state=None, billing_country=None,
            billing_pincode=None, billing_full_name=None,
            shipping_address1=None, shipping_address2=None, shipping_address3=None,
            shipping_city=None, shipping_state=None, shipping_country=None,
            shipping_pincode=None, shipping_full_name=None,
            merchant_metadata=None,
        )
        assert result is not None
        assert result.customer is not None
        assert result.customer.email_id == "test@example.com"

    def test_builds_with_shipping_address(self) -> None:
        result = _build_purchase_details(
            customer_email=None, customer_first_name=None, customer_last_name=None,
            customer_mobile=None, customer_country_code=None, customer_id=None,
            billing_address1=None, billing_address2=None, billing_address3=None,
            billing_city=None, billing_state=None, billing_country=None,
            billing_pincode=None, billing_full_name=None,
            shipping_address1="123 Ship St", shipping_address2=None,
            shipping_address3=None, shipping_city="Mumbai",
            shipping_state=None, shipping_country=None,
            shipping_pincode=None, shipping_full_name=None,
            merchant_metadata=None,
        )
        assert result is not None
        assert result.customer is not None
        assert result.customer.shipping_address is not None
        assert result.customer.shipping_address.address1 == "123 Ship St"

    def test_builds_with_merchant_metadata(self) -> None:
        result = _build_purchase_details(
            customer_email=None, customer_first_name=None, customer_last_name=None,
            customer_mobile=None, customer_country_code=None, customer_id=None,
            billing_address1=None, billing_address2=None, billing_address3=None,
            billing_city=None, billing_state=None, billing_country=None,
            billing_pincode=None, billing_full_name=None,
            shipping_address1=None, shipping_address2=None, shipping_address3=None,
            shipping_city=None, shipping_state=None, shipping_country=None,
            shipping_pincode=None, shipping_full_name=None,
            merchant_metadata={"key1": "val1"},
        )
        assert result is not None
        assert result.merchant_metadata == {"key1": "val1"}


# ---------------------------------------------------------------------------
# Tool happy-path tests
# ---------------------------------------------------------------------------


class TestCreateUpiIntentPaymentWithQrHappyPath:
    @pytest.mark.asyncio
    async def test_creates_order_then_qr_payment(self, tool, mock_client) -> None:
        mock_client.post = AsyncMock(side_effect=[
            {
                "data": {
                    "order_id": "v1-order-123",
                    "status": "CREATED",
                    "order_amount": {"value": 1100, "currency": "INR"},
                }
            },
            {
                "data": {
                    "order_id": "v1-order-123",
                    "status": "PENDING",
                    "challenge_url": "upi://pay?...",
                    "image_url": "https://s3.ap-south-1.amazonaws.com/bucket/qr.png",
                }
            },
        ])

        raw = await tool(
            merchant_order_reference="order-qr-001",
            merchant_payment_reference="payment-qr-001",
            amount_value=1100,
        )
        # Success path returns a list of content items; first item is the JSON TextContent
        assert isinstance(raw, list)
        assert isinstance(raw[0], TextContent)
        result = json.loads(raw[0].text)

        assert result["order"]["data"]["order_id"] == "v1-order-123"
        assert result["payment"]["data"]["image_url"] == "https://s3.ap-south-1.amazonaws.com/bucket/qr.png"
        assert mock_client.post.await_count == 2

        first_call = mock_client.post.await_args_list[0]
        assert first_call.args[0] == "/pay/v1/orders"
        assert first_call.args[1]["merchant_order_reference"] == "order-qr-001"
        assert first_call.args[1]["allowed_payment_methods"] == ["UPI"]

        second_call = mock_client.post.await_args_list[1]
        assert second_call.args[0] == "/pay/v1/orders/v1-order-123/payments"
        payment = second_call.args[1]["payments"][0]
        assert payment["merchant_payment_reference"] == "payment-qr-001"
        assert payment["payment_method"] == "UPI"
        assert payment["payment_amount"]["value"] == 1100
        assert payment["payment_option"]["upi_details"]["txn_mode"] == "INTENT"
        assert payment["payment_option"]["upi_details"]["upi_qr"] is True

    @pytest.mark.asyncio
    async def test_auto_generates_payment_reference(self, tool, mock_client) -> None:
        mock_client.post = AsyncMock(side_effect=[
            {"data": {"order_id": "v1-order-456", "order_amount": {"value": 2000, "currency": "INR"}}},
            {"data": {"order_id": "v1-order-456", "status": "PENDING"}},
        ])

        raw = await tool(
            merchant_order_reference="order-qr-002",
            amount_value=2000,
        )
        assert isinstance(raw, list)
        result = json.loads(raw[0].text)

        assert result["payment"]["data"]["order_id"] == "v1-order-456"
        payment = mock_client.post.await_args_list[1].args[1]["payments"][0]
        assert isinstance(payment["merchant_payment_reference"], str)
        assert payment["merchant_payment_reference"]

    @pytest.mark.asyncio
    async def test_inline_qr_image_fetched_on_success(self, tool, mock_client) -> None:
        """When payment response has image_url, the image is fetched and returned as ImageContent."""
        mock_client.post = AsyncMock(side_effect=[
            {"data": {"order_id": "v1-order-img", "order_amount": {"value": 500, "currency": "INR"}}},
            {"data": {"order_id": "v1-order-img", "status": "PENDING", "image_url": "https://s3.ap-south-1.amazonaws.com/bucket/qr.png"}},
        ])
        fake_png = b"\x89PNG\r\n\x1a\nfakedata"
        mock_request = httpx.Request("GET", "https://s3.ap-south-1.amazonaws.com/bucket/qr.png")
        mock_response = httpx.Response(200, content=fake_png, headers={"content-type": "image/png"}, request=mock_request)

        with patch("pkg.pinelabs.upi_intent_qr.httpx.AsyncClient") as mock_http_cls:
            mock_http = AsyncMock()
            mock_http.get.return_value = mock_response
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=False)
            mock_http_cls.return_value = mock_http

            raw = await tool(
                merchant_order_reference="order-qr-img",
                amount_value=500,
            )

        assert isinstance(raw, list)
        assert len(raw) == 2
        assert isinstance(raw[0], TextContent)
        assert isinstance(raw[1], ImageContent)
        assert raw[1].mimeType == "image/png"
        import base64
        assert base64.b64decode(raw[1].data) == fake_png

    @pytest.mark.asyncio
    async def test_image_fetch_blocked_for_untrusted_domain(self, tool, mock_client) -> None:
        """If image_url points to an untrusted domain, the image should NOT be fetched (SSRF protection)."""
        mock_client.post = AsyncMock(side_effect=[
            {"data": {"order_id": "v1-order-ssrf", "order_amount": {"value": 600, "currency": "INR"}}},
            {"data": {"order_id": "v1-order-ssrf", "status": "PENDING", "image_url": "https://evil.com/steal.png"}},
        ])

        raw = await tool(
            merchant_order_reference="order-qr-ssrf",
            amount_value=600,
        )

        assert isinstance(raw, list)
        assert len(raw) == 1  # Only text, no image
        assert isinstance(raw[0], TextContent)

    @pytest.mark.asyncio
    async def test_image_fetch_failure_still_returns_text(self, tool, mock_client) -> None:
        """If image fetch fails, the tool should still return the text content without error."""
        mock_client.post = AsyncMock(side_effect=[
            {"data": {"order_id": "v1-order-imgfail", "order_amount": {"value": 600, "currency": "INR"}}},
            {"data": {"order_id": "v1-order-imgfail", "status": "PENDING", "image_url": "https://s3.ap-south-1.amazonaws.com/bucket/qr.png"}},
        ])

        with patch("pkg.pinelabs.upi_intent_qr.httpx.AsyncClient") as mock_http_cls:
            mock_http = AsyncMock()
            mock_http.get.side_effect = httpx.ConnectError("network error")
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=False)
            mock_http_cls.return_value = mock_http

            raw = await tool(
                merchant_order_reference="order-qr-imgfail",
                amount_value=600,
            )

        assert isinstance(raw, list)
        assert len(raw) == 1
        assert isinstance(raw[0], TextContent)
        result = json.loads(raw[0].text)
        assert result["payment"]["data"]["order_id"] == "v1-order-imgfail"

    @pytest.mark.asyncio
    async def test_no_image_url_in_response(self, tool, mock_client) -> None:
        """When payment response has no image_url, only TextContent is returned."""
        mock_client.post = AsyncMock(side_effect=[
            {"data": {"order_id": "v1-order-noimg", "order_amount": {"value": 700, "currency": "INR"}}},
            {"data": {"order_id": "v1-order-noimg", "status": "PENDING"}},
        ])

        raw = await tool(
            merchant_order_reference="order-qr-noimg",
            amount_value=700,
        )

        assert isinstance(raw, list)
        assert len(raw) == 1
        assert isinstance(raw[0], TextContent)

    @pytest.mark.asyncio
    async def test_with_purchase_details(self, tool, mock_client) -> None:
        """Coverage for _build_purchase_details with customer, billing, shipping details."""
        mock_client.post = AsyncMock(side_effect=[
            {"data": {"order_id": "v1-order-pd", "order_amount": {"value": 1500, "currency": "INR"}}},
            {"data": {"order_id": "v1-order-pd", "status": "PENDING"}},
        ])

        raw = await tool(
            merchant_order_reference="order-qr-pd",
            amount_value=1500,
            customer_email="user@example.com",
            customer_first_name="John",
            customer_last_name="Doe",
            billing_address1="123 Bill St",
            billing_city="Mumbai",
            shipping_address1="456 Ship Rd",
            shipping_city="Delhi",
            merchant_metadata={"ref": "abc"},
        )

        assert isinstance(raw, list)
        order_payload = mock_client.post.await_args_list[0].args[1]
        pd = order_payload["purchase_details"]
        assert pd["customer"]["email_id"] == "user@example.com"
        assert pd["customer"]["billing_address"]["address1"] == "123 Bill St"
        assert pd["customer"]["shipping_address"]["address1"] == "456 Ship Rd"
        assert pd["merchant_metadata"]["ref"] == "abc"

    @pytest.mark.asyncio
    async def test_with_upi_in_allowed_methods(self, tool, mock_client) -> None:
        """When UPI is explicitly included in allowed_payment_methods, it should work."""
        mock_client.post = AsyncMock(side_effect=[
            {"data": {"order_id": "v1-order-upi", "order_amount": {"value": 800, "currency": "INR"}}},
            {"data": {"order_id": "v1-order-upi", "status": "PENDING"}},
        ])

        raw = await tool(
            merchant_order_reference="order-qr-upi-ok",
            amount_value=800,
            allowed_payment_methods=["UPI"],
        )

        assert isinstance(raw, list)
        order_payload = mock_client.post.await_args_list[0].args[1]
        assert order_payload["allowed_payment_methods"] == ["UPI"]


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestCreateUpiIntentPaymentWithQrValidation:
    @pytest.mark.asyncio
    async def test_rejects_payment_methods_without_upi(self, tool) -> None:
        result = json.loads(await tool(
            merchant_order_reference="order-qr-invalid",
            amount_value=1100,
            allowed_payment_methods=["CARD"],
        ))

        assert result["code"] == "VALIDATION_ERROR"
        assert "UPI" in result["error"]

    @pytest.mark.asyncio
    async def test_rejects_invalid_payment_reference(self, tool) -> None:
        result = json.loads(await tool(
            merchant_order_reference="order-qr-invalid-ref",
            merchant_payment_reference="bad/ref",
            amount_value=1100,
        ))

        assert result["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_rejects_invalid_order_reference(self, tool) -> None:
        result = json.loads(await tool(
            merchant_order_reference="bad/order/ref!!",
            amount_value=1100,
        ))

        assert result["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_rejects_completely_invalid_payment_method(self, tool) -> None:
        """Covers the ValueError branch for invalid enum values."""
        result = json.loads(await tool(
            merchant_order_reference="order-qr-badmethod",
            amount_value=1100,
            allowed_payment_methods=["INVALID_METHOD"],
        ))

        assert result["code"] == "VALIDATION_ERROR"
        assert "Allowed values" in result["error"]

    @pytest.mark.asyncio
    async def test_rejects_negative_amount(self, tool, mock_client) -> None:
        """Covers order_request model validation error branch."""
        mock_client.post = AsyncMock()
        result = json.loads(await tool(
            merchant_order_reference="order-qr-neg",
            amount_value=-100,
        ))

        assert result["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


class TestCreateUpiIntentPaymentWithQrErrors:
    @pytest.mark.asyncio
    async def test_order_api_error(self, tool, mock_client) -> None:
        mock_client.post = AsyncMock(
            side_effect=PineLabsAPIError(422, "DUPLICATE_REQUEST", "Duplicate Merchant Reference ID received")
        )

        result = json.loads(await tool(
            merchant_order_reference="order-qr-dup",
            amount_value=1100,
        ))

        assert result["code"] == "DUPLICATE_REQUEST"
        assert result["status_code"] == 422

    @pytest.mark.asyncio
    async def test_payment_api_error_includes_order_id(self, tool, mock_client) -> None:
        mock_client.post = AsyncMock(side_effect=[
            {"data": {"order_id": "v1-order-789", "order_amount": {"value": 1100, "currency": "INR"}}},
            PineLabsAPIError(400, "INVALID_REQUEST", "Payment request invalid"),
        ])

        result = json.loads(await tool(
            merchant_order_reference="order-qr-payment-error",
            amount_value=1100,
        ))

        assert result["code"] == "INVALID_REQUEST"
        assert result["status_code"] == 400
        assert result["details"]["order_id"] == "v1-order-789"

    @pytest.mark.asyncio
    async def test_missing_order_id_in_order_response(self, tool, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={"data": {"status": "CREATED"}})

        result = json.loads(await tool(
            merchant_order_reference="order-qr-no-id",
            amount_value=1100,
        ))

        assert result["code"] == "UPSTREAM_INVALID_RESPONSE"
        assert result["status_code"] == 502

    @pytest.mark.asyncio
    async def test_unexpected_error_during_order_creation(self, tool, mock_client) -> None:
        """Covers the generic Exception handler for order creation."""
        mock_client.post = AsyncMock(side_effect=RuntimeError("connection reset"))

        result = json.loads(await tool(
            merchant_order_reference="order-qr-unexpected",
            amount_value=1100,
        ))

        assert result["code"] == "INTERNAL_ERROR"

    @pytest.mark.asyncio
    async def test_unexpected_error_during_payment_creation(self, tool, mock_client) -> None:
        """Covers the generic Exception handler for payment creation."""
        mock_client.post = AsyncMock(side_effect=[
            {"data": {"order_id": "v1-order-exc", "order_amount": {"value": 900, "currency": "INR"}}},
            RuntimeError("timeout"),
        ])

        result = json.loads(await tool(
            merchant_order_reference="order-qr-pay-unexpected",
            amount_value=900,
        ))

        assert result["code"] == "INTERNAL_ERROR"

