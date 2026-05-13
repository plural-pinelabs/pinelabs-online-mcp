"""
Pine Labs OTP MCP tools.

Defines tools for OTP operations during card payment flow:
- generate_otp: Generate OTP for card payment verification
- submit_otp: Submit OTP to complete card payment
- resend_otp: Resend OTP to customer's registered mobile
"""

import json
import logging

from fastmcp import FastMCP
from pydantic import ValidationError

from pkg.pinelabs.client import PineLabsAPIError, PineLabsClient
from pkg.pinelabs.models.card_payments import (
    GenerateOtpRequest,
    ResendOtpRequest,
    SubmitOtpRequest,
)
from pkg.pinelabs.utils.errors import (
    api_error_response,
    unexpected_error_response,
    validation_error_response,
)
from pkg.pinelabs.utils.validators import validate_resource_id
from pkg.pinelabs import routes

logger = logging.getLogger("pinelabs-mcp-server.otp")


def _sanitize_validation_error(e: Exception) -> str:
    if isinstance(e, ValidationError):
        return json.dumps(e.errors(include_input=False), default=str)
    return str(e)


def register_otp_tools(
    mcp: FastMCP, client: PineLabsClient
) -> None:
    """Register OTP tools on the FastMCP server."""

    @mcp.tool(
        name="generate_otp",
        description=(
            "Generate OTP for a card payment. Sends an OTP to the "
            "customer's registered mobile number for payment "
            "verification."
        ),
    )
    async def generate_otp(payment_id: str) -> str:
        """Generate OTP for card payment verification.

        Args:
            payment_id: Payment ID from Pine Labs.
        """
        try:
            payment_id = validate_resource_id(
                payment_id,
                "payment_id",
                max_length=50,
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            request_body = GenerateOtpRequest(payment_id=payment_id)
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info(
                "Generating OTP for payment_id=%s", payment_id
            )
            response = await client.post(
                routes.OTP_GENERATE, payload
            )
            return json.dumps(response, indent=2)

        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error generating OTP: %s", e
            )
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error("Unexpected error generating OTP: %s", e)
            return unexpected_error_response(e, "generate OTP")

    @mcp.tool(
        name="submit_otp",
        description=(
            "Submit OTP to verify and process a card payment. "
            "Requires the payment_id and the OTP received by the "
            "customer."
        ),
    )
    async def submit_otp(payment_id: str, otp: str) -> str:
        """Submit OTP for card payment verification.

        Args:
            payment_id: Payment ID from Pine Labs.
            otp: OTP received on registered mobile (4-8 digits).
        """
        try:
            payment_id = validate_resource_id(
                payment_id,
                "payment_id",
                max_length=50,
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            request_body = SubmitOtpRequest(
                payment_id=payment_id, otp=otp
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info(
                "Submitting OTP for payment_id=%s", payment_id
            )
            response = await client.post(
                routes.OTP_SUBMIT, payload
            )
            return json.dumps(response, indent=2)

        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error submitting OTP: %s", e
            )
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error("Unexpected error submitting OTP: %s", e)
            return unexpected_error_response(e, "submit OTP")

    @mcp.tool(
        name="resend_otp",
        description=(
            "Resend OTP to the customer's registered mobile number "
            "for card payment verification."
        ),
    )
    async def resend_otp(payment_id: str) -> str:
        """Resend OTP for card payment verification.

        Args:
            payment_id: Payment ID from Pine Labs.
        """
        try:
            payment_id = validate_resource_id(
                payment_id,
                "payment_id",
                max_length=50,
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            request_body = ResendOtpRequest(payment_id=payment_id)
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info(
                "Resending OTP for payment_id=%s", payment_id
            )
            response = await client.post(
                routes.OTP_RESEND, payload
            )
            return json.dumps(response, indent=2)

        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error resending OTP: %s", e
            )
            return api_error_response(
                e.message, e.code, e.status_code, e.payload or None
            )
        except Exception as e:
            logger.error("Unexpected error resending OTP: %s", e)
            return unexpected_error_response(e, "resend OTP")
