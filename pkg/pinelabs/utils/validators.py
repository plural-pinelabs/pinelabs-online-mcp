"""
Shared validation utilities for Pine Labs MCP Server.

Provides reusable functions for resource ID validation
and timestamp validation — used across all tool modules.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

_SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-_]+$")
_SAFE_ID_PATTERN_DOTS = re.compile(r"^[a-zA-Z0-9\-_.]+$")
_SAFE_PATH_PARAM_RE = re.compile(r"^[a-zA-Z0-9\-]{1,128}$")


def validate_resource_id(
    value: str,
    field_name: str,
    max_length: int = 50,
    *,
    allow_dots: bool = False,
) -> str:
    if not value or not value.strip():
        raise ValueError(
            f"{field_name} is required and must not be empty."
        )

    value = value.strip()

    if len(value) > max_length:
        raise ValueError(
            f"{field_name} must be at most {max_length} characters."
        )

    pattern = _SAFE_ID_PATTERN_DOTS if allow_dots else _SAFE_ID_PATTERN
    if not pattern.match(value):
        allowed = (
            "alphanumeric characters, hyphens, underscores, and dots"
            if allow_dots
            else "alphanumeric characters, hyphens, and underscores"
        )
        raise ValueError(
            f"{field_name} contains invalid characters. "
            f"Only {allowed} are allowed."
        )

    return value


def validate_expire_by(expire_by: str) -> None:
    try:
        dt = datetime.fromisoformat(
            expire_by.replace("Z", "+00:00")
        )
    except (ValueError, TypeError):
        raise ValueError(
            "expire_by must be a valid ISO 8601 timestamp "
            "(e.g., 2025-03-21T08:29Z or "
            "2025-03-21T08:29:00+05:30)."
        )

    now = datetime.now(timezone.utc)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    if dt <= now:
        raise ValueError("expire_by must be a future timestamp.")

    max_expiry = now + timedelta(days=180)
    if dt > max_expiry:
        raise ValueError(
            "expire_by must be within 180 days from now."
        )


def validate_path_param(value: str, name: str) -> str | None:
    if not value or not value.strip():
        return f"{name} must not be empty."
    if not _SAFE_PATH_PARAM_RE.match(value):
        return (
            f"{name} contains invalid characters. "
            "Only alphanumeric and hyphens are allowed."
        )
    return None
