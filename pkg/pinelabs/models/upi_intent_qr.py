"""
Pydantic models for Pine Labs pay order creation + UPI intent QR payment APIs.

These models cover the subset of fields needed by the MCP tool that:
1. Creates an order via /pay/v1/orders
2. Creates a UPI intent payment with QR via /pay/v1/orders/{order_id}/payments
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from pkg.pinelabs.models.checkout_orders import PurchaseDetails
from pkg.pinelabs.models.payment_links import Amount


class OrderAllowedPaymentMethod(str, Enum):
    """Payment methods accepted by the pay order creation API."""

    CARD = "CARD"
    UPI = "UPI"
    POINTS = "POINTS"
    NETBANKING = "NETBANKING"
    WALLET = "WALLET"
    CREDIT_EMI = "CREDIT_EMI"
    DEBIT_EMI = "DEBIT_EMI"


class CreatePayOrderRequest(BaseModel):
    """Request body for POST /pay/v1/orders."""

    merchant_order_reference: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique identifier for the order request",
    )
    order_amount: Amount = Field(
        ..., description="Transaction amount object with value in paisa and currency"
    )
    pre_auth: Optional[bool] = Field(default=None)
    allowed_payment_methods: Optional[list[OrderAllowedPaymentMethod]] = Field(
        default=None
    )
    notes: Optional[str] = Field(default=None)
    callback_url: Optional[str] = Field(default=None)
    failure_callback_url: Optional[str] = Field(default=None)
    purchase_details: Optional[PurchaseDetails] = Field(default=None)


class UpiTransactionMode(str, Enum):
    """Supported UPI transaction modes for this tool."""

    INTENT = "INTENT"


class UpiPaymentMethod(str, Enum):
    """Supported payment method for the QR flow."""

    UPI = "UPI"


class UpiDetails(BaseModel):
    """UPI configuration for the payment option."""

    txn_mode: UpiTransactionMode = Field(default=UpiTransactionMode.INTENT)
    upi_qr: bool = Field(default=True)


class UpiPaymentOption(BaseModel):
    """Container for UPI-specific payment options."""

    upi_details: UpiDetails = Field(default_factory=UpiDetails)


class UpiIntentQrPayment(BaseModel):
    """A single payment entry for UPI intent QR flow."""

    merchant_payment_reference: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique payment reference sent by merchant",
    )
    payment_method: UpiPaymentMethod = Field(default=UpiPaymentMethod.UPI)
    payment_amount: Amount = Field(...)
    payment_option: UpiPaymentOption = Field(default_factory=UpiPaymentOption)


class CreateUpiIntentQrPaymentRequest(BaseModel):
    """Request body for POST /pay/v1/orders/{order_id}/payments."""

    payments: list[UpiIntentQrPayment] = Field(min_length=1)
