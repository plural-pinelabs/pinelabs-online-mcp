"""
Pydantic models for Pine Labs Subscription APIs (Plans, Subscriptions, Presentations).

Covers request bodies for all subscription endpoints.
All models use `exclude_none=True` on serialization so only
provided fields are sent to the Pine Labs API.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from pkg.pinelabs.models.payment_links import Amount


class PlanFrequency(str, Enum):
    """Supported billing frequencies for subscription plans."""
    DAY = "Day"
    WEEK = "Week"
    MONTH = "Month"
    YEAR = "Year"
    BI_MONTHLY = "Bi-Monthly"
    QUARTERLY = "Quarterly"
    HALF_YEARLY = "Half-Yearly"
    AS = "AS"
    OT = "OT"


class SubscriptionIntegrationMode(str, Enum):
    """Integration modes for creating subscriptions."""
    SEAMLESS = "SEAMLESS"
    REDIRECT = "REDIRECT"


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------

class CreatePlanRequest(BaseModel):
    """Request body for POST /v1/public/plans."""
    plan_name: str = Field(..., max_length=100, description="Unique reference for the plan you want to create")
    frequency: PlanFrequency = Field(..., description="Frequency of recurring transactions for this plan")
    amount: Amount = Field(..., description="Amount details for recurring transactions")
    max_limit_amount: Amount = Field(..., description="Maximum limit amount details for the plan")
    end_date: str = Field(..., description="ISO 8601 UTC date when the plan expires and can no longer be used for new subscriptions")
    merchant_plan_reference: str = Field(..., min_length=1, max_length=50, description="Unique merchant plan reference (A-Z, a-z, -, _)")
    plan_description: Optional[str] = Field(default=None, max_length=500, description="Corresponding description for the plan")
    trial_period_in_days: Optional[int] = Field(default=None, ge=0, description="Duration of the trial period in days")
    start_date: Optional[str] = Field(default=None, description="ISO 8601 UTC date when the plan is active and available for use")
    initial_debit_amount: Optional[Amount] = Field(default=None, description="Amount debited at subscription creation before the recurring payment cycle starts")
    auto_debit_ot: Optional[bool] = Field(default=None, description="Whether auto-debit is enabled for one-time payments under the plan")
    merchant_metadata: Optional[dict[str, str]] = Field(default=None, description="Key-value pairs for additional info (max 10 pairs, 256 chars each)")


class UpdatePlanRequest(BaseModel):
    """Request body for PATCH /ps/v1/public/plans/{plan_id}."""
    plan_name: Optional[str] = Field(default=None, max_length=100, description="Updated plan name")
    plan_description: Optional[str] = Field(default=None, max_length=500, description="Updated plan description")
    status: Optional[str] = Field(default=None, description="Updated plan status")
    end_date: Optional[str] = Field(default=None, description="Updated end date (ISO 8601 UTC)")
    max_limit_amount: Optional[Amount] = Field(default=None, description="Updated max limit amount")
    merchant_metadata: Optional[dict[str, str]] = Field(default=None, description="Updated custom metadata")


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------

class BankAccount(BaseModel):
    """Bank account details for TPV-enabled subscriptions."""
    account_number: str = Field(..., max_length=50, description="Bank account number")
    name: str = Field(..., max_length=100, description="Account holder name")
    ifsc: str = Field(..., max_length=11, description="IFSC code")


class CreateSubscriptionRequest(BaseModel):
    """Request body for POST /ps/v1/public/subscriptions."""
    merchant_subscription_reference: str = Field(..., max_length=50, description="Unique merchant subscription reference")
    plan_id: str = Field(..., max_length=50, description="Plan ID to subscribe to")
    start_date: str = Field(..., description="Subscription start date (ISO 8601 UTC)")
    end_date: str = Field(..., description="Subscription end date (ISO 8601 UTC)")
    customer_id: str = Field(..., max_length=50, description="Customer ID in Pine Labs database")
    integration_mode: SubscriptionIntegrationMode = Field(..., description="Integration mode: SEAMLESS or REDIRECT")
    payment_mode: Optional[str] = Field(default=None, description="Payment mode (e.g., UPI)")
    allowed_payment_methods: Optional[list[str]] = Field(default=None, description="Allowed payment methods (e.g., ['UPI'])")
    redirect_url: Optional[str] = Field(default=None, max_length=500, description="Redirect URL after subscription created")
    failure_callback_url: Optional[str] = Field(default=None, max_length=500, description="Failure callback URL")
    callback_url: Optional[str] = Field(default=None, max_length=500, description="Success callback URL")
    quantity: Optional[int] = Field(default=None, ge=0, description="Subscription quantity")
    is_tpv_enabled: Optional[bool] = Field(default=None, description="Enable TPV (Third Party Validation)")
    bank_account: Optional[BankAccount] = Field(default=None, description="Bank account for TPV")
    enable_notification: Optional[bool] = Field(default=None, description="Enable pre-debit notification")
    merchant_metadata: Optional[dict[str, str]] = Field(default=None, description="Custom key-value metadata")


class UpdateSubscriptionRequest(BaseModel):
    """Request body for PATCH /ps/v1/public/subscriptions/{subscription_id}."""
    reason: str = Field(..., max_length=500, description="Reason for updating the subscription")
    new_plan_id: Optional[str] = Field(default=None, max_length=50, description="New plan ID to switch to")
    new_end_date: Optional[str] = Field(default=None, description="New end date (ISO 8601 UTC)")

    @model_validator(mode="after")
    def _require_at_least_one_update(self) -> "UpdateSubscriptionRequest":
        if self.new_plan_id is None and self.new_end_date is None:
            raise ValueError("At least one of 'new_plan_id' or 'new_end_date' must be provided")
        return self


# ---------------------------------------------------------------------------
# Presentations
# ---------------------------------------------------------------------------

class CreatePresentationRequest(BaseModel):
    """Request body for POST /ps/v1/public/subscriptions/{subscription_id}/presentations."""
    due_date: str = Field(..., description="Payment due date (ISO 8601 UTC)")
    amount: Amount = Field(..., description="Presentation amount")
    merchant_presentation_reference: str = Field(..., max_length=50, description="Unique merchant presentation reference")


# ---------------------------------------------------------------------------
# Notification, Debit, Merchant Retry
# ---------------------------------------------------------------------------

class SubscriptionNotificationRequest(BaseModel):
    """Request body for POST /ps/v1/public/subscriptions/notify."""
    subscription_id: str = Field(..., max_length=50, description="Subscription ID")
    due_date: str = Field(..., description="Payment due date (ISO 8601 UTC)")
    amount: Amount = Field(..., description="Notification amount")
    merchant_presentation_reference: str = Field(..., max_length=50, description="Merchant presentation reference")
    is_merchant_retry: Optional[bool] = Field(default=None, description="Whether this is a merchant retry notification")


class CreateDebitRequest(BaseModel):
    """Request body for POST /ps/v1/public/subscriptions/execute."""
    presentation_id: Optional[str] = Field(default=None, max_length=50, description="Presentation ID from Pine Labs")
    merchant_presentation_reference: Optional[str] = Field(default=None, max_length=50, description="Merchant presentation reference")
    is_merchant_retry: Optional[str] = Field(default=None, description="Whether merchant controls retry ('true'/'false')")

    @model_validator(mode="after")
    def _require_at_least_one_identifier(self) -> "CreateDebitRequest":
        if self.presentation_id is None and self.merchant_presentation_reference is None:
            raise ValueError("At least one of 'presentation_id' or 'merchant_presentation_reference' must be provided")
        return self


class CreateMerchantRetryRequest(BaseModel):
    """Request body for POST /ps/v1/mandate/merchant-retry."""
    presentation_id: Optional[str] = Field(default=None, max_length=50, description="Presentation ID from Pine Labs")
    merchant_presentation_reference: Optional[str] = Field(default=None, max_length=50, description="Merchant presentation reference")

    @model_validator(mode="after")
    def _require_at_least_one_identifier(self) -> "CreateMerchantRetryRequest":
        if self.presentation_id is None and self.merchant_presentation_reference is None:
            raise ValueError("At least one of 'presentation_id' or 'merchant_presentation_reference' must be provided")
        return self
