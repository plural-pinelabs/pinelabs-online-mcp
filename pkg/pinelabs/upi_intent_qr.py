"""
Pine Labs UPI intent QR MCP tool.

Creates a pay order via /pay/v1/orders, then creates a UPI intent
payment with QR for that order.
"""

import base64
import json
import logging
import uuid
from typing import Optional, Union
from urllib.parse import urlparse

import httpx
from mcp.types import ImageContent, TextContent
from fastmcp import FastMCP
from pydantic import ValidationError

from pkg.pinelabs.client import PineLabsAPIError, PineLabsClient
from pkg.pinelabs.models.checkout_orders import (
    CheckoutCustomer,
    PurchaseDetails,
)
from pkg.pinelabs.models.payment_links import Address, Amount
from pkg.pinelabs.models.upi_intent_qr import (
    CreatePayOrderRequest,
    CreateUpiIntentQrPaymentRequest,
    OrderAllowedPaymentMethod,
    UpiIntentQrPayment,
)
from pkg.pinelabs.utils.errors import (
    api_error_response,
    error_response,
    unexpected_error_response,
    validation_error_response,
)
from pkg.pinelabs.utils.validators import validate_resource_id
from pkg.pinelabs.config import ALLOWED_IMAGE_DOMAINS
from pkg.pinelabs import routes

logger = logging.getLogger("pinelabs-mcp-server.upi_intent_qr")


def _is_allowed_image_url(url: str) -> bool:
    """Validate that an image URL belongs to an allowed domain."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("https",):
            return False
        hostname = parsed.hostname or ""
        return any(
            hostname == domain
            or hostname.endswith(f".{domain}")
            for domain in ALLOWED_IMAGE_DOMAINS
        )
    except Exception:
        return False


def _sanitize_validation_error(e: Exception) -> str:
    if isinstance(e, ValidationError):
        return json.dumps(
            e.errors(include_input=False), default=str,
        )
    return str(e)


def _build_purchase_details(
    *,
    customer_email: Optional[str],
    customer_first_name: Optional[str],
    customer_last_name: Optional[str],
    customer_mobile: Optional[str],
    customer_country_code: Optional[str],
    customer_id: Optional[str],
    billing_address1: Optional[str],
    billing_address2: Optional[str],
    billing_address3: Optional[str],
    billing_city: Optional[str],
    billing_state: Optional[str],
    billing_country: Optional[str],
    billing_pincode: Optional[str],
    billing_full_name: Optional[str],
    shipping_address1: Optional[str],
    shipping_address2: Optional[str],
    shipping_address3: Optional[str],
    shipping_city: Optional[str],
    shipping_state: Optional[str],
    shipping_country: Optional[str],
    shipping_pincode: Optional[str],
    shipping_full_name: Optional[str],
    merchant_metadata: Optional[dict[str, str]],
) -> Optional[PurchaseDetails]:
    """Build order purchase details from flat tool arguments."""
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

    if customer or merchant_metadata:
        return PurchaseDetails(
            customer=customer,
            merchant_metadata=merchant_metadata,
        )

    return None


def register_upi_intent_qr_tools(
    mcp: FastMCP, client: PineLabsClient
) -> None:
    """Register all UPI intent QR tools on the FastMCP server."""

    @mcp.tool(
        name="create_upi_intent_payment_with_qr",
        description=(
            "Create a Pine Labs pay order and then create a UPI "
            "intent payment with QR for that order. Returns both "
            "the order response and the QR payment response."
        ),
    )
    async def create_upi_intent_payment_with_qr(
        merchant_order_reference: str,
        amount_value: int,
        merchant_payment_reference: Optional[str] = None,
        currency: str = "INR",
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
    ) -> Union[list[Union[TextContent, ImageContent]], str]:
        """Create an order and generate a UPI intent QR payment."""
        try:
            merchant_order_reference = validate_resource_id(
                merchant_order_reference,
                "merchant_order_reference",
                max_length=50,
            )
            if merchant_payment_reference is not None:
                merchant_payment_reference = validate_resource_id(
                    merchant_payment_reference,
                    "merchant_payment_reference",
                    max_length=50,
                )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            purchase_details = _build_purchase_details(
                customer_email=customer_email,
                customer_first_name=customer_first_name,
                customer_last_name=customer_last_name,
                customer_mobile=customer_mobile,
                customer_country_code=customer_country_code,
                customer_id=customer_id,
                billing_address1=billing_address1,
                billing_address2=billing_address2,
                billing_address3=billing_address3,
                billing_city=billing_city,
                billing_state=billing_state,
                billing_country=billing_country,
                billing_pincode=billing_pincode,
                billing_full_name=billing_full_name,
                shipping_address1=shipping_address1,
                shipping_address2=shipping_address2,
                shipping_address3=shipping_address3,
                shipping_city=shipping_city,
                shipping_state=shipping_state,
                shipping_country=shipping_country,
                shipping_pincode=shipping_pincode,
                shipping_full_name=shipping_full_name,
                merchant_metadata=merchant_metadata,
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        order_payment_methods = None
        if allowed_payment_methods:
            try:
                order_payment_methods = [
                    OrderAllowedPaymentMethod(method.upper())
                    for method in allowed_payment_methods
                ]
            except ValueError:
                valid = [
                    e.value for e in OrderAllowedPaymentMethod
                ]
                return validation_error_response(
                    "Invalid payment method. "
                    f"Allowed values: {valid}"
                )

            if (OrderAllowedPaymentMethod.UPI
                    not in order_payment_methods):
                return validation_error_response(
                    "allowed_payment_methods must include UPI "
                    "for QR generation."
                )
        else:
            order_payment_methods = [
                OrderAllowedPaymentMethod.UPI,
            ]

        try:
            order_request = CreatePayOrderRequest(
                merchant_order_reference=merchant_order_reference,
                order_amount=Amount(
                    value=amount_value, currency=currency,
                ),
                pre_auth=pre_auth,
                allowed_payment_methods=order_payment_methods,
                notes=notes,
                callback_url=callback_url,
                failure_callback_url=failure_callback_url,
                purchase_details=purchase_details,
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        # Step 1: Create pay order
        try:
            order_payload = order_request.model_dump(
                exclude_none=True,
            )
            logger.info(
                "Creating pay order for UPI QR: ref=%s "
                "amount=%s %s",
                merchant_order_reference,
                amount_value,
                currency,
            )
            order_response = await client.post(
                routes.ORDER_CREATE, order_payload,
            )
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error creating pay order: "
                "code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error creating pay order: %s",
                type(e).__name__,
            )
            return unexpected_error_response(
                e, "create pay order for UPI QR",
            )

        order_data = order_response.get("data", order_response)
        order_id = (
            order_data.get("order_id")
            if isinstance(order_data, dict) else None
        )
        if not order_id:
            return error_response(
                error=(
                    "Order creation response did not include "
                    "an order_id"
                ),
                code="UPSTREAM_INVALID_RESPONSE",
                status_code=502,
            )

        order_amount_data = (
            order_data.get("order_amount", {})
            if isinstance(order_data, dict) else {}
        )
        payment_amount_value = order_amount_data.get(
            "value", amount_value,
        )
        payment_amount_currency = order_amount_data.get(
            "currency", currency,
        )

        # Step 2: Create UPI intent QR payment
        try:
            payment_request = CreateUpiIntentQrPaymentRequest(
                payments=[
                    UpiIntentQrPayment(
                        merchant_payment_reference=(
                            merchant_payment_reference
                            or str(uuid.uuid4())
                        ),
                        payment_amount=Amount(
                            value=payment_amount_value,
                            currency=payment_amount_currency,
                        ),
                    )
                ]
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        try:
            payment_payload = payment_request.model_dump(
                exclude_none=True,
            )
            logger.info(
                "Creating UPI intent QR payment: order_id=%s",
                order_id,
            )
            payment_response = await client.post(
                routes.ORDER_PAYMENTS.format(
                    order_id=order_id,
                ),
                payment_payload,
            )
            json_str = json.dumps(
                {
                    "order": order_response,
                    "payment": payment_response,
                },
                indent=2,
            )
            content: list = [
                TextContent(type="text", text=json_str),
            ]
            # Try to embed the QR image inline
            image_url = (
                payment_response.get("data", {}).get("image_url")
                if isinstance(
                    payment_response.get("data"), dict
                )
                else None
            )
            if image_url and _is_allowed_image_url(image_url):
                try:
                    async with httpx.AsyncClient(
                        timeout=10
                    ) as http:
                        img_resp = await http.get(image_url)
                        img_resp.raise_for_status()
                        mime_type = (
                            img_resp.headers.get(
                                "content-type", "image/png"
                            )
                            .split(";")[0]
                            .strip()
                        )
                        img_b64 = base64.b64encode(
                            img_resp.content
                        ).decode()
                        content.append(
                            ImageContent(
                                type="image",
                                data=img_b64,
                                mimeType=mime_type,
                            )
                        )
                except Exception as img_err:
                    logger.warning(
                        "Could not fetch QR image: %s", img_err,
                    )
            elif image_url:
                logger.warning(
                    "Blocked image fetch from untrusted domain: "
                    "%s",
                    urlparse(image_url).hostname,
                )
            return content
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error creating UPI QR: "
                "code=%s status=%d order_id=%s",
                e.code, e.status_code, order_id,
            )
            return api_error_response(
                e.message,
                e.code,
                e.status_code,
                {"order_id": order_id, **(e.payload or {})},
            )
        except Exception as e:
            logger.error(
                "Unexpected error creating UPI QR: %s "
                "order_id=%s",
                type(e).__name__, order_id,
            )
            return unexpected_error_response(
                e, "create UPI intent payment with QR",
            )
