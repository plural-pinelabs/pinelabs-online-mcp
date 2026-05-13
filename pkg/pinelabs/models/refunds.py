"""
Pydantic models for Pine Labs Refund API.

Matches the OpenAPI spec from refund-integration.md.
All models use `exclude_none=True` on serialization so only
provided fields are sent to the Pine Labs API.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class RefundAmount(BaseModel):
    """Refund amount object."""

    value: int = Field(
        ...,
        ge=100,
        le=100_000_000,
        description="Amount in paisa (e.g., 50000 = Rs.500). Min: 100, Max: 100000000",
    )
    currency: str = Field(
        default="INR",
        pattern=r"^[A-Z]{3}$",
        description="Three-letter ISO currency code (e.g., INR)",
    )


class RefundProductAmount(BaseModel):
    """Product amount for a refund line item."""

    value: int = Field(
        ...,
        ge=100,
        le=100_000_000,
        description="Product refund amount in paisa. Min: 100, Max: 100000000",
    )
    currency: str = Field(
        default="INR",
        pattern=r"^[A-Z]{3}$",
        description="Three-letter ISO currency code (e.g., INR)",
    )


class RefundProduct(BaseModel):
    """Product details for multi-cart partial refunds."""

    product_code: str = Field(
        ...,
        description="Unique product identifier (e.g., SM-S908EZKP)",
    )
    product_amount: Optional[RefundProductAmount] = Field(
        default=None,
        description="Product refund amount object",
    )
    product_imei: Optional[str] = Field(
        default=None,
        description=(
            "The unique IMEI number of the product. "
            "Provide the IMEI of the product that needs to be unblocked."
        ),
    )


class SplitAmount(BaseModel):
    """Amount object within a split detail."""

    value: int = Field(
        ...,
        ge=100,
        le=100_000_000,
        description="Split refund amount in paisa. Min: 100, Max: 100000000",
    )
    currency: str = Field(
        default="INR",
        pattern=r"^[A-Z]{3}$",
        description="Three-letter ISO currency code (e.g., INR)",
    )


class SplitDetail(BaseModel):
    """Individual split settlement detail for a refund."""

    parent_order_split_settlement_id: str = Field(
        ...,
        max_length=50,
        description=(
            "Unique identifier of the parent split settlement in the Plural database. "
            "Example: v1-250513063000-aa-UBAnaE-ss-g"
        ),
    )
    split_merchant_id: str = Field(
        ...,
        description="Unique identifier of your partner merchant in the Plural database",
    )
    merchant_settlement_reference: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique identifier entered while creating an order in split",
    )
    amount: Optional[SplitAmount] = Field(
        default=None,
        description="Split refund amount object",
    )
    status: Optional[Literal["DO_NOT_RECOVER"]] = Field(
        default=None,
        description=(
            "Indicate whether the settlement is to be recovered or not. "
            "Accepted values: DO_NOT_RECOVER (refund not recovered from merchant settlement) "
            "or blank (refund recovered from merchant settlement)."
        ),
    )


class SplitInfo(BaseModel):
    """Split settlement information for a refund."""

    split_type: Literal["AMOUNT"] = Field(
        ...,
        description="Type of split. Must be 'AMOUNT'.",
    )
    split_details: Optional[list[SplitDetail]] = Field(
        default=None,
        description="Array of split settlement details",
    )


class CreateRefundRequest(BaseModel):
    """
    Request body for creating a Pine Labs refund.

    Required fields: merchant_order_reference, order_amount
    """

    merchant_order_reference: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique identifier for this refund (1-50 chars)",
    )
    order_amount: RefundAmount = Field(
        ...,
        description="Refund amount object with value (in paisa) and currency",
    )
    merchant_metadata: Optional[dict[str, str]] = Field(
        default=None,
        description="Key-value pairs for additional information",
    )
    products: Optional[list[RefundProduct]] = Field(
        default=None,
        description=(
            "Product details array. Mandatory for multi-cart partial refunds. "
            "For partial refunds, specify the IMEI number that needs to be blocked."
        ),
    )
    split_info: Optional[SplitInfo] = Field(
        default=None,
        description=(
            "Split settlement information. Mandatory for split settlements. "
            "Ensure split settlements are enabled for your account."
        ),
    )

    @field_validator("merchant_metadata")
    @classmethod
    def validate_merchant_metadata(
        cls, v: dict[str, str] | None
    ) -> dict[str, str] | None:
        if v is None:
            return v
        if len(v) > 20:
            raise ValueError(
                "merchant_metadata must have at most 20 entries."
            )
        for key, value in v.items():
            if len(key) > 256:
                raise ValueError(
                    "merchant_metadata keys must be at most 256 characters."
                )
            if len(value) > 256:
                raise ValueError(
                    "merchant_metadata values must be at most 256 characters."
                )
        return v
