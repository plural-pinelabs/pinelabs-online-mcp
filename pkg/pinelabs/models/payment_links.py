"""
Pydantic models for Pine Labs Payment Link API.

Matches the OpenAPI spec from payment-link-create.md.
All models use `exclude_none=True` on serialization so only
provided fields are sent to the Pine Labs API.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Amount(BaseModel):
    """Payment amount object."""

    value: int = Field(
        ...,
        ge=100,
        le=100_000_000,
        description="Amount in paisa (e.g., 50000 = Rs.500). Min: 100, Max: 100000000",
    )
    currency: str = Field(
        default="INR",
        description="Three-letter ISO currency code (e.g., INR)",
    )


class AddressType(str, Enum):
    HOME = "HOME"
    WORK = "WORK"
    OTHER = "OTHER"


class Address(BaseModel):
    """Billing or shipping address."""

    address1: Optional[str] = Field(
        default=None, max_length=100, description="Address line 1"
    )
    address2: Optional[str] = Field(
        default=None, max_length=100, description="Address line 2"
    )
    address3: Optional[str] = Field(
        default=None, max_length=100, description="Address line 3"
    )
    pincode: Optional[str] = Field(
        default=None, min_length=3, max_length=11, description="Pincode"
    )
    city: Optional[str] = Field(
        default=None, max_length=50, description="City"
    )
    state: Optional[str] = Field(
        default=None, max_length=50, description="State"
    )
    country: Optional[str] = Field(
        default=None, max_length=50, description="Country"
    )
    full_name: Optional[str] = Field(
        default=None, max_length=100, description="Customer full name"
    )
    address_type: Optional[AddressType] = Field(
        default=None, description="Address type: HOME, WORK, or OTHER"
    )
    address_category: Optional[str] = Field(
        default=None, max_length=20, description="Address category (e.g., billing, shipping)"
    )


class Customer(BaseModel):
    """Customer information."""

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
        description="Country code for mobile number (e.g., +91). Defaults to +91 if not provided.",
    )
    billing_address: Optional[Address] = Field(
        default=None, description="Customer billing address"
    )
    shipping_address: Optional[Address] = Field(
        default=None, description="Customer shipping address"
    )
    
    @model_validator(mode="after")
    def check_email_or_mobile(self) -> "Customer":
        """Pine Labs API requires at least one of email_id or mobile_number."""
        if not self.email_id and not self.mobile_number:
            raise ValueError(
                "At least one of 'email_id' or 'mobile_number' must be provided."
            )
        return self


class AllowedPaymentMethod(str, Enum):
    CARD = "CARD"
    UPI = "UPI"
    POINTS = "POINTS"
    NETBANKING = "NETBANKING"
    WALLET = "WALLET"
    CREDIT_EMI = "CREDIT_EMI"
    DEBIT_EMI = "DEBIT_EMI"


class ProductDetail(BaseModel):
    """Product details associated with the payment."""

    product_code: str = Field(
        ..., description="Unique product identifier (e.g., redmi_10)"
    )
    product_amount: Optional[Amount] = Field(
        default=None, description="Product amount"
    )
    product_coupon_discount_amount: Optional[Amount] = Field(
        default=None, description="Product coupon discount amount"
    )


class CreatePaymentLinkRequest(BaseModel):
    """
    Request body for creating a Pine Labs payment link.

    Required fields: amount, merchant_payment_link_reference, customer
    """

    amount: Amount = Field(
        ..., description="Payment amount object with value (in paisa) and currency"
    )
    merchant_payment_link_reference: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique identifier for the payment link request (1-50 chars, A-Z, a-z, -, _)",
    )
    customer: Customer = Field(
        ..., description="Customer information"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description for the payment (e.g., Payment for Order #12345)",
    )
    expire_by: Optional[str] = Field(
        default=None,
        description="Expiration timestamp in ISO 8601 format (e.g., 2025-03-21T08:29Z). Max 180 days from now.",
    )
    allowed_payment_methods: Optional[list[AllowedPaymentMethod]] = Field(
        default=None,
        description="Payment methods to offer: CARD, UPI, POINTS, NETBANKING, WALLET, CREDIT_EMI, DEBIT_EMI",
    )
    product_details: Optional[list[ProductDetail]] = Field(
        default=None, description="List of products associated with the payment"
    )
    cart_coupon_discount_amount: Optional[Amount] = Field(
        default=None, description="Cart-level coupon discount amount"
    )
    merchant_metadata: Optional[dict[str, str]] = Field(
        default=None, description="Custom key-value metadata"
    )
