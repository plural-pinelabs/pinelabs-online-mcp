"""Tests for tools/orders.py — get_order_by_order_id and cancel_order tools."""

import json
from unittest.mock import AsyncMock

import pytest

from pkg.pinelabs.client import PineLabsAPIError
from pkg.pinelabs.orders import register_order_tools


@pytest.fixture()
def _register(fake_mcp, mock_client):
    register_order_tools(fake_mcp, mock_client)


@pytest.fixture()
def tool(fake_mcp, mock_client, _register):
    return fake_mcp.tools["get_order_by_order_id"]


@pytest.fixture()
def cancel_tool(fake_mcp, mock_client, _register):
    return fake_mcp.tools["cancel_order"]


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestGetOrderHappyPath:
    @pytest.mark.asyncio
    async def test_success(self, tool, mock_client) -> None:
        mock_client.get = AsyncMock(return_value={
            "order_id": "v1-123-aa-abc",
            "status": "PROCESSED",
        })

        result = json.loads(await tool(order_id="v1-123-aa-abc"))
        assert result["status"] == "PROCESSED"
        mock_client.get.assert_awaited_once()


# ---------------------------------------------------------------------------
# API error
# ---------------------------------------------------------------------------

class TestGetOrderAPIError:
    @pytest.mark.asyncio
    async def test_api_error(self, tool, mock_client) -> None:
        mock_client.get = AsyncMock(
            side_effect=PineLabsAPIError(404, "UPSTREAM_NOT_FOUND", "Not found")
        )

        result = json.loads(await tool(order_id="v1-missing"))
        assert result["code"] == "UPSTREAM_NOT_FOUND"
        assert result["status_code"] == 404


# ---------------------------------------------------------------------------
# Unexpected error
# ---------------------------------------------------------------------------

class TestGetOrderUnexpectedError:
    @pytest.mark.asyncio
    async def test_unexpected_error(self, tool, mock_client) -> None:
        mock_client.get = AsyncMock(side_effect=RuntimeError("crash"))

        result = json.loads(await tool(order_id="v1-123"))
        assert result["code"] == "INTERNAL_ERROR"
        assert result["status_code"] == 500


# ---------------------------------------------------------------------------
# Input validation — order_id goes straight to the URL path;
# the tool doesn't validate it independently (unlike card_payments),
# so there's no local validation test needed.
# ---------------------------------------------------------------------------


# ===========================================================================
# cancel_order tool tests
# ===========================================================================


class TestCancelOrderHappyPath:
    @pytest.mark.asyncio
    async def test_success(self, cancel_tool, mock_client) -> None:
        mock_client.put = AsyncMock(return_value={
            "data": {
                "order_id": "v1-5757575757-aa-hU1rUd",
                "status": "CANCELLED",
                "type": "CHARGE",
                "pre_auth": True,
                "order_amount": {"value": 50000, "currency": "INR"},
            }
        })

        result = json.loads(await cancel_tool(order_id="v1-5757575757-aa-hU1rUd"))
        assert result["data"]["status"] == "CANCELLED"
        mock_client.put.assert_awaited_once()
        call_args = mock_client.put.call_args
        assert "/cancel" in call_args[0][0]


class TestCancelOrderAPIError:
    @pytest.mark.asyncio
    async def test_not_found(self, cancel_tool, mock_client) -> None:
        mock_client.put = AsyncMock(
            side_effect=PineLabsAPIError(404, "ORDER_NOT_FOUND", "Order not found")
        )

        result = json.loads(await cancel_tool(order_id="v1-missing"))
        assert result["code"] == "ORDER_NOT_FOUND"
        assert result["status_code"] == 404

    @pytest.mark.asyncio
    async def test_operation_not_allowed(self, cancel_tool, mock_client) -> None:
        mock_client.put = AsyncMock(
            side_effect=PineLabsAPIError(422, "OPERATION_NOT_ALLOWED", "Void is not allowed")
        )

        result = json.loads(await cancel_tool(order_id="v1-123-aa-abc"))
        assert result["code"] == "OPERATION_NOT_ALLOWED"
        assert result["status_code"] == 422

    @pytest.mark.asyncio
    async def test_unauthorized(self, cancel_tool, mock_client) -> None:
        mock_client.put = AsyncMock(
            side_effect=PineLabsAPIError(401, "UNAUTHORIZED", "Unauthorized")
        )

        result = json.loads(await cancel_tool(order_id="v1-123-aa-abc"))
        assert result["code"] == "UNAUTHORIZED"
        assert result["status_code"] == 401


class TestCancelOrderUnexpectedError:
    @pytest.mark.asyncio
    async def test_unexpected_error(self, cancel_tool, mock_client) -> None:
        mock_client.put = AsyncMock(side_effect=RuntimeError("crash"))

        result = json.loads(await cancel_tool(order_id="v1-123"))
        assert result["code"] == "INTERNAL_ERROR"
        assert result["status_code"] == 500


class TestCancelOrderValidation:
    @pytest.mark.asyncio
    async def test_invalid_order_id(self, cancel_tool, mock_client) -> None:
        result = json.loads(await cancel_tool(order_id=""))
        assert result["code"] == "VALIDATION_ERROR"
