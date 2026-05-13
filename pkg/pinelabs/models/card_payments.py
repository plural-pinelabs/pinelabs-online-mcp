"""
Pydantic models for Pine Labs Card Payment, OTP, and Card Details APIs.

Covers:
- Create Card Payment (POST /pay/v1/orders/{order_id}/payments)
- Get Card Details (POST /pay/v1/getCardDetails)
- Generate / Submit / Resend OTP
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class PaymentAmount(BaseModel):
    """Payment amount in paisa."""

    value: int = Field(
        ...,
        ge=100,
        le=100_000_000,
        description="Amount in paisa (e.g., 1100 = Rs.11). Min: 100, Max: 100000000",
    )
    currency: str = Field(
        default="INR",
        description="Three-letter ISO currency code (e.g., INR)",
    )


class TokenTxnType(str, Enum):
    ALT_TOKEN = "ALT_TOKEN"
    NETWORK_TOKEN = "NETWORK_TOKEN"
    ISSUER_TOKEN = "ISSUER_TOKEN"


class CardData(BaseModel):
    """Card data for direct or tokenized card payment."""

    card_number: Optional[str] = Field(
        default=None, min_length=13, max_length=19,
        description="Full card number (13-19 digits)",
    )
    card_expiry_month: Optional[str] = Field(
        default=None, min_length=2, max_length=2,
        description="Card expiry month (MM)",
    )
    card_expiry_year: Optional[str] = Field(
        default=None, min_length=4, max_length=4,
        description="Card expiry year (YYYY)",
    )
    card_cvv: Optional[str] = Field(
        default=None, min_length=3, max_length=4,
        description="Card CVV (3-4 digits)",
    )
    card_holder_name: Optional[str] = Field(
        default=None, max_length=100,
        description="Cardholder name as on card",
    )
    save: Optional[bool] = Field(
        default=None,
        description="Whether to save card for future transactions",
    )
    token_txn_type: Optional[TokenTxnType] = Field(
        default=None,
        description="Token transaction type: ALT_TOKEN, NETWORK_TOKEN, ISSUER_TOKEN",
    )
    token_value: Optional[str] = Field(
        default=None, max_length=100,
        description="Token value for tokenized transactions",
    )
    token_cryptogram: Optional[str] = Field(
        default=None, max_length=200,
        description="Token cryptogram for tokenized transactions",
    )
    last4_digit: Optional[str] = Field(
        default=None, min_length=4, max_length=4,
        description="Last 4 digits of the card",
    )
    token_expiry_month: Optional[str] = Field(
        default=None, min_length=2, max_length=2,
        description="Token expiry month (MM)",
    )
    token_expiry_year: Optional[str] = Field(
        default=None, min_length=4, max_length=4,
        description="Token expiry year (YYYY)",
    )


class PaymentOption(BaseModel):
    """Payment option containing card data."""

    card_data: CardData


class CardPayment(BaseModel):
    """Single payment entry within the payments array."""

    merchant_payment_reference: Optional[str] = Field(
        default=None, max_length=50,
        description="Unique merchant payment reference (max 50 chars)",
    )
    payment_amount: PaymentAmount
    payment_method: str = Field(
        default="CARD", description="Payment method (CARD)",
    )
    payment_option: PaymentOption


class CreateCardPaymentRequest(BaseModel):
    """Request body for Create Card Payment API."""

    payments: list[CardPayment] = Field(
        ..., min_length=1, max_length=1,
        description="Array of payment objects (exactly one for card payment)",
    )

    @model_validator(mode="after")
    def validate_card_or_token(self) -> "CreateCardPaymentRequest":
        card = self.payments[0].payment_option.card_data

        has_direct = card.card_number is not None
        has_token = card.token_value is not None

        if not has_direct and not has_token:
            raise ValueError(
                "Either card_number (direct card) or token_value "
                "(tokenized payment) must be provided."
            )

        if has_direct and has_token:
            raise ValueError(
                "Provide either card_number or token_value, not both."
            )

        if has_direct:
            if not card.card_expiry_month or not card.card_expiry_year:
                raise ValueError(
                    "card_expiry_month and card_expiry_year are required "
                    "for direct card payments."
                )

        if has_token:
            missing = []
            if not card.last4_digit:
                missing.append("last4_digit")
            if not card.token_expiry_month:
                missing.append("token_expiry_month")
            if not card.token_expiry_year:
                missing.append("token_expiry_year")
            if not card.token_cryptogram:
                missing.append("token_cryptogram")
            if not card.token_txn_type:
                missing.append("token_txn_type")
            if missing:
                raise ValueError(
                    f"Token-based payment requires: {', '.join(missing)}"
                )
            if (
                card.token_txn_type == TokenTxnType.ALT_TOKEN
                and not card.card_cvv
            ):
                raise ValueError(
                    "card_cvv is required for ALT_TOKEN transactions."
                )

        return self


# --- Get Card Details ---

class CardDetailEntry(BaseModel):
    """Single card_number entry for Get Card Details request."""

    card_number: str = Field(
        ..., min_length=13, max_length=19,
        description="Card number to look up (13-19 digits)",
    )


class GetCardDetailsRequest(BaseModel):
    """Request body for Get Card Details API."""

    card_details: list[CardDetailEntry] = Field(
        ..., min_length=1, max_length=1,
        description="Array of card detail objects",
    )


# --- OTP ---

class GenerateOtpRequest(BaseModel):
    """Request body for Generate OTP API."""

    payment_id: str = Field(
        ..., max_length=50, description="Payment ID from Pine Labs",
    )


class SubmitOtpRequest(BaseModel):
    """Request body for Submit OTP API."""

    payment_id: str = Field(
        ..., max_length=50, description="Payment ID from Pine Labs",
    )
    otp: str = Field(
        ..., min_length=4, max_length=8, pattern=r"^\d{4,8}$",
        description="OTP received on registered mobile (4-8 digits)",
    )


class ResendOtpRequest(BaseModel):
    """Request body for Resend OTP API."""

    payment_id: str = Field(
        ..., max_length=50, description="Payment ID from Pine Labs",
    )
