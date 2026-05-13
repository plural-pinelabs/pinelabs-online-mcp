"""
Pine Labs Card Details MCP tool.

Defines the get_card_details tool that:
1. Validates card_number
2. Calls Pine Labs Get Card Details API
3. Returns card info (network, issuer, type, etc.)
"""

import json
import logging

from fastmcp import FastMCP
from pydantic import ValidationError

from pkg.pinelabs.client import PineLabsAPIError, PineLabsClient
from pkg.pinelabs.models.card_payments import (
    CardDetailEntry,
    GetCardDetailsRequest,
)
from pkg.pinelabs.utils.errors import (
    api_error_response,
    unexpected_error_response,
    validation_error_response,
)
from pkg.pinelabs import routes

logger = logging.getLogger("pinelabs-mcp-server.card_details")


def _sanitize_validation_error(e: Exception) -> str:
    if isinstance(e, ValidationError):
        return json.dumps(e.errors(include_input=False), default=str)
    return str(e)


def register_card_details_tools(
    mcp: FastMCP, client: PineLabsClient
) -> None:
    """Register card details tools on the FastMCP server."""

    @mcp.tool(
        name="get_card_details",
        description=(
            "Get card BIN details such as card network, issuer, "
            "type, and OTP support for a given card number."
        ),
    )
    async def get_card_details(card_number: str) -> str:
        """Get card details (network, issuer, type) for a card number.

        Args:
            card_number: Full card number (13-19 digits).
        """
        try:
            request_body = GetCardDetailsRequest(
                card_details=[
                    CardDetailEntry(card_number=card_number)
                ]
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info("Fetching card details for card BIN")
            response = await client.post(
                routes.CARD_DETAILS_GET, payload
            )
            return json.dumps(response, indent=2)

        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error fetching card details: %s", e
            )
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching card details: %s", e
            )
            return unexpected_error_response(e, "get card details")
