"""
Pine Labs Refund MCP tool.

Defines the create_refund tool that:
1. Validates params via Pydantic models
2. Calls Pine Labs API
3. Returns the result
"""

import json
import logging
from typing import Optional

from fastmcp import FastMCP
from pydantic import ValidationError

from pkg.pinelabs.client import PineLabsAPIError, PineLabsClient
from pkg.pinelabs.models.refunds import (
    CreateRefundRequest,
    RefundAmount,
    RefundProduct,
    RefundProductAmount,
    SplitAmount,
    SplitDetail,
    SplitInfo,
)
from pkg.pinelabs.utils.errors import (
    api_error_response,
    unexpected_error_response,
    validation_error_response,
)
from pkg.pinelabs.utils.validators import validate_resource_id
from pkg.pinelabs import routes

logger = logging.getLogger("pinelabs-mcp-server.refunds")


def _sanitize_validation_error(e: Exception) -> str:
    """Format a validation error without echoing user input."""
    if isinstance(e, ValidationError):
        return json.dumps(e.errors(include_input=False), default=str)
    return str(e)


def register_refund_tools(
    mcp: FastMCP, client: PineLabsClient
) -> None:
    """Register all refund tools on the FastMCP server."""

    @mcp.tool(
        name="create_refund",
        description=(
            "Initiate a refund against a Pine Labs order. "
            "Supports full refunds, partial refunds, multi-cart "
            "partial refunds, and split settlement refunds. "
            "Requires the order_id and refund amount."
        ),
    )
    async def create_refund(
        order_id: str,
        amount_value: int,
        merchant_order_reference: str,
        currency: str = "INR",
        merchant_metadata: Optional[dict[str, str]] = None,
        products: Optional[list[dict]] = None,
        split_type: Optional[str] = None,
        split_details: Optional[list[dict]] = None,
        idempotency_key: Optional[str] = None,
    ) -> str:
        """Create a refund against a Pine Labs order.

        Args:
            order_id: Unique identifier of the order in the Pine
                Labs database. Example: v1-5757575757-aa-hU1rUd
            amount_value: Refund amount in paisa
                (e.g., 50000 = Rs.500). Min: 100, Max: 100000000.
            merchant_order_reference: Unique identifier for this
                refund (1-50 chars).
            currency: Three-letter ISO currency code (default: INR).
            merchant_metadata: Key-value pairs for additional info.
            products: Product details for multi-cart partial refunds.
                Each item: {"product_code": "...",
                "product_imei": "...",
                "product_amount_value": 10000,
                "product_amount_currency": "INR"}.
            split_type: Type of split for split settlement refunds.
                Example: "AMOUNT".
            split_details: Split settlement details array. Each item:
                {"parent_order_split_settlement_id": "...",
                "split_merchant_id": "...",
                "merchant_settlement_reference": "...",
                "amount_value": 20000, "amount_currency": "INR",
                "status": "DO_NOT_RECOVER"}.
            idempotency_key: Optional idempotency key.
        """
        # Validate order_id
        try:
            order_id = validate_resource_id(
                order_id,
                "order_id",
                max_length=100,
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        if (
            not isinstance(amount_value, int)
            or amount_value < 100
            or amount_value > 100_000_000
        ):
            return validation_error_response(
                "amount_value must be an integer between 100 and "
                "100000000 (in paisa)."
            )

        # Build product models (multi-cart partial refunds)
        product_models = None
        if products:
            try:
                product_models = []
                for p in products:
                    product_amount = None
                    if "product_amount_value" in p:
                        product_amount = RefundProductAmount(
                            value=p["product_amount_value"],
                            currency=p.get(
                                "product_amount_currency", "INR"
                            ),
                        )
                    product_models.append(
                        RefundProduct(
                            product_code=p["product_code"],
                            product_imei=p.get("product_imei"),
                            product_amount=product_amount,
                        )
                    )
            except (
                KeyError,
                ValueError,
                TypeError,
                ValidationError,
            ):
                return validation_error_response(
                    "Invalid product data. Each product requires "
                    "'product_code'."
                )

        # Build split info (split settlement refunds)
        split_info_model = None
        if split_type:
            split_detail_models = None
            if split_details:
                try:
                    split_detail_models = []
                    for sd in split_details:
                        split_amount = None
                        if "amount_value" in sd:
                            split_amount = SplitAmount(
                                value=sd["amount_value"],
                                currency=sd.get(
                                    "amount_currency", "INR"
                                ),
                            )
                        split_detail_models.append(
                            SplitDetail(
                                parent_order_split_settlement_id=sd[
                                    "parent_order_split_settlement_id"
                                ],
                                split_merchant_id=str(
                                    sd["split_merchant_id"]
                                ),
                                merchant_settlement_reference=sd[
                                    "merchant_settlement_reference"
                                ],
                                amount=split_amount,
                                status=sd.get("status"),
                            )
                        )
                except (
                    KeyError,
                    ValueError,
                    TypeError,
                    ValidationError,
                ):
                    return validation_error_response(
                        "Invalid split detail data. Each split "
                        "detail requires "
                        "'parent_order_split_settlement_id', "
                        "'split_merchant_id', and "
                        "'merchant_settlement_reference'."
                    )
            try:
                split_info_model = SplitInfo(
                    split_type=split_type,
                    split_details=split_detail_models,
                )
            except (ValidationError, ValueError) as e:
                return validation_error_response(
                    _sanitize_validation_error(e)
                )

        # Build request
        try:
            request_body = CreateRefundRequest(
                merchant_order_reference=merchant_order_reference,
                order_amount=RefundAmount(
                    value=amount_value, currency=currency
                ),
                merchant_metadata=merchant_metadata,
                products=product_models,
                split_info=split_info_model,
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        # Call API
        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info(
                "Creating refund: order_id=%s ref=%s",
                order_id,
                merchant_order_reference,
            )
            response = await client.post(
                routes.REFUND_CREATE.format(order_id=order_id),
                payload,
                idempotency_key,
            )
            return json.dumps(response, indent=2)

        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error("Unexpected error creating refund: %s", e)
            return unexpected_error_response(e, "create refund")
