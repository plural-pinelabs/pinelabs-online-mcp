"""Tests for tools/payment_links.py — all five payment link tools."""

import json
from unittest.mock import AsyncMock

import pytest

from pkg.pinelabs.client import PineLabsAPIError
from pkg.pinelabs.payment_links import register_payment_link_tools


@pytest.fixture()
def tools(fake_mcp, mock_client):
    register_payment_link_tools(fake_mcp, mock_client)
    return fake_mcp.tools


# ===================================================================
# create_payment_link
# ===================================================================

class TestCreatePaymentLink:
    @pytest.mark.asyncio
    async def test_happy_path(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={"payment_link_id": "pl-123", "url": "https://pay.example"})
        result = json.loads(await tools["create_payment_link"](amount_value=5000, customer_email="a@b.com"))
        assert result["payment_link_id"] == "pl-123"

    @pytest.mark.asyncio
    async def test_api_error(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(
            side_effect=PineLabsAPIError(400, "UPSTREAM_BAD_REQUEST", "Bad request")
        )
        result = json.loads(await tools["create_payment_link"](amount_value=5000, customer_email="a@b.com"))
        assert result["code"] == "UPSTREAM_BAD_REQUEST"

    @pytest.mark.asyncio
    async def test_unexpected_error(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(side_effect=RuntimeError("boom"))
        result = json.loads(await tools["create_payment_link"](amount_value=5000, customer_email="a@b.com"))
        assert result["code"] == "INTERNAL_ERROR"

    @pytest.mark.asyncio
    async def test_invalid_payment_method(self, tools) -> None:
        result = json.loads(await tools["create_payment_link"](
            amount_value=5000, customer_email="a@b.com", allowed_payment_methods=["BITCOIN"],
        ))
        assert result["code"] == "VALIDATION_ERROR"


# ===================================================================
# get_payment_link_by_id
# ===================================================================

class TestGetPaymentLinkById:
    @pytest.mark.asyncio
    async def test_happy_path(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(return_value={"payment_link_id": "pl-123", "status": "CREATED"})
        result = json.loads(await tools["get_payment_link_by_id"](payment_link_id="pl-123"))
        assert result["status"] == "CREATED"

    @pytest.mark.asyncio
    async def test_api_error(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(
            side_effect=PineLabsAPIError(404, "UPSTREAM_NOT_FOUND", "Not found")
        )
        result = json.loads(await tools["get_payment_link_by_id"](payment_link_id="pl-bad"))
        assert result["code"] == "UPSTREAM_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_unexpected_error(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(side_effect=RuntimeError("crash"))
        result = json.loads(await tools["get_payment_link_by_id"](payment_link_id="pl-123"))
        assert result["code"] == "INTERNAL_ERROR"

    @pytest.mark.asyncio
    async def test_id_too_long(self, tools) -> None:
        result = json.loads(await tools["get_payment_link_by_id"](payment_link_id="x" * 51))
        assert result["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_empty_id(self, tools) -> None:
        result = json.loads(await tools["get_payment_link_by_id"](payment_link_id=""))
        assert result["code"] == "VALIDATION_ERROR"


# ===================================================================
# get_payment_link_by_merchant_reference
# ===================================================================

class TestGetPaymentLinkByMerchantRef:
    @pytest.mark.asyncio
    async def test_happy_path(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(return_value={"status": "CREATED"})
        result = json.loads(await tools["get_payment_link_by_merchant_reference"](
            merchant_payment_link_reference="ref-abc"
        ))
        assert result["status"] == "CREATED"

    @pytest.mark.asyncio
    async def test_ref_too_long(self, tools) -> None:
        result = json.loads(await tools["get_payment_link_by_merchant_reference"](
            merchant_payment_link_reference="x" * 51
        ))
        assert result["code"] == "VALIDATION_ERROR"


# ===================================================================
# cancel_payment_link
# ===================================================================

class TestCancelPaymentLink:
    @pytest.mark.asyncio
    async def test_happy_path(self, tools, mock_client) -> None:
        mock_client.put = AsyncMock(return_value={"status": "CANCELLED"})
        result = json.loads(await tools["cancel_payment_link"](payment_link_id="pl-123"))
        assert result["status"] == "CANCELLED"

    @pytest.mark.asyncio
    async def test_api_error(self, tools, mock_client) -> None:
        mock_client.put = AsyncMock(
            side_effect=PineLabsAPIError(409, "UPSTREAM_CONFLICT", "Already cancelled")
        )
        result = json.loads(await tools["cancel_payment_link"](payment_link_id="pl-123"))
        assert result["code"] == "UPSTREAM_CONFLICT"

    @pytest.mark.asyncio
    async def test_unexpected_error(self, tools, mock_client) -> None:
        mock_client.put = AsyncMock(side_effect=RuntimeError("crash"))
        result = json.loads(await tools["cancel_payment_link"](payment_link_id="pl-123"))
        assert result["code"] == "INTERNAL_ERROR"

    @pytest.mark.asyncio
    async def test_empty_id(self, tools) -> None:
        result = json.loads(await tools["cancel_payment_link"](payment_link_id=""))
        assert result["code"] == "VALIDATION_ERROR"


# ===================================================================
# resend_payment_link_notification
# ===================================================================

class TestResendNotification:
    @pytest.mark.asyncio
    async def test_happy_path(self, tools, mock_client) -> None:
        mock_client.patch = AsyncMock(return_value={"status": "ok"})
        result = json.loads(await tools["resend_payment_link_notification"](payment_link_id="pl-123"))
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_api_error(self, tools, mock_client) -> None:
        mock_client.patch = AsyncMock(
            side_effect=PineLabsAPIError(400, "UPSTREAM_BAD_REQUEST", "Bad")
        )
        result = json.loads(await tools["resend_payment_link_notification"](payment_link_id="pl-123"))
        assert result["code"] == "UPSTREAM_BAD_REQUEST"

    @pytest.mark.asyncio
    async def test_unexpected_error(self, tools, mock_client) -> None:
        mock_client.patch = AsyncMock(side_effect=RuntimeError("crash"))
        result = json.loads(await tools["resend_payment_link_notification"](payment_link_id="pl-123"))
        assert result["code"] == "INTERNAL_ERROR"

    @pytest.mark.asyncio
    async def test_id_too_long(self, tools) -> None:
        result = json.loads(await tools["resend_payment_link_notification"](payment_link_id="x" * 51))
        assert result["code"] == "VALIDATION_ERROR"
