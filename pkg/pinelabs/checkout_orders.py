"""
Pine Labs Checkout Order MCP tools.

Defines the create_order tool that generates a checkout link.
"""

import json
import logging
from typing import Optional

from pydantic import ValidationError
from fastmcp import FastMCP

from pkg.pinelabs.client import PineLabsClient, PineLabsAPIError
from pkg.pinelabs.models.payment_links import Address, Amount
from pkg.pinelabs.models.checkout_orders import (
    CheckoutAllowedPaymentMethod,
    CheckoutCustomer,
    CheckoutProduct,
    CreateCheckoutOrderRequest,
    IntegrationMode,
    PurchaseDetails,
)
from pkg.pinelabs.utils.validators import validate_resource_id
from pkg.pinelabs.utils.errors import (
    api_error_response,
    validation_error_response,
    unexpected_error_response,
)
from pkg.pinelabs import routes

logger = logging.getLogger("pinelabs-mcp-server.checkout_orders")


def _sanitize_validation_error(e: Exception) -> str:
    if isinstance(e, ValidationError):
        return json.dumps(e.errors(include_input=False), default=str)
    return str(e)


def register_checkout_order_tools(
    mcp: FastMCP, client: PineLabsClient
) -> None:
    """Register all checkout order tools on the FastMCP server."""

    @mcp.tool(
        name="create_order",
        description=(
            "Create a new Pine Labs checkout order and generate a "
            "checkout link. Returns an order ID and redirect URL. "
            "Requires a merchant order reference and amount (in "
            "paisa). Supports REDIRECT, IFRAME, and SDK modes."
        ),
    )
    async def create_order(
        merchant_order_reference: str,
        amount_value: int,
        currency: str = "INR",
        integration_mode: Optional[str] = None,
        pre_auth: Optional[bool] = None,
        allowed_payment_methods: Optional[list[str]] = None,
        notes: Optional[str] = None,
        callback_url: Optional[str] = None,
        failure_callback_url: Optional[str] = None,
        customer_email: Optional[str] = None,
        customer_first_name: Optional[str] = None,
        customer_last_name: Optional[str] = None,
        customer_mobile: Optional[str] = None,
        customer_country_code: Optional[str] = None,
        customer_id: Optional[str] = None,
        billing_address1: Optional[str] = None,
        billing_address2: Optional[str] = None,
        billing_address3: Optional[str] = None,
        billing_city: Optional[str] = None,
        billing_state: Optional[str] = None,
        billing_country: Optional[str] = None,
        billing_pincode: Optional[str] = None,
        billing_full_name: Optional[str] = None,
        shipping_address1: Optional[str] = None,
        shipping_address2: Optional[str] = None,
        shipping_address3: Optional[str] = None,
        shipping_city: Optional[str] = None,
        shipping_state: Optional[str] = None,
        shipping_country: Optional[str] = None,
        shipping_pincode: Optional[str] = None,
        shipping_full_name: Optional[str] = None,
        merchant_metadata: Optional[dict[str, str]] = None,
        product_code: Optional[str] = None,
        product_amount: Optional[int] = None,
    ) -> str:
        """Create a Pine Labs checkout order (generate checkout link)."""
        # Validate merchant_order_reference
        try:
            merchant_order_reference = validate_resource_id(
                merchant_order_reference,
                "merchant_order_reference",
                max_length=50,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        # Build nested objects
        try:
            billing_address = None
            billing_fields = {
                "address1": billing_address1,
                "address2": billing_address2,
                "address3": billing_address3,
                "city": billing_city,
                "state": billing_state,
                "country": billing_country,
                "pincode": billing_pincode,
                "full_name": billing_full_name,
            }
            if any(v is not None for v in billing_fields.values()):
                billing_address = Address(
                    address_category="billing",
                    **{k: v for k, v in billing_fields.items()
                       if v is not None},
                )

            shipping_address = None
            shipping_fields = {
                "address1": shipping_address1,
                "address2": shipping_address2,
                "address3": shipping_address3,
                "city": shipping_city,
                "state": shipping_state,
                "country": shipping_country,
                "pincode": shipping_pincode,
                "full_name": shipping_full_name,
            }
            if any(v is not None for v in shipping_fields.values()):
                shipping_address = Address(
                    address_category="shipping",
                    **{k: v for k, v in shipping_fields.items()
                       if v is not None},
                )

            customer = None
            customer_fields = {
                "email_id": customer_email,
                "first_name": customer_first_name,
                "last_name": customer_last_name,
                "mobile_number": customer_mobile,
                "country_code": customer_country_code,
                "customer_id": customer_id,
                "billing_address": billing_address,
                "shipping_address": shipping_address,
            }
            if any(v is not None for v in customer_fields.values()):
                customer = CheckoutCustomer(**customer_fields)

            purchase_details = None
            if customer or merchant_metadata:
                purchase_details = PurchaseDetails(
                    customer=customer,
                    merchant_metadata=merchant_metadata,
                )

        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        # Payment methods
        payment_methods = None
        if allowed_payment_methods:
            try:
                payment_methods = [
                    CheckoutAllowedPaymentMethod(m.upper())
                    for m in allowed_payment_methods
                ]
            except ValueError:
                valid = [
                    e.value for e in CheckoutAllowedPaymentMethod
                ]
                return validation_error_response(
                    f"Invalid payment method. Allowed: {valid}"
                )

        # Integration mode
        mode = None
        if integration_mode:
            try:
                mode = IntegrationMode(integration_mode.upper())
            except ValueError:
                valid = [e.value for e in IntegrationMode]
                return validation_error_response(
                    f"Invalid integration mode. Allowed: {valid}"
                )

        # Products (for EMI orders)
        products = None
        try:
            if product_code:
                pd_kwargs: dict = {"product_code": product_code}
                if product_amount is not None:
                    pd_kwargs["product_amount"] = Amount(
                        value=product_amount, currency=currency,
                    )
                products = [CheckoutProduct(**pd_kwargs)]
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        # Build request
        try:
            request_body = CreateCheckoutOrderRequest(
                merchant_order_reference=merchant_order_reference,
                order_amount=Amount(
                    value=amount_value, currency=currency,
                ),
                integration_mode=mode,
                pre_auth=pre_auth,
                allowed_payment_methods=payment_methods,
                notes=notes,
                callback_url=callback_url,
                failure_callback_url=failure_callback_url,
                purchase_details=purchase_details,
                product=products,
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        # Call API
        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info(
                "Creating checkout order: ref=%s amount=%s %s",
                merchant_order_reference,
                amount_value,
                currency,
            )
            response = await client.post(
                routes.CHECKOUT_ORDER_CREATE, payload,
            )
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
                "Unexpected error creating checkout order: %s",
                type(e).__name__,
            )
            return unexpected_error_response(
                e, "create checkout order",
            )
