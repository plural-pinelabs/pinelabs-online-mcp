"""
Pydantic models for Pine Labs Checkout Order (Generate Checkout Link) API.

Matches the OpenAPI spec from generate-checkout-link.md.
All models use `exclude_none=True` on serialization so only
provided fields are sent to the Pine Labs API.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from pkg.pinelabs.models.payment_links import Address, Amount


class IntegrationMode(str, Enum):
    REDIRECT = "REDIRECT"
    IFRAME = "IFRAME"
    SDK = "SDK"


class CheckoutAllowedPaymentMethod(str, Enum):
    CARD = "CARD"
    UPI = "UPI"
    POINTS = "POINTS"
    NETBANKING = "NETBANKING"
    WALLET = "WALLET"
    CREDIT_EMI = "CREDIT_EMI"
    DEBIT_EMI = "DEBIT_EMI"
    BNPL = "BNPL"


class CheckoutCustomer(BaseModel):
    """Customer information for checkout orders.

    Unlike payment links, checkout orders do not require
    at least one of email_id or mobile_number.
    """

    email_id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Customer email address (e.g., kevin.bob@example.com)",
    )
    first_name: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Customer first name",
    )
    last_name: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Customer last name",
    )
    customer_id: Optional[str] = Field(
        default=None,
        max_length=19,
        description="Unique customer identifier in Pine Labs database",
    )
    mobile_number: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=20,
        description="Customer mobile number (digits only, e.g., 9876543210)",
    )
    country_code: Optional[str] = Field(
        default=None,
        max_length=5,
        description="Country code for mobile number (e.g., 91). Defaults to 91 if not provided.",
    )
    billing_address: Optional[Address] = Field(
        default=None, description="Customer billing address"
    )
    shipping_address: Optional[Address] = Field(
        default=None, description="Customer shipping address"
    )


class CartItem(BaseModel):
    """Single item in the checkout cart."""

    item_id: Optional[str] = Field(
        default=None, description="Unique identifier of the item (e.g., cart_id_1)"
    )
    item_name: Optional[str] = Field(
        default=None, description="Name of the item (e.g., T Shirt)"
    )
    item_description: Optional[str] = Field(
        default=None, description="Description of the item"
    )
    item_image_url: Optional[str] = Field(
        default=None, description="Image URL of the item (24x24 recommended)"
    )
    item_original_unit_price: Optional[str] = Field(
        default=None, description="Original unit price of the item"
    )
    item_discounted_unit_price: Optional[str] = Field(
        default=None, description="Discounted unit price of the item"
    )
    item_quantity: Optional[str] = Field(
        default=None, description="Number of items (e.g., 2)"
    )
    item_currency: Optional[str] = Field(
        default=None, description="Currency for the item (e.g., INR)"
    )


class CartDetails(BaseModel):
    """Cart details for checkout display."""

    cart_items: Optional[list[CartItem]] = Field(
        default=None, description="List of cart items"
    )


class PurchaseDetails(BaseModel):
    """Container for customer, merchant metadata, and cart details."""

    customer: Optional[CheckoutCustomer] = Field(
        default=None, description="Customer information"
    )
    merchant_metadata: Optional[dict[str, str]] = Field(
        default=None, description="Custom key-value metadata (max 10 pairs, 256 chars each)"
    )
    cart_details: Optional[CartDetails] = Field(
        default=None, description="Cart details for display during checkout"
    )


class CheckoutProduct(BaseModel):
    """Product details for EMI orders."""

    product_code: str = Field(
        ..., description="Unique code of the product (e.g., redm_1)"
    )
    product_amount: Optional[Amount] = Field(
        default=None, description="Product amount object with value and currency"
    )


class CreateCheckoutOrderRequest(BaseModel):
    """
    Request body for creating a Pine Labs checkout order (generate checkout link).

    Required fields: merchant_order_reference, order_amount
    """

    merchant_order_reference: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique identifier for the order request (e.g., 112345)",
    )
    order_amount: Amount = Field(
        ..., description="Transaction amount object with value (in paisa) and currency"
    )
    integration_mode: Optional[IntegrationMode] = Field(
        default=None, description="Integration mode: REDIRECT (default), IFRAME, or SDK"
    )
    pre_auth: Optional[bool] = Field(
        default=None, description="Whether pre-authorization is required (default: false)"
    )
    allowed_payment_methods: Optional[list[CheckoutAllowedPaymentMethod]] = Field(
        default=None, description="Payment methods to offer: CARD, UPI, POINTS, NETBANKING, WALLET, CREDIT_EMI, DEBIT_EMI, BNPL"
    )
    notes: Optional[str] = Field(
        default=None, description="Note to show against the order (e.g., Order1)"
    )
    callback_url: Optional[str] = Field(
        default=None, description="URL to redirect customers on success"
    )
    failure_callback_url: Optional[str] = Field(
        default=None, description="URL to redirect customers on failure"
    )
    purchase_details: Optional[PurchaseDetails] = Field(
        default=None, description="Customer, metadata, cart, and account details"
    )
    product: Optional[list[CheckoutProduct]] = Field(
        default=None, description="Product details (mandatory for EMI orders)"
    )
