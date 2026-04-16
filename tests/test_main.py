"""Tests for server creation via new_pinelabs_mcp_server."""

import asyncio


from pkg.pinelabs.config import Settings
from pkg.pinelabs.server import new_pinelabs_mcp_server


class TestNewPineLabsMCPServer:
    def test_creates_fastmcp_instance(self):
        settings = Settings(
            client_id="test-id",
            client_secret="test-secret",
        )
        mcp = new_pinelabs_mcp_server(settings)
        assert mcp is not None
        assert mcp.name == "pinelabs-mcp-server"

    def test_tools_are_registered(self):
        settings = Settings(
            client_id="test-id",
            client_secret="test-secret",
        )
        mcp = new_pinelabs_mcp_server(settings)
        tools = asyncio.run(mcp.list_tools())
        tool_names = [t.name for t in tools]
        expected_tools = [
            "create_payment_link",
            "get_payment_link_by_id",
            "get_payment_link_by_merchant_reference",
            "cancel_payment_link",
            "resend_payment_link_notification",
            "cancel_order",
            "get_order_by_order_id",
            "create_order",
            "create_upi_intent_payment_with_qr",
            "get_payment_link_details",
            "get_order_details",
            "get_refund_order_details",
            "search_transaction",
        ]
        for name in expected_tools:
            assert name in tool_names, f"Tool '{name}' not registered"

    def test_read_only_mode(self):
        settings = Settings(
            client_id="test-id",
            client_secret="test-secret",
        )
        mcp = new_pinelabs_mcp_server(settings, read_only=True)
        assert mcp is not None

    def test_enabled_toolsets_filter(self):
        settings = Settings(
            client_id="test-id",
            client_secret="test-secret",
        )
        mcp = new_pinelabs_mcp_server(
            settings, enabled_toolsets=["payment_links"]
        )
        assert mcp is not None
