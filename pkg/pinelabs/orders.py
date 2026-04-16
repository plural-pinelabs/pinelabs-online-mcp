"""
Pine Labs Order MCP tools.

Defines order tools: get_order_by_order_id, cancel_order.
"""

import json
import logging

from fastmcp import FastMCP

from pkg.pinelabs.client import PineLabsClient, PineLabsAPIError
from pkg.pinelabs.utils.validators import validate_resource_id
from pkg.pinelabs.utils.errors import (
    api_error_response,
    validation_error_response,
    unexpected_error_response,
)
from pkg.pinelabs import routes

logger = logging.getLogger("pinelabs-mcp-server.orders")


def register_order_tools(
    mcp: FastMCP, client: PineLabsClient
) -> None:
    """Register all order tools on the FastMCP server."""

    @mcp.tool(
        name="cancel_order",
        description=(
            "Cancel a pre-authorized payment against a Pine Labs "
            "order. Can only be used when the order was created "
            "with pre_auth=true. Returns cancelled order details."
        ),
    )
    async def cancel_order(order_id: str) -> str:
        """Cancel a pre-authorized order by order ID."""
        try:
            order_id = validate_resource_id(
                order_id, "order_id", allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            path = routes.ORDER_CANCEL.format(
                order_id=order_id,
            )
            logger.info("Cancelling order: order_id=%s", order_id)
            response = await client.put(path)
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error cancelling order: %s",
                type(e).__name__,
            )
            return unexpected_error_response(e, "cancel order")

    @mcp.tool(
        name="get_order_by_order_id",
        description=(
            "Retrieve order details from Pine Labs by order ID. "
            "Returns comprehensive order information including "
            "status, payment details, refunds, and customer info."
        ),
    )
    async def get_order_by_order_id(order_id: str) -> str:
        """Get order details by order ID from Pine Labs."""
        try:
            order_id = validate_resource_id(
                order_id, "order_id", allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            path = routes.ORDER_GET.format(
                order_id=order_id,
            )
            logger.info("Fetching order: order_id=%s", order_id)
            response = await client.get(path)
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching order: %s",
                type(e).__name__,
            )
            return unexpected_error_response(e, "fetch order")
