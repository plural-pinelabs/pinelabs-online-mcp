"""
Configuration for Pine Labs MCP Server.

Reads config from environment variables and CLI flags.
All domains and configurable URLs live here — source modules
must import from this file rather than hardcoding values.
"""

import os
from enum import Enum

from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv()


class Environment(str, Enum):
    UAT = "uat"
    PROD = "prod"


# ---------------------------------------------------------------------------
# Default base and token URLs per environment
# Override at runtime via PINELABS_BASE_URL / PINELABS_TOKEN_URL env vars.
# ---------------------------------------------------------------------------
BASE_URLS: dict[Environment, str] = {
    Environment.UAT: "https://pluraluat.v2.pinepg.in/api",
    Environment.PROD: "https://api.pluralpay.in/api",
}

TOKEN_URLS: dict[Environment, str] = {
    Environment.UAT: "https://pluraluat.v2.pinepg.in/api/auth/v1/token",
    Environment.PROD: "https://api.pluralpay.in/api/auth/v1/token",
}

# ---------------------------------------------------------------------------
# Developer portal — used by API documentation tools.
# Override via PINELABS_DOCS_BASE_URL env var.
# ---------------------------------------------------------------------------
DOCS_BASE_URL: str = os.getenv(
    "PINELABS_DOCS_BASE_URL",
    "https://developer.pinelabsonline.com",
)

# ---------------------------------------------------------------------------
# SSRF-safe domain allowlist for QR image downloads.
# Override via PINELABS_ALLOWED_IMAGE_DOMAINS (comma-separated).
# ---------------------------------------------------------------------------
_DEFAULT_ALLOWED_IMAGE_DOMAINS = (
    "pinepg.in,"
    "pluralpay.in,"
    "amazonaws.com,"
    "s3.ap-south-1.amazonaws.com"
)
ALLOWED_IMAGE_DOMAINS: frozenset[str] = frozenset(
    d.strip()
    for d in os.getenv(
        "PINELABS_ALLOWED_IMAGE_DOMAINS",
        _DEFAULT_ALLOWED_IMAGE_DOMAINS,
    ).split(",")
    if d.strip()
)


class Settings:
    """Server settings loaded from environment variables.

    Constructor kwargs override the corresponding env var values.
    """

    def __init__(self, **overrides: str) -> None:
        env_str = overrides.get(
            "environment",
            os.getenv("PINELABS_ENV", "uat"),
        ).lower()
        try:
            self.environment = Environment(env_str)
        except ValueError:
            self.environment = Environment.UAT

        self.base_url: str = overrides.get(
            "base_url",
            os.getenv(
                "PINELABS_BASE_URL",
                BASE_URLS[self.environment],
            ),
        )

        self.client_id: str = overrides.get(
            "client_id",
            os.getenv("PINELABS_CLIENT_ID", ""),
        )
        self.client_secret: str = overrides.get(
            "client_secret",
            os.getenv("PINELABS_CLIENT_SECRET", ""),
        )

        self.log_level: str = overrides.get(
            "log_level",
            os.getenv("LOG_LEVEL", "INFO"),
        ).upper()
        self.log_file: str = overrides.get(
            "log_file",
            os.getenv("LOG_FILE", ""),
        )

        self.http_timeout: float = float(overrides.get(
            "http_timeout",
            os.getenv("HTTP_TIMEOUT", "30.0"),
        ))

        self.token_url: str = overrides.get(
            "token_url",
            os.getenv(
                "PINELABS_TOKEN_URL",
                TOKEN_URLS[self.environment],
            ),
        )

        self.docs_base_url: str = overrides.get(
            "docs_base_url",
            DOCS_BASE_URL,
        )


settings = Settings()
