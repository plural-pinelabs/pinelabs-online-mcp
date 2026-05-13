"""
Pine Labs Card Payment MCP tool.

Defines the create_card_payment tool that:
1. Validates params via Pydantic models
2. Calls Pine Labs API
3. Returns the result
"""

import json
import logging
import uuid
from typing import Optional

from fastmcp import FastMCP
from pydantic import ValidationError

from pkg.pinelabs.client import PineLabsAPIError, PineLabsClient
from pkg.pinelabs.models.card_payments import (
    CardData,
    CardPayment,
    CreateCardPaymentRequest,
    PaymentAmount,
    PaymentOption,
    TokenTxnType,
)
from pkg.pinelabs.utils.errors import (
    api_error_response,
    unexpected_error_response,
    validation_error_response,
)
from pkg.pinelabs.utils.validators import validate_resource_id
from pkg.pinelabs import routes

logger = logging.getLogger("pinelabs-mcp-server.card_payments")


def _sanitize_validation_error(e: Exception) -> str:
    """Format a validation error without echoing user input (PII safety)."""
    if isinstance(e, ValidationError):
        return json.dumps(e.errors(include_input=False), default=str)
    return str(e)


def register_card_payment_tools(
    mcp: FastMCP, client: PineLabsClient
) -> None:
    """Register card payment tools on the FastMCP server."""

    @mcp.tool(
        name="create_card_payment",
        description=(
            "Create a card payment for an existing order. "
            "Supports direct card and tokenized card payments. "
            "Requires order_id, card holder name, amount, and "
            "card details."
        ),
    )
    async def create_card_payment(
        order_id: str,
        card_name: str,
        amount_value: int,
        card_number: Optional[str] = None,
        card_cvv: Optional[str] = None,
        card_expiry_month: Optional[str] = None,
        card_expiry_year: Optional[str] = None,
        save_card: Optional[bool] = None,
        use_token: bool = False,
        token_last4_digit: Optional[str] = None,
        token_expiry_month: Optional[str] = None,
        token_expiry_year: Optional[str] = None,
        token_value: Optional[str] = None,
        token_cryptogram: Optional[str] = None,
        token_txn_type: Optional[str] = None,
        token_cvv: Optional[str] = None,
        merchant_payment_reference: Optional[str] = None,
        currency: str = "INR",
        idempotency_key: Optional[str] = None,
    ) -> str:
        """Create a card payment for an existing Pine Labs order.

        Args:
            order_id: Pine Labs order ID
                (e.g., v1-4405071524-aa-qlAtAf).
            card_name: Cardholder name as printed on the card.
            amount_value: Amount in paisa (e.g., 1100 = Rs.11).
            card_number: Full card number (13-19 digits) - direct.
            card_cvv: Card CVV (3-4 digits) - direct.
            card_expiry_month: Card expiry month (MM) - direct.
            card_expiry_year: Card expiry year (YYYY) - direct.
            save_card: Whether to save card for future transactions.
            use_token: Set True for tokenized card payments.
            token_last4_digit: Last 4 digits of tokenized card.
            token_expiry_month: Token expiry month (MM).
            token_expiry_year: Token expiry year (YYYY).
            token_value: Token value.
            token_cryptogram: Token cryptogram.
            token_txn_type: ALT_TOKEN, NETWORK_TOKEN, or
                ISSUER_TOKEN.
            token_cvv: CVV for ALT_TOKEN transactions.
            merchant_payment_reference: Your unique payment ref
                (max 50 chars). Auto-generated if omitted.
            currency: Three-letter ISO currency code (default INR).
            idempotency_key: Optional idempotency key.
        """
        try:
            order_id = validate_resource_id(order_id, "order_id")
        except ValueError as e:
            return validation_error_response(str(e))

        if merchant_payment_reference:
            try:
                merchant_payment_reference = validate_resource_id(
                    merchant_payment_reference,
                    "merchant_payment_reference",
                    max_length=50,
                )
            except ValueError as e:
                return validation_error_response(str(e))
        else:
            merchant_payment_reference = uuid.uuid4().hex

        try:
            if use_token:
                card_data = CardData(
                    card_holder_name=card_name,
                    card_cvv=token_cvv,
                    save=save_card,
                    token_txn_type=(
                        TokenTxnType(token_txn_type)
                        if token_txn_type
                        else None
                    ),
                    token_value=token_value,
                    token_cryptogram=token_cryptogram,
                    last4_digit=token_last4_digit,
                    token_expiry_month=token_expiry_month,
                    token_expiry_year=token_expiry_year,
                )
            else:
                card_data = CardData(
                    card_number=card_number,
                    card_expiry_month=card_expiry_month,
                    card_expiry_year=card_expiry_year,
                    card_cvv=card_cvv,
                    card_holder_name=card_name,
                    save=save_card,
                )

            request_body = CreateCardPaymentRequest(
                payments=[
                    CardPayment(
                        merchant_payment_reference=(
                            merchant_payment_reference
                        ),
                        payment_amount=PaymentAmount(
                            value=amount_value, currency=currency,
                        ),
                        payment_method="CARD",
                        payment_option=PaymentOption(
                            card_data=card_data
                        ),
                    )
                ]
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info(
                "Creating card payment: order_id=%s ref=%s "
                "amount=%s %s",
                order_id,
                merchant_payment_reference,
                amount_value,
                currency,
            )
            response = await client.post(
                routes.CARD_PAYMENT_CREATE.format(
                    order_id=order_id
                ),
                payload,
                idempotency_key,
            )
            return json.dumps(response, indent=2)

        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error creating card payment: %s", e
            )
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error(
                "Unexpected error creating card payment: %s", e
            )
            return unexpected_error_response(
                e, "create card payment"
            )
