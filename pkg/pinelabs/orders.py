"""
Pine Labs Order MCP tools.

Defines order tools: get_order_by_order_id, cancel_order,
capture_order, get_order_by_merchant_order_reference,
fetch_order_payments.
"""

import json
import logging
from typing import Optional

from fastmcp import FastMCP
from pydantic import ValidationError

from pkg.pinelabs.client import PineLabsClient, PineLabsAPIError
from pkg.pinelabs.models.checkout_orders import CaptureOrderRequest
from pkg.pinelabs.models.payment_links import Amount
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

    @mcp.tool(
        name="get_order_by_merchant_order_reference",
        description=(
            "Retrieve order details from Pine Labs by merchant "
            "order reference. Returns comprehensive order "
            "information including status, payment details, "
            "refunds, customer info, and more."
        ),
    )
    async def get_order_by_merchant_order_reference(
        merchant_order_reference: str,
    ) -> str:
        """Get order details by merchant order reference."""
        try:
            merchant_order_reference = validate_resource_id(
                merchant_order_reference,
                "merchant_order_reference",
                max_length=50,
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            path = routes.ORDER_GET_BY_REF.format(
                merchant_order_reference=merchant_order_reference,
            )
            logger.info(
                "Fetching order by merchant reference: ref=%s",
                merchant_order_reference,
            )
            response = await client.get(path)
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code,
                e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching order by ref: %s",
                type(e).__name__,
            )
            return unexpected_error_response(
                e, "fetch order by merchant reference"
            )

    @mcp.tool(
        name="capture_order",
        description=(
            "Capture a pre-authorized payment against a Pine Labs "
            "order. Can only be used when the order was created "
            "with pre_auth=true. Supports full capture (no amount) "
            "or partial capture (with amount). Only one partial "
            "capture per order is allowed; any remaining amount "
            "will be auto-reversed to the customer's account. "
            "Returns the captured order details including status "
            "and payment info."
        ),
    )
    async def capture_order(
        order_id: str,
        merchant_capture_reference: str,
        capture_amount_value: Optional[int] = None,
        capture_amount_currency: Optional[str] = "INR",
        idempotency_key: Optional[str] = None,
    ) -> str:
        """Capture a pre-authorized order.

        Args:
            order_id: Unique identifier of the order
                (e.g. v1-5757575757-aa-hU1rUd).
            merchant_capture_reference: Unique capture reference
                (1-50 chars, alphanumeric/hyphens/underscores).
            capture_amount_value: Amount to capture in paisa
                (e.g., 50000 = Rs.500). Required for partial
                capture. If omitted, full amount is captured.
            capture_amount_currency: Currency code (default INR).
            idempotency_key: Optional idempotency key.
        """
        try:
            order_id = validate_resource_id(
                order_id, "order_id", allow_dots=True
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            merchant_capture_reference = validate_resource_id(
                merchant_capture_reference,
                "merchant_capture_reference",
                max_length=50,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            capture_amount = None
            if capture_amount_value is not None:
                capture_amount = Amount(
                    value=capture_amount_value,
                    currency=capture_amount_currency or "INR",
                )
            request_body = CaptureOrderRequest(
                merchant_capture_reference=(
                    merchant_capture_reference
                ),
                capture_amount=capture_amount,
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(str(e))

        try:
            path = routes.ORDER_CAPTURE.format(order_id=order_id)
            payload = request_body.model_dump(exclude_none=True)
            logger.info(
                "Capturing order: order_id=%s ref=%s",
                order_id,
                merchant_capture_reference,
            )
            response = await client.put(
                path, payload, idempotency_key
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code,
                e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error(
                "Unexpected error capturing order: %s",
                type(e).__name__,
            )
            return unexpected_error_response(e, "capture order")

    @mcp.tool(
        name="fetch_order_payments",
        description=(
            "Fetch all payments made against a Pine Labs order. "
            "Returns the payments array from the order, including "
            "payment method, status, amount, acquirer data, and "
            "transaction references. Use when you need payment "
            "details for a specific order."
        ),
    )
    async def fetch_order_payments(order_id: str) -> str:
        """Fetch all payments for a specific order by order ID."""
        try:
            order_id = validate_resource_id(
                order_id, "order_id", allow_dots=True
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            path = routes.ORDER_GET.format(order_id=order_id)
            logger.info(
                "Fetching order payments: order_id=%s", order_id
            )
            response = await client.get(path)
            order_data = (
                response.get("data", response)
                if isinstance(response, dict)
                else response
            )
            payments = (
                order_data.get("payments", [])
                if isinstance(order_data, dict)
                else []
            )
            result = {
                "order_id": (
                    order_data.get("order_id", order_id)
                    if isinstance(order_data, dict)
                    else order_id
                ),
                "payments": payments,
            }
            return json.dumps(result, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code,
                e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching order payments: %s",
                type(e).__name__,
            )
            return unexpected_error_response(
                e, "fetch order payments"
            )
