"""Tests for the merchant success-rate MCP tool in tools/success_rate.py."""

import json

import httpx
import pytest
import respx

from pkg.pinelabs.config import BASE_URLS, Environment
from pkg.pinelabs.success_rate import register_success_rate_tools
from pkg.pinelabs import routes

SR_URL = f"{BASE_URLS[Environment.UAT]}{routes.SUCCESS_RATE}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeMCP:
    """Minimal MCP stub that captures registered tool functions."""

    def __init__(self):
        self.tools = {}

    def tool(self, name, description):
        def decorator(fn):
            self.tools[name] = fn
            return fn
        return decorator


class _FakeClient:
    """Minimal PineLabsClient stub for success rate tests."""

    def __init__(self):
        self.base_url = BASE_URLS[Environment.UAT]

    async def _get_access_token(self):
        return "test-bearer-token"


def _make_tools():
    mcp = _FakeMCP()
    client = _FakeClient()
    register_success_rate_tools(mcp, client)
    return mcp.tools


_SAMPLE_RESPONSE = {
    "success_rate": 95.5,
    "total_transactions": 200,
    "successful_transactions": 191,
    "failed_transactions": 9,
    "breakdown": [
        {"payment_method": "CARD", "success_rate": 96.0, "total": 100},
        {"payment_method": "UPI", "success_rate": 95.0, "total": 100},
    ],
}


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestGetMerchantSuccessRateHappyPath:
    @respx.mock
    @pytest.mark.asyncio
    async def test_happy_path_space_separator(self):
        respx.get(SR_URL).mock(return_value=httpx.Response(200, json=_SAMPLE_RESPONSE))
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="2026-04-01 00:00:00",
            end_date="2026-04-07 23:59:59",
        )
        data = json.loads(result)
        assert data["success_rate"] == 95.5
        assert data["total_transactions"] == 200

    @respx.mock
    @pytest.mark.asyncio
    async def test_happy_path_iso_t_separator(self):
        """Accept ISO 8601 T-separator format as well."""
        respx.get(SR_URL).mock(return_value=httpx.Response(200, json=_SAMPLE_RESPONSE))
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="2026-04-01T00:00:00",
            end_date="2026-04-07T23:59:59",
        )
        data = json.loads(result)
        assert data["success_rate"] == 95.5

    @respx.mock
    @pytest.mark.asyncio
    async def test_happy_path_with_pagination(self):
        respx.get(SR_URL).mock(return_value=httpx.Response(200, json=_SAMPLE_RESPONSE))
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="2026-04-07 00:00:00",
            end_date="2026-04-07 23:59:59",
        )
        data = json.loads(result)
        assert "success_rate" in data

    @respx.mock
    @pytest.mark.asyncio
    async def test_params_formatted_with_space_separator(self):
        """Verify the API call uses 'YYYY-MM-DD HH:MM:SS' format regardless of input format."""
        route = respx.get(SR_URL).mock(return_value=httpx.Response(200, json=_SAMPLE_RESPONSE))
        tools = _make_tools()
        await tools["get_merchant_success_rate"](
            start_date="2026-04-01T00:00:00",
            end_date="2026-04-01T23:59:59",
        )
        sent_params = dict(route.calls.last.request.url.params)
        assert "T" not in sent_params["start_date"]
        assert "T" not in sent_params["end_date"]
        assert sent_params["start_date"] == "2026-04-01 00:00:00"
        assert sent_params["end_date"] == "2026-04-01 23:59:59"

    @respx.mock
    @pytest.mark.asyncio
    async def test_today_single_day_range(self):
        """A same-day range is valid."""
        respx.get(SR_URL).mock(return_value=httpx.Response(200, json=_SAMPLE_RESPONSE))
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="2026-04-07 00:00:00",
            end_date="2026-04-07 23:59:59",
        )
        data = json.loads(result)
        assert data["success_rate"] == 95.5

    @respx.mock
    @pytest.mark.asyncio
    async def test_auth_header_sent(self):
        """Verify Authorization header is included in the request."""
        route = respx.get(SR_URL).mock(return_value=httpx.Response(200, json=_SAMPLE_RESPONSE))
        tools = _make_tools()
        await tools["get_merchant_success_rate"](
            start_date="2026-04-07 00:00:00",
            end_date="2026-04-07 23:59:59",
        )
        assert route.calls.last.request.headers["authorization"] == "Bearer test-bearer-token"


# ---------------------------------------------------------------------------
# API / unexpected errors
# ---------------------------------------------------------------------------

class TestGetMerchantSuccessRateErrors:
    @respx.mock
    @pytest.mark.asyncio
    async def test_http_status_error_401(self):
        respx.get(SR_URL).mock(
            return_value=httpx.Response(401, json={"code": "UNAUTHORIZED", "message": "Invalid credentials"})
        )
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="2026-04-07 00:00:00",
            end_date="2026-04-07 23:59:59",
        )
        data = json.loads(result)
        assert data["code"] == "UNAUTHORIZED"
        assert data["status_code"] == 401

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_status_error_500(self):
        respx.get(SR_URL).mock(return_value=httpx.Response(500, json={"error": "Server error"}))
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="2026-04-07 00:00:00",
            end_date="2026-04-07 23:59:59",
        )
        data = json.loads(result)
        assert data["status_code"] == 500

    @respx.mock
    @pytest.mark.asyncio
    async def test_network_error(self):
        respx.get(SR_URL).mock(side_effect=httpx.ConnectError("connection refused"))
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="2026-04-07 00:00:00",
            end_date="2026-04-07 23:59:59",
        )
        data = json.loads(result)
        assert data["code"] == "INTERNAL_ERROR"


# ---------------------------------------------------------------------------
# Date validation
# ---------------------------------------------------------------------------

class TestGetMerchantSuccessRateDateValidation:
    @pytest.mark.asyncio
    async def test_invalid_date_format(self):
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="not-a-date-at-all-xyz",
            end_date="2026-04-07 23:59:59",
        )
        data = json.loads(result)
        assert data["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_end_before_start(self):
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="2026-04-07 23:59:59",
            end_date="2026-04-07 00:00:00",
        )
        data = json.loads(result)
        assert data["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_range_exceeds_7_days(self):
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="2026-03-31 00:00:00",
            end_date="2026-04-07 23:59:59",  # 8 days
        )
        data = json.loads(result)
        assert data["code"] == "VALIDATION_ERROR"
        assert "7" in data["error"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_exactly_7_days_is_valid(self):
        """A 7-day range should not be rejected."""
        respx.get(SR_URL).mock(return_value=httpx.Response(200, json=_SAMPLE_RESPONSE))
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="2026-04-01 00:00:00",
            end_date="2026-04-07 23:59:59",  # exactly 6 days 23h 59m 59s — within limit
        )
        data = json.loads(result)
        assert "success_rate" in data

    @pytest.mark.asyncio
    async def test_empty_start_date(self):
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="",
            end_date="2026-04-07 23:59:59",
        )
        data = json.loads(result)
        assert data["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Natural-language date parsing (dateparser)
# ---------------------------------------------------------------------------

class TestGetMerchantSuccessRateNaturalLanguage:
    @respx.mock
    @pytest.mark.asyncio
    async def test_natural_language_hours_ago(self):
        """'5 hours ago' + 'now' should resolve to a valid range and call the API."""
        respx.get(SR_URL).mock(return_value=httpx.Response(200, json=_SAMPLE_RESPONSE))
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="5 hours ago",
            end_date="now",
        )
        data = json.loads(result)
        assert data["success_rate"] == 95.5

    @respx.mock
    @pytest.mark.asyncio
    async def test_natural_language_yesterday(self):
        """'yesterday at 00:00' + 'yesterday at 23:59:59' should resolve correctly."""
        respx.get(SR_URL).mock(return_value=httpx.Response(200, json=_SAMPLE_RESPONSE))
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="yesterday at 00:00",
            end_date="yesterday at 23:59:59",
        )
        data = json.loads(result)
        assert data["success_rate"] == 95.5

    @respx.mock
    @pytest.mark.asyncio
    async def test_default_end_date_is_now(self):
        """Omitting end_date should default to 'now'."""
        respx.get(SR_URL).mock(return_value=httpx.Response(200, json=_SAMPLE_RESPONSE))
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="3 hours ago",
        )
        data = json.loads(result)
        assert data["success_rate"] == 95.5

    @respx.mock
    @pytest.mark.asyncio
    async def test_natural_language_today(self):
        """'today at 00:00:00' + 'now' is a valid range."""
        respx.get(SR_URL).mock(return_value=httpx.Response(200, json=_SAMPLE_RESPONSE))
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="today at 00:00:00",
            end_date="now",
        )
        data = json.loads(result)
        assert data["success_rate"] == 95.5

    @respx.mock
    @pytest.mark.asyncio
    async def test_exact_dates_still_work(self):
        """Exact YYYY-MM-DD HH:MM:SS strings should still be accepted."""
        respx.get(SR_URL).mock(return_value=httpx.Response(200, json=_SAMPLE_RESPONSE))
        tools = _make_tools()
        result = await tools["get_merchant_success_rate"](
            start_date="2026-04-07 00:00:00",
            end_date="2026-04-07 23:59:59",
        )
        data = json.loads(result)
        assert data["success_rate"] == 95.5
