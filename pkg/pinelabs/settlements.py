"""
Pine Labs Settlement tools.

Defines read-only tools for querying settlement data via /settlements/v1/:
- get_all_settlements: List settlements within a date range
- get_settlement_by_utr: Get settlement details by UTR number
"""

import json
import logging
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

logger = logging.getLogger("pinelabs-mcp-server.settlements")


def _validate_date_range(
    start_date: str, end_date: str
) -> str | None:
    """Validate date range as ISO 8601, logical order, max 60 days."""
    try:
        dt_start = datetime.fromisoformat(start_date)
        dt_end = datetime.fromisoformat(end_date)
    except (ValueError, TypeError):
        return (
            "start_date and end_date must be valid ISO 8601 "
            "timestamps."
        )
    if dt_end < dt_start:
        return "end_date must not be before start_date."
    if (dt_end - dt_start).total_seconds() > 60 * 86400:
        return "Date range must not exceed 60 days."
    return None


def _validate_pagination(
    page: Optional[str], per_page: Optional[str]
) -> str | None:
    if per_page is not None:
        try:
            pp = int(per_page)
        except (ValueError, TypeError):
            return "per_page must be a valid integer."
        if pp < 1 or pp > 10:
            return "per_page must be between 1 and 10."
    if page is not None:
        try:
            pg = int(page)
        except (ValueError, TypeError):
            return "page must be a valid integer."
        if pg < 1:
            return "page must be >= 1."
    return None


def register_settlement_tools(
    mcp: FastMCP, client: PineLabsClient
) -> None:
    """Register all settlement tools on the FastMCP server."""

    @mcp.tool(
        name="get_all_settlements",
        description=(
            "Fetch all settlements from Pine Labs for a given "
            "date range. Returns settlement records with "
            "pagination. Both start_date and end_date are "
            "required. Maximum date range is 60 days. Page size "
            "is max 10 records per page."
        ),
    )
    async def get_all_settlements(
        start_date: str,
        end_date: str,
        page: Optional[str] = None,
        per_page: Optional[str] = None,
    ) -> str:
        """Fetch all settlements within a date range.

        Args:
            start_date: Start date in ISO 8601 format
                (e.g. 2024-10-01T00:00:00).
            end_date: End date in ISO 8601 format
                (e.g. 2024-10-09T23:59:59).
            page: Page number to retrieve (e.g. "1").
            per_page: Records per page, max 10 (e.g. "10").
        """
        if not start_date or not start_date.strip():
            return validation_error_response(
                "start_date is required."
            )
        if not end_date or not end_date.strip():
            return validation_error_response(
                "end_date is required."
            )

        date_err = _validate_date_range(start_date, end_date)
        if date_err:
            return validation_error_response(date_err)

        page_err = _validate_pagination(page, per_page)
        if page_err:
            return validation_error_response(page_err)

        params: dict[str, str] = {
            "start_date": start_date,
            "end_date": end_date,
        }
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page

        try:
            logger.info(
                "Fetching all settlements: %s to %s",
                start_date,
                end_date,
            )
            response = await client.get(
                routes.SETTLEMENT_LIST, params=params
            )
            return json.dumps(response, indent=2)

        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching settlements: %s", e
            )
            return unexpected_error_response(
                e, "fetching settlements"
            )

    @mcp.tool(
        name="get_settlement_by_utr",
        description=(
            "Fetch settlement details by UTR (Unique Transaction "
            "Reference) from Pine Labs. Returns settlement summary "
            "and individual transaction details for the given UTR. "
            "Page size is max 10 records per page."
        ),
    )
    async def get_settlement_by_utr(
        utr: str,
        page: Optional[str] = None,
        per_page: Optional[str] = None,
    ) -> str:
        """Fetch settlement details by UTR number.

        Args:
            utr: Unique Transaction Reference number.
                Example: "410092786849".
            page: Page number to retrieve (e.g. "1").
            per_page: Records per page, max 10 (e.g. "10").
        """
        try:
            utr = validate_resource_id(utr, "utr", max_length=100)
        except ValueError as e:
            return validation_error_response(str(e))

        page_err = _validate_pagination(page, per_page)
        if page_err:
            return validation_error_response(page_err)

        params: dict[str, str] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page

        try:
            logger.info("Fetching settlement by UTR: %s", utr)
            response = await client.get(
                routes.SETTLEMENT_DETAIL.format(utr=utr),
                params=params if params else None,
            )
            return json.dumps(response, indent=2)

        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching settlement by UTR: %s",
                e,
            )
            return unexpected_error_response(
                e, "fetching settlement by UTR"
            )
