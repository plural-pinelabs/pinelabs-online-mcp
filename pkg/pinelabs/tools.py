"""
Central tool registration.

Creates toolset groups and registers all tool modules.
Respects read_only mode and enabled_toolsets filtering.
"""

from __future__ import annotations

from fastmcp import FastMCP

from pkg.pinelabs.client import PineLabsClient

from pkg.pinelabs.payment_links import register_payment_link_tools
from pkg.pinelabs.orders import register_order_tools
from pkg.pinelabs.checkout_orders import (
    register_checkout_order_tools,
)
from pkg.pinelabs.subscriptions import register_subscription_tools
from pkg.pinelabs.upi_intent_qr import (
    register_upi_intent_qr_tools,
)
from pkg.pinelabs.refunds import register_refund_tools
from pkg.pinelabs.card_details import register_card_details_tools
from pkg.pinelabs.card_payments import register_card_payment_tools
from pkg.pinelabs.otp import register_otp_tools
from pkg.pinelabs.settlements import register_settlement_tools
from pkg.pinelabs.payouts import register_payout_tools
from pkg.pinelabs.code_generation import (
    register_code_generation_tools,
)
from pkg.pinelabs.mcp_api import register_mcp_api_tools
from pkg.pinelabs.api_docs import register_api_docs_tools
from pkg.pinelabs.success_rate import register_success_rate_tools

# Toolset definitions: maps toolset name → (registrar, access_type)
# access_type is "read", "write", or "readwrite".
# In read_only mode, "write"-only toolsets are skipped entirely.
_TOOLSETS: dict[str, dict] = {
    "payment_links": {
        "registrar": lambda mcp, client: register_payment_link_tools(mcp, client),
        "access": "readwrite",
    },
    "orders": {
        "registrar": lambda mcp, client: register_order_tools(mcp, client),
        "access": "readwrite",
    },
    "checkout_orders": {
        "registrar": lambda mcp, client: register_checkout_order_tools(mcp, client),
        "access": "write",
    },
    "subscriptions": {
        "registrar": lambda mcp, client: register_subscription_tools(mcp, client),
        "access": "readwrite",
    },
    "upi_intent_qr": {
        "registrar": lambda mcp, client: register_upi_intent_qr_tools(mcp, client),
        "access": "write",
    },
    "refunds": {
        "registrar": lambda mcp, client: register_refund_tools(mcp, client),
        "access": "write",
    },
    "card_details": {
        "registrar": lambda mcp, client: register_card_details_tools(mcp, client),
        "access": "read",
    },
    "card_payments": {
        "registrar": lambda mcp, client: register_card_payment_tools(mcp, client),
        "access": "write",
    },
    "otp": {
        "registrar": lambda mcp, client: register_otp_tools(mcp, client),
        "access": "write",
    },
    "settlements": {
        "registrar": lambda mcp, client: register_settlement_tools(mcp, client),
        "access": "read",
    },
    "payouts": {
        "registrar": lambda mcp, client: register_payout_tools(mcp, client),
        "access": "readwrite",
    },
    "code_generation": {
        "registrar": lambda mcp, _client: register_code_generation_tools(mcp),
        "access": "read",
    },
    "mcp_api": {
        "registrar": lambda mcp, client: register_mcp_api_tools(mcp, client),
        "access": "read",
    },
    "api_docs": {
        "registrar": lambda mcp, _client: register_api_docs_tools(mcp),
        "access": "read",
    },
    "success_rate": {
        "registrar": lambda mcp, client: register_success_rate_tools(mcp, client),
        "access": "read",
    },
}


def register_all_tools(
    mcp: FastMCP,
    client: PineLabsClient,
    *,
    read_only: bool = False,
    enabled_toolsets: list[str] | None = None,
) -> None:
    """Register all Pine Labs tools onto the MCP server.

    Args:
        mcp: FastMCP server instance.
        client: PineLabsClient for API calls.
        read_only: If True, skip write-only toolsets.
        enabled_toolsets: If set, only register these toolsets.
    """
    active = enabled_toolsets or list(_TOOLSETS.keys())

    for name in active:
        ts = _TOOLSETS.get(name)
        if ts is None:
            continue

        # In read_only mode, skip write-only toolsets entirely.
        if read_only and ts["access"] == "write":
            continue

        ts["registrar"](mcp, client)
