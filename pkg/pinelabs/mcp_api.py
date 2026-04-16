"""
Pine Labs MCP API tools.

Defines tools that proxy to the settlement-api MCP endpoints:
1. get_payment_link_details
2. get_order_details
3. get_refund_order_details
4. search_transaction
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Optional

from fastmcp import FastMCP

from pkg.pinelabs.client import PineLabsClient, PineLabsAPIError
from pkg.pinelabs.utils.errors import (
    api_error_response,
    validation_error_response,
    unexpected_error_response,
)
from pkg.pinelabs.utils.validators import validate_path_param
from pkg.pinelabs import routes

_SAFE_MERCHANT_ID_RE = re.compile(r"^[a-zA-Z0-9\-_]{1,128}$")

logger = logging.getLogger("pinelabs-mcp-server.mcp_api")


def _validate_date_range(
    start_date: str, end_date: str,
) -> str | None:
    """Validate ISO 8601 dates, logical order, max 60 days."""
    try:
        dt_start = datetime.fromisoformat(start_date)
        dt_end = datetime.fromisoformat(end_date)
    except (ValueError, TypeError):
        return (
            "start_date and end_date must be valid "
            "ISO 8601 timestamps."
        )

    if dt_end < dt_start:
        return "end_date must not be before start_date."
    if (dt_end - dt_start).total_seconds() > 60 * 86400:
        return "Date range must not exceed 60 days."

    return None


def _validate_pagination(
    page: Optional[int], per_page: Optional[int],
) -> str | None:
    if page is not None and page < 1:
        return "page must be >= 1."
    if per_page is not None:
        if per_page < 1 or per_page > 100:
            return "per_page must be between 1 and 100."
    return None


def _validate_merchant_id(merchant_id: str) -> str | None:
    if not merchant_id or not merchant_id.strip():
        return "merchant_id is required and must not be empty."
    if not _SAFE_MERCHANT_ID_RE.match(merchant_id):
        return (
            "merchant_id contains invalid characters. "
            "Only alphanumeric, hyphens, and underscores "
            "are allowed (max 128 chars)."
        )
    return None


def register_mcp_api_tools(
    mcp: FastMCP, client: PineLabsClient
) -> None:
    """Register all MCP API tools on the FastMCP server."""

    @mcp.tool(
        name="get_payment_link_details",
        description=(
            "Fetch payment link details within a date range from "
            "Pine Labs. Max date range is 60 days. Requires "
            "merchant_id."
        ),
    )
    async def get_payment_link_details(
        merchant_id: str,
        start_date: str,
        end_date: str,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> str:
        """Fetch payment link details within a date range."""
        mid_err = _validate_merchant_id(merchant_id)
        if mid_err:
            return validation_error_response(mid_err)

        date_err = _validate_date_range(start_date, end_date)
        if date_err:
            return validation_error_response(date_err)

        pag_err = _validate_pagination(page, per_page)
        if pag_err:
            return validation_error_response(pag_err)

        params: dict[str, str] = {
            "start_date": start_date,
            "end_date": end_date,
        }
        if page is not None:
            params["page"] = str(page)
        if per_page is not None:
            params["per_page"] = str(per_page)

        try:
            logger.info(
                "Fetching payment link details: "
                "merchant_id=%s",
                merchant_id,
            )
            response = await client.get(
                routes.MCP_PAYMENT_LINK_DETAILS,
                params=params,
                extra_headers={"merchant-id": merchant_id},
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code,
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching payment link "
                "details: %s", e,
            )
            return unexpected_error_response(
                e, "fetching payment link details",
            )

    @mcp.tool(
        name="get_order_details",
        description=(
            "Fetch order details within a date range from "
            "Pine Labs. Max date range is 60 days. Requires "
            "merchant_id."
        ),
    )
    async def get_order_details(
        merchant_id: str,
        start_date: str,
        end_date: str,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> str:
        """Fetch order details within a date range."""
        mid_err = _validate_merchant_id(merchant_id)
        if mid_err:
            return validation_error_response(mid_err)

        date_err = _validate_date_range(start_date, end_date)
        if date_err:
            return validation_error_response(date_err)

        pag_err = _validate_pagination(page, per_page)
        if pag_err:
            return validation_error_response(pag_err)

        params: dict[str, str] = {
            "start_date": start_date,
            "end_date": end_date,
        }
        if page is not None:
            params["page"] = str(page)
        if per_page is not None:
            params["per_page"] = str(per_page)

        try:
            logger.info(
                "Fetching order details: merchant_id=%s",
                merchant_id,
            )
            response = await client.get(
                routes.MCP_ORDER_DETAILS,
                params=params,
                extra_headers={"merchant-id": merchant_id},
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code,
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching order details: %s",
                e,
            )
            return unexpected_error_response(
                e, "fetching order details",
            )

    @mcp.tool(
        name="get_refund_order_details",
        description=(
            "Fetch refund order details within a date range from "
            "Pine Labs. Max date range is 60 days. Requires "
            "merchant_id."
        ),
    )
    async def get_refund_order_details(
        merchant_id: str,
        start_date: str,
        end_date: str,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> str:
        """Fetch refund order details within a date range."""
        mid_err = _validate_merchant_id(merchant_id)
        if mid_err:
            return validation_error_response(mid_err)

        date_err = _validate_date_range(start_date, end_date)
        if date_err:
            return validation_error_response(date_err)

        pag_err = _validate_pagination(page, per_page)
        if pag_err:
            return validation_error_response(pag_err)

        params: dict[str, str] = {
            "start_date": start_date,
            "end_date": end_date,
        }
        if page is not None:
            params["page"] = str(page)
        if per_page is not None:
            params["per_page"] = str(per_page)

        try:
            logger.info(
                "Fetching refund order details: "
                "merchant_id=%s",
                merchant_id,
            )
            response = await client.get(
                routes.MCP_REFUND_ORDER_DETAILS,
                params=params,
                extra_headers={"merchant-id": merchant_id},
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code,
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching refund order "
                "details: %s", e,
            )
            return unexpected_error_response(
                e, "fetching refund order details",
            )

    @mcp.tool(
        name="search_transaction",
        description=(
            "Search for a transaction by transaction ID in "
            "Pine Labs. Requires merchant_id."
        ),
    )
    async def search_transaction(
        merchant_id: str,
        transaction_id: str,
    ) -> str:
        """Search for a transaction by transaction ID."""
        mid_err = _validate_merchant_id(merchant_id)
        if mid_err:
            return validation_error_response(mid_err)

        tid_err = validate_path_param(
            transaction_id, "transaction_id",
        )
        if tid_err:
            return validation_error_response(tid_err)

        try:
            path = routes.MCP_SEARCH_TRANSACTION.format(
                transaction_id=transaction_id,
            )
            logger.info(
                "Searching transaction: merchant_id=%s "
                "transaction_id=%s",
                merchant_id, transaction_id,
            )
            response = await client.get(
                path,
                extra_headers={"merchant-id": merchant_id},
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error("Pine Labs API error: %s", e)
            return api_error_response(
                e.message, e.code, e.status_code,
            )
        except Exception as e:
            logger.error(
                "Unexpected error searching transaction: %s", e,
            )
            return unexpected_error_response(
                e, "searching transaction",
            )
