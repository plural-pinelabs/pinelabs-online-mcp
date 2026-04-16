"""
Structured error response utilities for Pine Labs MCP Server.

Provides consistent, RFC 7807-inspired error JSON responses.
Simplified from the original — no PII sanitization or injection filtering.
"""

import json
from typing import Optional


def error_response(
    *,
    error: str,
    code: str = "INTERNAL_ERROR",
    status_code: Optional[int] = None,
    details: Optional[dict] = None,
) -> str:
    resp: dict = {
        "error": error,
        "code": code,
    }
    if status_code is not None:
        resp["status_code"] = status_code
    if details:
        resp["details"] = details
    return json.dumps(resp)


def api_error_response(
    message: str,
    code: str,
    status_code: int,
    details: Optional[dict] = None,
) -> str:
    return error_response(
        error=message,
        code=code,
        status_code=status_code,
        details=details,
    )


def validation_error_response(message: str) -> str:
    return error_response(
        error=message,
        code="VALIDATION_ERROR",
        status_code=422,
    )


def unexpected_error_response(
    exc: Exception, context: str = "operation"
) -> str:
    return error_response(
        error=f"An internal error occurred during {context}",
        code="INTERNAL_ERROR",
        status_code=500,
    )
