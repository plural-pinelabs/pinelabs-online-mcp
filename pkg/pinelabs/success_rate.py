"""
Pine Labs Merchant Success Rate MCP tool.

Defines the get_merchant_success_rate tool using dateparser
for natural-language date parsing.
"""

import json
import logging

import dateparser
import httpx
from fastmcp import FastMCP

from pkg.pinelabs.client import PineLabsClient
from pkg.pinelabs.utils.errors import (
    api_error_response,
    validation_error_response,
    unexpected_error_response,
)
from pkg.pinelabs import routes

logger = logging.getLogger("pinelabs-mcp-server.success_rate")

_MAX_RANGE_DAYS = 7
_API_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def register_success_rate_tools(
    mcp: FastMCP, client: PineLabsClient
) -> None:
    """Register the merchant success-rate tool."""

    @mcp.tool(
        name="get_merchant_success_rate",
        description=(
            "Fetch the transaction success rate for the "
            "merchant's account over a given date-time range. "
            "Both start_date and end_date accept natural-language "
            "expressions (e.g., '5 hours ago', 'now') or exact "
            "'YYYY-MM-DD HH:MM:SS' strings. Max range: 7 days."
        ),
    )
    async def get_merchant_success_rate(
        start_date: str,
        end_date: str = "now",
    ) -> str:
        """Fetch merchant transaction success rate."""
        _parser_settings = {
            "PREFER_DATES_FROM": "past",
            "RETURN_AS_TIMEZONE_AWARE": False,
            "TIMEZONE": "Asia/Kolkata",
        }
        dt_start = dateparser.parse(
            start_date.strip(), settings=_parser_settings,
        )
        dt_end = dateparser.parse(
            end_date.strip(), settings=_parser_settings,
        )

        if dt_start is None or dt_end is None:
            return validation_error_response(
                "Could not parse start_date or end_date. "
                "Use natural language or "
                "'YYYY-MM-DD HH:MM:SS' format."
            )

        if dt_end < dt_start:
            return validation_error_response(
                "end_date must not be before start_date."
            )

        if (dt_end - dt_start).total_seconds() > (
            _MAX_RANGE_DAYS * 86400 + 60
        ):
            return validation_error_response(
                f"Date range must not exceed "
                f"{_MAX_RANGE_DAYS} days."
            )

        params: dict[str, str] = {
            "start_date": dt_start.strftime(_API_DATE_FORMAT),
            "end_date": dt_end.strftime(_API_DATE_FORMAT),
        }

        # Use the client's token and base_url
        url = f"{client.base_url}{routes.SUCCESS_RATE}"
        try:
            bearer_token = await client._get_access_token()
            headers = {
                "Authorization": f"Bearer {bearer_token}",
            }

            logger.info(
                "Fetching merchant success rate: "
                "start_date=%s end_date=%s",
                params["start_date"],
                params["end_date"],
            )
            async with httpx.AsyncClient(
                verify=True,
            ) as http_client:
                response = await http_client.get(
                    url, params=params, headers=headers,
                )
                response.raise_for_status()
                return json.dumps(response.json(), indent=2)

        except httpx.HTTPStatusError as e:
            logger.error(
                "SR API HTTP error: status=%s",
                e.response.status_code,
            )
            try:
                body = e.response.json()
                code = body.get("code", "API_ERROR")
                message = body.get("message") or body.get(
                    "error", "Request failed",
                )
            except Exception:
                code = "API_ERROR"
                message = "Request failed"
            return api_error_response(
                message, code, e.response.status_code,
            )
        except httpx.RequestError as e:
            logger.error("SR API request error: %s", e)
            return unexpected_error_response(
                e, "fetching merchant success rate",
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching merchant "
                "success rate: %s", e,
            )
            return unexpected_error_response(
                e, "fetching merchant success rate",
            )
