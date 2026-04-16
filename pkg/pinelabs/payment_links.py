"""
Pine Labs Payment Link MCP tools.

Defines payment link tools that:
1. Validate params via Pydantic models
2. Call Pine Labs API (token auto-managed by client)
3. Return the result
"""

import json
import logging
import uuid
from typing import Optional

from pydantic import ValidationError
from fastmcp import FastMCP

from pkg.pinelabs.client import PineLabsClient, PineLabsAPIError
from pkg.pinelabs.models.payment_links import (
    Amount,
    Address,
    AllowedPaymentMethod,
    CreatePaymentLinkRequest,
    Customer,
    ProductDetail,
)
from pkg.pinelabs.utils.validators import (
    validate_resource_id,
    validate_expire_by,
)
from pkg.pinelabs.utils.errors import (
    api_error_response,
    validation_error_response,
    unexpected_error_response,
)
from pkg.pinelabs import routes

logger = logging.getLogger("pinelabs-mcp-server.payment_links")


def _sanitize_validation_error(e: Exception) -> str:
    """Format a validation error without echoing user input."""
    if isinstance(e, ValidationError):
        return json.dumps(e.errors(include_input=False), default=str)
    return str(e)


def register_payment_link_tools(
    mcp: FastMCP, client: PineLabsClient
) -> None:
    """Register all payment link tools on the FastMCP server."""

    @mcp.tool(
        name="create_payment_link",
        description=(
            "Create a new Pine Labs payment link. "
            "Returns a short URL that customers can use to make "
            "payments. Requires amount (in paisa) and customer "
            "details."
        ),
    )
    async def create_payment_link(
        amount_value: int,
        currency: str = "INR",
        customer_email: Optional[str] = None,
        customer_first_name: Optional[str] = None,
        customer_last_name: Optional[str] = None,
        customer_mobile: Optional[str] = None,
        customer_country_code: Optional[str] = None,
        customer_id: Optional[str] = None,
        description: Optional[str] = None,
        expire_by: Optional[str] = None,
        allowed_payment_methods: Optional[list[str]] = None,
        merchant_payment_link_reference: Optional[str] = None,
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
        cart_coupon_discount_amount: Optional[int] = None,
    ) -> str:
        """Create a Pine Labs payment link.

        Args:
            amount_value: Amount in paisa (e.g., 50000 = Rs.500).
            currency: Three-letter ISO currency code (default: INR).
            customer_email: Customer email address.
            customer_first_name: Customer first name.
            customer_last_name: Customer last name.
            customer_mobile: Customer mobile number (10-20 digits).
            customer_country_code: Country code (e.g., +91).
            customer_id: Customer ID in Pine Labs database.
            description: Payment description.
            expire_by: Expiry in ISO 8601. Max 180 days.
            allowed_payment_methods: CARD, UPI, POINTS, etc.
            merchant_payment_link_reference: Unique ref (1-50 chars).
            billing_address1..billing_full_name: Billing address.
            shipping_address1..shipping_full_name: Shipping address.
            merchant_metadata: Custom key-value metadata.
            product_code: Product identifier.
            product_amount: Product amount in paisa.
            cart_coupon_discount_amount: Coupon discount in paisa.
        """
        # Validate merchant reference
        if merchant_payment_link_reference:
            try:
                merchant_payment_link_reference = validate_resource_id(
                    merchant_payment_link_reference,
                    "merchant_payment_link_reference",
                    max_length=50,
                )
            except ValueError as e:
                return validation_error_response(str(e))
        else:
            merchant_payment_link_reference = uuid.uuid4().hex

        # Validate expire_by
        if expire_by:
            try:
                validate_expire_by(expire_by)
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

            customer = Customer(
                email_id=customer_email,
                first_name=customer_first_name,
                last_name=customer_last_name,
                mobile_number=customer_mobile,
                country_code=customer_country_code,
                customer_id=customer_id,
                billing_address=billing_address,
                shipping_address=shipping_address,
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        # Allowed payment methods
        payment_methods = None
        if allowed_payment_methods:
            try:
                payment_methods = [
                    AllowedPaymentMethod(m.upper())
                    for m in allowed_payment_methods
                ]
            except ValueError:
                valid = [e.value for e in AllowedPaymentMethod]
                return validation_error_response(
                    f"Invalid payment method. Allowed: {valid}"
                )

        # Product details / cart coupon
        product_details = None
        cart_coupon = None
        try:
            if product_code:
                pd_kwargs: dict = {"product_code": product_code}
                if product_amount is not None:
                    pd_kwargs["product_amount"] = Amount(
                        value=product_amount, currency=currency,
                    )
                product_details = [ProductDetail(**pd_kwargs)]
            if cart_coupon_discount_amount is not None:
                cart_coupon = Amount(
                    value=cart_coupon_discount_amount,
                    currency=currency,
                )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        # Build request
        try:
            request_body = CreatePaymentLinkRequest(
                amount=Amount(value=amount_value, currency=currency),
                merchant_payment_link_reference=(
                    merchant_payment_link_reference
                ),
                customer=customer,
                description=description,
                expire_by=expire_by,
                allowed_payment_methods=payment_methods,
                product_details=product_details,
                cart_coupon_discount_amount=cart_coupon,
                merchant_metadata=merchant_metadata,
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        # Call API
        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info(
                "Creating payment link: ref=%s amount=%s %s",
                merchant_payment_link_reference,
                amount_value,
                currency,
            )
            response = await client.post(
                routes.PAYMENT_LINK_CREATE, payload,
            )
            return json.dumps(response, indent=2)

        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error creating payment link: %s", e,
            )
            return unexpected_error_response(
                e, "create payment link",
            )

    @mcp.tool(
        name="get_payment_link_by_id",
        description=(
            "Fetch a Pine Labs payment link by its payment link ID. "
            "Returns full payment link details including status, "
            "amount, customer info, and more."
        ),
    )
    async def get_payment_link_by_id(
        payment_link_id: str,
    ) -> str:
        """Get a Pine Labs payment link by its ID."""
        try:
            payment_link_id = validate_resource_id(
                payment_link_id, "payment_link_id",
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info(
                "Fetching payment link: id=%s", payment_link_id,
            )
            response = await client.get(
                routes.PAYMENT_LINK_GET.format(
                    payment_link_id=payment_link_id,
                ),
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching payment link: %s", e,
            )
            return unexpected_error_response(
                e, "fetch payment link",
            )

    @mcp.tool(
        name="get_payment_link_by_merchant_reference",
        description=(
            "Fetch a Pine Labs payment link by its merchant "
            "payment link reference. Returns the full payment "
            "link details."
        ),
    )
    async def get_payment_link_by_merchant_reference(
        merchant_payment_link_reference: str,
    ) -> str:
        """Get a payment link by merchant reference."""
        try:
            merchant_payment_link_reference = validate_resource_id(
                merchant_payment_link_reference,
                "merchant_payment_link_reference",
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info(
                "Fetching payment link by ref: %s",
                merchant_payment_link_reference,
            )
            response = await client.get(
                routes.PAYMENT_LINK_GET_BY_REF.format(
                    ref=merchant_payment_link_reference,
                ),
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching payment link: %s", e,
            )
            return unexpected_error_response(
                e, "fetch payment link",
            )

    @mcp.tool(
        name="cancel_payment_link",
        description=(
            "Cancel a Pine Labs payment link. Only links with "
            "status CREATED can be cancelled. Returns the updated "
            "payment link details with status CANCELLED."
        ),
    )
    async def cancel_payment_link(
        payment_link_id: str,
    ) -> str:
        """Cancel a Pine Labs payment link."""
        try:
            payment_link_id = validate_resource_id(
                payment_link_id, "payment_link_id",
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info(
                "Cancelling payment link: id=%s", payment_link_id,
            )
            response = await client.put(
                routes.PAYMENT_LINK_CANCEL.format(
                    payment_link_id=payment_link_id,
                ),
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error cancelling payment link: %s", e,
            )
            return unexpected_error_response(
                e, "cancel payment link",
            )

    @mcp.tool(
        name="resend_payment_link_notification",
        description=(
            "Resend a Pine Labs payment link notification to the "
            "customer. Only works for active (CREATED) links."
        ),
    )
    async def resend_payment_link_notification(
        payment_link_id: str,
    ) -> str:
        """Resend payment link notification to the customer."""
        try:
            payment_link_id = validate_resource_id(
                payment_link_id, "payment_link_id",
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info(
                "Resending notification: id=%s", payment_link_id,
            )
            response = await client.patch(
                routes.PAYMENT_LINK_NOTIFY.format(
                    payment_link_id=payment_link_id,
                ),
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error resending notification: %s", e,
            )
            return unexpected_error_response(
                e, "resend notification",
            )
