"""
Pine Labs Payout tools.

Defines tools for the full payout lifecycle via /payouts/v3/:
- create_payout: Create a new bank payout
- get_payout_payments: List/filter payouts with pagination
- get_payout_balance: Get funding account balance
- update_payout: Update scheduled payout date
- cancel_payout: Cancel a scheduled payout
"""

import json
import logging
import re
from datetime import datetime
from typing import Optional

from fastmcp import FastMCP

from pkg.pinelabs.client import PineLabsAPIError, PineLabsClient
from pkg.pinelabs.utils.errors import (
    api_error_response,
    unexpected_error_response,
    validation_error_response,
)
from pkg.pinelabs.utils.validators import validate_resource_id
from pkg.pinelabs import routes

logger = logging.getLogger("pinelabs-mcp-server.payouts")

_VALID_MODES = frozenset({"UPI", "IMPS", "NEFT", "RTGS"})
_VALID_STATUSES = frozenset({
    "SCHEDULED", "PENDING", "PROCESSING",
    "PROCESSED", "SUCCESS", "FAILED",
})

_CLIENT_REF_RE = re.compile(r"^[^\s]{1,40}$")
_PAYEE_NAME_RE = re.compile(r"^[a-zA-Z ]{1,40}$")
_REMARKS_RE = re.compile(r"^[a-zA-Z0-9\- ]{1,50}$")
_PHONE_RE = re.compile(r"^\d{10}$")
_ACCOUNT_RE = re.compile(r"^\d{9,18}$")
_BRANCH_CODE_RE = re.compile(r"^[A-Z0-9]{1,11}$")


def _validate_date_range(
    date_from: str, date_to: str
) -> str | None:
    """Validate date range as ISO 8601, logical order, max 60 days."""
    try:
        dt_from = datetime.fromisoformat(date_from)
        dt_to = datetime.fromisoformat(date_to)
    except (ValueError, TypeError):
        return (
            "dateFrom and dateTo must be valid ISO 8601 timestamps."
        )
    if dt_to < dt_from:
        return "dateTo must not be before dateFrom."
    if (dt_to - dt_from).total_seconds() > 60 * 86400:
        return "Date range must not exceed 60 days."
    return None


def register_payout_tools(
    mcp: FastMCP, client: PineLabsClient
) -> None:
    """Register all payout tools on the FastMCP server."""

    @mcp.tool(
        name="create_payout",
        description=(
            "Create a new bank payout via Pine Labs. Initiates a "
            "fund transfer to a payee's bank account or UPI. "
            "Amount value is in the smallest currency unit "
            "(e.g. paisa). For IMPS/NEFT/RTGS modes, "
            "account_number and branch_code are required."
        ),
    )
    async def create_payout(
        client_reference_id: str,
        payee_name: str,
        amount_value: int,
        mode: str,
        remarks: str,
        currency: str = "INR",
        email: Optional[str] = None,
        phone: Optional[str] = None,
        account_number: Optional[str] = None,
        branch_code: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> str:
        """Create a new bank payout.

        Args:
            client_reference_id: Unique reference (1-40 chars,
                no spaces).
            payee_name: Payee name (1-40 chars, letters and spaces).
            amount_value: Amount in smallest currency unit
                (e.g. paisa).
            mode: Transfer mode - UPI, IMPS, NEFT, or RTGS.
            remarks: Transfer remarks (1-50 chars,
                alphanumeric/dash/space).
            currency: Three-letter ISO currency code (default INR).
            email: Payee email address.
            phone: Payee phone number (10 digits).
            account_number: Payee bank account number (9-18 digits).
                Required for IMPS, NEFT, RTGS modes.
            branch_code: IFSC code (max 11 chars, alphanumeric).
                Required for IMPS, NEFT, RTGS modes.
            idempotency_key: Optional idempotency key.
        """
        if not client_reference_id or not _CLIENT_REF_RE.match(
            client_reference_id
        ):
            return validation_error_response(
                "client_reference_id must be 1-40 characters with "
                "no spaces."
            )

        if not payee_name or not _PAYEE_NAME_RE.match(payee_name):
            return validation_error_response(
                "payee_name must be 1-40 characters, letters and "
                "spaces only."
            )

        mode_upper = mode.upper() if mode else ""
        if mode_upper not in _VALID_MODES:
            return validation_error_response(
                "mode must be one of: "
                f"{', '.join(sorted(_VALID_MODES))}."
            )

        if not remarks or not _REMARKS_RE.match(remarks):
            return validation_error_response(
                "remarks must be 1-50 characters, alphanumeric, "
                "dashes, and spaces only."
            )

        if not isinstance(amount_value, int) or amount_value <= 0:
            return validation_error_response(
                "amount_value must be a positive integer."
            )

        if phone and not _PHONE_RE.match(phone):
            return validation_error_response(
                "phone must be exactly 10 digits."
            )

        if mode_upper in {"IMPS", "NEFT", "RTGS"}:
            if not account_number:
                return validation_error_response(
                    f"account_number is required for {mode_upper} "
                    "mode."
                )
            if not branch_code:
                return validation_error_response(
                    f"branch_code is required for {mode_upper} "
                    "mode."
                )

        if account_number and not _ACCOUNT_RE.match(account_number):
            return validation_error_response(
                "account_number must be 9-18 digits."
            )

        if branch_code and not _BRANCH_CODE_RE.match(
            branch_code.upper()
        ):
            return validation_error_response(
                "branch_code must be max 11 alphanumeric "
                "characters (IFSC format)."
            )

        payload: dict = {
            "clientReferenceId": client_reference_id,
            "payeeName": payee_name,
            "amount": {
                "currency": currency,
                "value": amount_value,
            },
            "mode": mode_upper,
            "remarks": remarks,
        }
        if email:
            payload["email"] = email
        if phone:
            payload["phone"] = phone
        if account_number:
            payload["accountNumber"] = account_number
        if branch_code:
            payload["branchCode"] = branch_code.upper()

        try:
            logger.info(
                "Creating payout: ref=%s mode=%s amount=%s",
                client_reference_id,
                mode_upper,
                amount_value,
            )
            response = await client.post(
                routes.PAYOUT_CREATE, payload, idempotency_key
            )
            return json.dumps(response, indent=2)

        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error("Unexpected error creating payout: %s", e)
            return unexpected_error_response(e, "creating payout")

    @mcp.tool(
        name="get_payout_payments",
        description=(
            "List and filter payouts from Pine Labs. Returns "
            "payout records with pagination. All filter "
            "parameters are optional. Maximum date range is 60 "
            "days. Count range is 1-20."
        ),
    )
    async def get_payout_payments(
        payment_reference_id: Optional[str] = None,
        client_reference_id: Optional[str] = None,
        request_reference_id: Optional[str] = None,
        bank_transaction_reference_id: Optional[str] = None,
        mode: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        status: Optional[str] = None,
        page: Optional[int] = None,
        count: Optional[int] = None,
    ) -> str:
        """List and filter payouts.

        Args:
            payment_reference_id: Filter by payment reference ID.
            client_reference_id: Filter by client reference ID.
            request_reference_id: Filter by request reference ID.
            bank_transaction_reference_id: Filter by bank txn ref.
            mode: Filter by mode (UPI, IMPS, NEFT, RTGS).
            date_from: Start date in ISO 8601 format.
            date_to: End date in ISO 8601 format.
            status: Filter by status (SCHEDULED, PENDING,
                PROCESSING, PROCESSED, SUCCESS, FAILED).
            page: Page number (starts at 1).
            count: Records per page (1-20).
        """
        if mode and mode.upper() not in _VALID_MODES:
            return validation_error_response(
                "mode must be one of: "
                f"{', '.join(sorted(_VALID_MODES))}."
            )

        if status and status.upper() not in _VALID_STATUSES:
            return validation_error_response(
                "status must be one of: "
                f"{', '.join(sorted(_VALID_STATUSES))}."
            )

        if date_from and date_to:
            date_err = _validate_date_range(date_from, date_to)
            if date_err:
                return validation_error_response(date_err)

        if page is not None and page < 1:
            return validation_error_response("page must be >= 1.")
        if count is not None and (count < 1 or count > 20):
            return validation_error_response(
                "count must be between 1 and 20."
            )

        params: dict[str, str] = {}
        if payment_reference_id:
            params["paymentReferenceId"] = payment_reference_id
        if client_reference_id:
            params["clientReferenceId"] = client_reference_id
        if request_reference_id:
            params["requestReferenceId"] = request_reference_id
        if bank_transaction_reference_id:
            params["bankTransactionReferenceId"] = (
                bank_transaction_reference_id
            )
        if mode:
            params["mode"] = mode.upper()
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        if status:
            params["status"] = status.upper()
        if page is not None:
            params["page"] = str(page)
        if count is not None:
            params["count"] = str(count)

        try:
            logger.info("Fetching payout payments with filters")
            response = await client.get(
                routes.PAYOUT_LIST, params=params
            )
            return json.dumps(response, indent=2)

        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching payout payments: %s", e
            )
            return unexpected_error_response(
                e, "fetching payout payments"
            )

    @mcp.tool(
        name="get_payout_balance",
        description=(
            "Get the payout funding account balance from Pine "
            "Labs. Returns the account number, branch code, and "
            "current available balance. No parameters required."
        ),
    )
    async def get_payout_balance() -> str:
        """Get the payout funding account balance."""
        try:
            logger.info("Fetching payout funding account balance")
            response = await client.get(routes.PAYOUT_BALANCE)
            return json.dumps(response, indent=2)

        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching payout balance: %s", e
            )
            return unexpected_error_response(
                e, "fetching payout balance"
            )

    @mcp.tool(
        name="update_payout",
        description=(
            "Update the scheduled date of a payout in Pine Labs. "
            "Only payouts with status SCHEDULED can be updated. "
            "Provide the new schedule date in ISO 8601 UTC format."
        ),
    )
    async def update_payout(
        payment_reference_id: str,
        schedule_at: str,
        idempotency_key: Optional[str] = None,
    ) -> str:
        """Update the scheduled date of a payout.

        Args:
            payment_reference_id: Payout reference ID
                (max 50 chars).
            schedule_at: New schedule date in ISO 8601 UTC format
                (e.g., 2025-04-21T10:00:00Z).
            idempotency_key: Optional idempotency key.
        """
        try:
            payment_reference_id = validate_resource_id(
                payment_reference_id,
                "payment_reference_id",
                max_length=50,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            datetime.fromisoformat(
                schedule_at.replace("Z", "+00:00")
            )
        except (ValueError, TypeError, AttributeError):
            return validation_error_response(
                "schedule_at must be a valid ISO 8601 UTC "
                "timestamp (e.g., 2025-04-21T10:00:00Z)."
            )

        payload = {"scheduleAt": schedule_at}

        try:
            logger.info(
                "Updating payout: ref=%s schedule_at=%s",
                payment_reference_id,
                schedule_at,
            )
            response = await client.put(
                routes.PAYOUT_UPDATE.format(
                    payment_reference_id=payment_reference_id
                ),
                payload,
                idempotency_key,
            )
            return json.dumps(response, indent=2)

        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error("Unexpected error updating payout: %s", e)
            return unexpected_error_response(e, "updating payout")

    @mcp.tool(
        name="cancel_payout",
        description=(
            "Cancel a scheduled payout in Pine Labs. Only payouts "
            "with status SCHEDULED can be cancelled. Returns the "
            "payout details with status CANCELLED."
        ),
    )
    async def cancel_payout(payment_reference_id: str) -> str:
        """Cancel a scheduled payout.

        Args:
            payment_reference_id: Payout reference ID
                (max 50 chars).
        """
        try:
            payment_reference_id = validate_resource_id(
                payment_reference_id,
                "payment_reference_id",
                max_length=50,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info(
                "Cancelling payout: ref=%s",
                payment_reference_id,
            )
            response = await client.put(
                routes.PAYOUT_CANCEL.format(
                    payment_reference_id=payment_reference_id
                ),
            )
            return json.dumps(response, indent=2)

        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error(
                "Unexpected error cancelling payout: %s", e
            )
            return unexpected_error_response(
                e, "cancelling payout"
            )
