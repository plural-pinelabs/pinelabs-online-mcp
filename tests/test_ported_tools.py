"""Coverage tests for ported tool modules.

Exercises happy paths and key validation branches for:
- card_details, card_payments, otp, refunds, settlements, payouts.
"""

import json
from unittest.mock import AsyncMock

import pytest

from pkg.pinelabs.client import PineLabsAPIError, PineLabsClient
from pkg.pinelabs.card_details import register_card_details_tools
from pkg.pinelabs.card_payments import register_card_payment_tools
from pkg.pinelabs.otp import register_otp_tools
from pkg.pinelabs.refunds import register_refund_tools
from pkg.pinelabs.settlements import register_settlement_tools
from pkg.pinelabs.payouts import register_payout_tools


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, name, description):
        def decorator(fn):
            self.tools[name] = fn
            return fn
        return decorator


def _make_client():
    return PineLabsClient(
        base_url="https://fake.test/api",
        token_url="https://fake.test/api/auth/v1/token",
        client_id="cid",
        client_secret="csec",
    )


def _api_err():
    return PineLabsAPIError(status_code=502, code="UPSTREAM", message="boom")


# ===========================================================================
# Card Details
# ===========================================================================

class TestCardDetails:
    @pytest.fixture
    def tools(self):
        client = _make_client()
        client.post = AsyncMock(return_value={"data": [{"network": "VISA"}]})
        mcp = _FakeMCP()
        register_card_details_tools(mcp, client)
        return mcp.tools, client

    @pytest.mark.asyncio
    async def test_success(self, tools):
        t, client = tools
        result = await t["get_card_details"](card_number="4111111111111111")
        data = json.loads(result)
        assert "data" in data
        client.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_validation_error_invalid_card(self, tools):
        t, _ = tools
        result = await t["get_card_details"](card_number="abc")
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_api_error(self, tools):
        t, client = tools
        client.post = AsyncMock(side_effect=_api_err())
        result = await t["get_card_details"](card_number="4111111111111111")
        assert json.loads(result)["code"] == "UPSTREAM"

    @pytest.mark.asyncio
    async def test_unexpected_error(self, tools):
        t, client = tools
        client.post = AsyncMock(side_effect=RuntimeError("x"))
        result = await t["get_card_details"](card_number="4111111111111111")
        assert json.loads(result)["code"] == "INTERNAL_ERROR"


# ===========================================================================
# Card Payments
# ===========================================================================

class TestCardPayments:
    @pytest.fixture
    def tools(self):
        client = _make_client()
        client.post = AsyncMock(return_value={"payment_id": "pay-1"})
        mcp = _FakeMCP()
        register_card_payment_tools(mcp, client)
        return mcp.tools, client

    @pytest.mark.asyncio
    async def test_direct_card_success(self, tools):
        t, client = tools
        result = await t["create_card_payment"](
            order_id="v1-1234567890-aa-test",
            card_name="John Doe",
            amount_value=1100,
            card_number="4111111111111111",
            card_cvv="123",
            card_expiry_month="12",
            card_expiry_year="2030",
        )
        data = json.loads(result)
        assert data.get("payment_id") == "pay-1"
        client.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_token_payment_success(self, tools):
        t, client = tools
        result = await t["create_card_payment"](
            order_id="v1-1234567890-aa-test",
            card_name="John Doe",
            amount_value=1100,
            use_token=True,
            token_value="tok-abc",
            token_last4_digit="1111",
            token_expiry_month="12",
            token_expiry_year="2030",
            token_txn_type="NETWORK_TOKEN",
            token_cryptogram="crypt",
        )
        data = json.loads(result)
        assert data.get("payment_id") == "pay-1"

    @pytest.mark.asyncio
    async def test_invalid_order_id(self, tools):
        t, _ = tools
        result = await t["create_card_payment"](
            order_id="",
            card_name="John Doe",
            amount_value=1100,
            card_number="4111111111111111",
            card_cvv="123",
            card_expiry_month="12",
            card_expiry_year="2030",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_invalid_merchant_payment_reference(self, tools):
        t, _ = tools
        result = await t["create_card_payment"](
            order_id="v1-1234567890-aa-test",
            card_name="John Doe",
            amount_value=1100,
            card_number="4111111111111111",
            card_cvv="123",
            card_expiry_month="12",
            card_expiry_year="2030",
            merchant_payment_reference="bad ref!",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_token_payment_invalid_token_type(self, tools):
        t, _ = tools
        # Pydantic enum validation triggers VALIDATION_ERROR
        result = await t["create_card_payment"](
            order_id="v1-1234567890-aa-test",
            card_name="John Doe",
            amount_value=1100,
            use_token=True,
            token_value="tok-abc",
            token_last4_digit="1111",
            token_expiry_month="12",
            token_expiry_year="2030",
            token_txn_type="BOGUS_TOKEN_TYPE",
            token_cryptogram="crypt",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_api_error(self, tools):
        t, client = tools
        client.post = AsyncMock(side_effect=_api_err())
        result = await t["create_card_payment"](
            order_id="v1-1234567890-aa-test",
            card_name="John Doe",
            amount_value=1100,
            card_number="4111111111111111",
            card_cvv="123",
            card_expiry_month="12",
            card_expiry_year="2030",
        )
        assert json.loads(result)["code"] == "UPSTREAM"

    @pytest.mark.asyncio
    async def test_unexpected_error(self, tools):
        t, client = tools
        client.post = AsyncMock(side_effect=RuntimeError("x"))
        result = await t["create_card_payment"](
            order_id="v1-1234567890-aa-test",
            card_name="John Doe",
            amount_value=1100,
            card_number="4111111111111111",
            card_cvv="123",
            card_expiry_month="12",
            card_expiry_year="2030",
        )
        assert json.loads(result)["code"] == "INTERNAL_ERROR"


# ===========================================================================
# OTP
# ===========================================================================

class TestOtp:
    @pytest.fixture
    def tools(self):
        client = _make_client()
        client.post = AsyncMock(return_value={"status": "OK"})
        mcp = _FakeMCP()
        register_otp_tools(mcp, client)
        return mcp.tools, client

    @pytest.mark.asyncio
    async def test_generate_otp_success(self, tools):
        t, client = tools
        result = await t["generate_otp"](payment_id="pay-123")
        assert json.loads(result)["status"] == "OK"
        client.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_generate_otp_invalid_payment_id(self, tools):
        t, _ = tools
        result = await t["generate_otp"](payment_id="")
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_generate_otp_api_error(self, tools):
        t, client = tools
        client.post = AsyncMock(side_effect=_api_err())
        result = await t["generate_otp"](payment_id="pay-123")
        assert json.loads(result)["code"] == "UPSTREAM"

    @pytest.mark.asyncio
    async def test_generate_otp_unexpected(self, tools):
        t, client = tools
        client.post = AsyncMock(side_effect=RuntimeError("x"))
        result = await t["generate_otp"](payment_id="pay-123")
        assert json.loads(result)["code"] == "INTERNAL_ERROR"

    @pytest.mark.asyncio
    async def test_submit_otp_success(self, tools):
        t, _ = tools
        result = await t["submit_otp"](payment_id="pay-123", otp="123456")
        assert json.loads(result)["status"] == "OK"

    @pytest.mark.asyncio
    async def test_submit_otp_invalid_payment_id(self, tools):
        t, _ = tools
        result = await t["submit_otp"](payment_id="", otp="123456")
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_submit_otp_invalid_otp(self, tools):
        t, _ = tools
        result = await t["submit_otp"](payment_id="pay-123", otp="ab")
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_submit_otp_api_error(self, tools):
        t, client = tools
        client.post = AsyncMock(side_effect=_api_err())
        result = await t["submit_otp"](payment_id="pay-123", otp="123456")
        assert json.loads(result)["code"] == "UPSTREAM"

    @pytest.mark.asyncio
    async def test_resend_otp_success(self, tools):
        t, _ = tools
        result = await t["resend_otp"](payment_id="pay-123")
        assert json.loads(result)["status"] == "OK"

    @pytest.mark.asyncio
    async def test_resend_otp_invalid(self, tools):
        t, _ = tools
        result = await t["resend_otp"](payment_id="")
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_resend_otp_api_error(self, tools):
        t, client = tools
        client.post = AsyncMock(side_effect=_api_err())
        result = await t["resend_otp"](payment_id="pay-123")
        assert json.loads(result)["code"] == "UPSTREAM"

    @pytest.mark.asyncio
    async def test_resend_otp_unexpected(self, tools):
        t, client = tools
        client.post = AsyncMock(side_effect=RuntimeError("x"))
        result = await t["resend_otp"](payment_id="pay-123")
        assert json.loads(result)["code"] == "INTERNAL_ERROR"


# ===========================================================================
# Refunds
# ===========================================================================

class TestRefunds:
    @pytest.fixture
    def tools(self):
        client = _make_client()
        client.post = AsyncMock(return_value={"refund_id": "rf-1"})
        mcp = _FakeMCP()
        register_refund_tools(mcp, client)
        return mcp.tools, client

    @pytest.mark.asyncio
    async def test_full_refund_success(self, tools):
        t, client = tools
        result = await t["create_refund"](
            order_id="v1-1234567890-aa-test",
            amount_value=10000,
            merchant_order_reference="ref-1",
        )
        assert json.loads(result)["refund_id"] == "rf-1"
        client.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_refund_with_products(self, tools):
        t, _ = tools
        result = await t["create_refund"](
            order_id="v1-1234567890-aa-test",
            amount_value=10000,
            merchant_order_reference="ref-2",
            products=[
                {
                    "product_code": "P1",
                    "product_imei": "imei-1",
                    "product_amount_value": 5000,
                    "product_amount_currency": "INR",
                }
            ],
        )
        assert json.loads(result)["refund_id"] == "rf-1"

    @pytest.mark.asyncio
    async def test_refund_with_split(self, tools):
        t, _ = tools
        result = await t["create_refund"](
            order_id="v1-1234567890-aa-test",
            amount_value=10000,
            merchant_order_reference="ref-3",
            split_type="AMOUNT",
            split_details=[
                {
                    "parent_order_split_settlement_id": "p1",
                    "split_merchant_id": "m1",
                    "merchant_settlement_reference": "msr-1",
                    "amount_value": 10000,
                    "amount_currency": "INR",
                    "status": "DO_NOT_RECOVER",
                }
            ],
        )
        assert json.loads(result)["refund_id"] == "rf-1"

    @pytest.mark.asyncio
    async def test_invalid_order_id(self, tools):
        t, _ = tools
        result = await t["create_refund"](
            order_id="",
            amount_value=10000,
            merchant_order_reference="ref-x",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_invalid_amount_too_low(self, tools):
        t, _ = tools
        result = await t["create_refund"](
            order_id="v1-1234567890-aa-test",
            amount_value=10,
            merchant_order_reference="ref-x",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_invalid_product_data(self, tools):
        t, _ = tools
        result = await t["create_refund"](
            order_id="v1-1234567890-aa-test",
            amount_value=10000,
            merchant_order_reference="ref-x",
            products=[{"product_imei": "imei-only"}],  # missing product_code
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_invalid_split_detail(self, tools):
        t, _ = tools
        result = await t["create_refund"](
            order_id="v1-1234567890-aa-test",
            amount_value=10000,
            merchant_order_reference="ref-x",
            split_type="AMOUNT",
            split_details=[{"amount_value": 100}],  # missing required keys
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_api_error(self, tools):
        t, client = tools
        client.post = AsyncMock(side_effect=_api_err())
        result = await t["create_refund"](
            order_id="v1-1234567890-aa-test",
            amount_value=10000,
            merchant_order_reference="ref-y",
        )
        assert json.loads(result)["code"] == "UPSTREAM"

    @pytest.mark.asyncio
    async def test_unexpected_error(self, tools):
        t, client = tools
        client.post = AsyncMock(side_effect=RuntimeError("x"))
        result = await t["create_refund"](
            order_id="v1-1234567890-aa-test",
            amount_value=10000,
            merchant_order_reference="ref-z",
        )
        assert json.loads(result)["code"] == "INTERNAL_ERROR"


# ===========================================================================
# Settlements
# ===========================================================================

class TestSettlements:
    @pytest.fixture
    def tools(self):
        client = _make_client()
        client.get = AsyncMock(return_value={"data": []})
        mcp = _FakeMCP()
        register_settlement_tools(mcp, client)
        return mcp.tools, client

    @pytest.mark.asyncio
    async def test_get_all_success(self, tools):
        t, client = tools
        result = await t["get_all_settlements"](
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
            page="1",
            per_page="5",
        )
        assert "data" in json.loads(result)
        client.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_all_missing_start(self, tools):
        t, _ = tools
        result = await t["get_all_settlements"](
            start_date="", end_date="2024-10-09T23:59:59"
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_get_all_missing_end(self, tools):
        t, _ = tools
        result = await t["get_all_settlements"](
            start_date="2024-10-01T00:00:00", end_date=""
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_get_all_invalid_date_format(self, tools):
        t, _ = tools
        result = await t["get_all_settlements"](
            start_date="not-a-date", end_date="2024-10-09T23:59:59"
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_get_all_end_before_start(self, tools):
        t, _ = tools
        result = await t["get_all_settlements"](
            start_date="2024-10-09T00:00:00",
            end_date="2024-10-01T00:00:00",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_get_all_range_too_large(self, tools):
        t, _ = tools
        result = await t["get_all_settlements"](
            start_date="2024-01-01T00:00:00",
            end_date="2024-06-01T00:00:00",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_get_all_invalid_per_page(self, tools):
        t, _ = tools
        result = await t["get_all_settlements"](
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
            per_page="100",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_get_all_api_error(self, tools):
        t, client = tools
        client.get = AsyncMock(side_effect=_api_err())
        result = await t["get_all_settlements"](
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
        )
        assert json.loads(result)["code"] == "UPSTREAM"

    @pytest.mark.asyncio
    async def test_get_all_unexpected(self, tools):
        t, client = tools
        client.get = AsyncMock(side_effect=RuntimeError("x"))
        result = await t["get_all_settlements"](
            start_date="2024-10-01T00:00:00",
            end_date="2024-10-09T23:59:59",
        )
        assert json.loads(result)["code"] == "INTERNAL_ERROR"

    @pytest.mark.asyncio
    async def test_by_utr_success(self, tools):
        t, _ = tools
        result = await t["get_settlement_by_utr"](
            utr="410092786849", page="1", per_page="5"
        )
        assert "data" in json.loads(result)

    @pytest.mark.asyncio
    async def test_by_utr_invalid(self, tools):
        t, _ = tools
        result = await t["get_settlement_by_utr"](utr="")
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_by_utr_api_error(self, tools):
        t, client = tools
        client.get = AsyncMock(side_effect=_api_err())
        result = await t["get_settlement_by_utr"](utr="410092786849")
        assert json.loads(result)["code"] == "UPSTREAM"

    @pytest.mark.asyncio
    async def test_by_utr_unexpected(self, tools):
        t, client = tools
        client.get = AsyncMock(side_effect=RuntimeError("x"))
        result = await t["get_settlement_by_utr"](utr="410092786849")
        assert json.loads(result)["code"] == "INTERNAL_ERROR"


# ===========================================================================
# Payouts
# ===========================================================================

class TestPayouts:
    @pytest.fixture
    def tools(self):
        client = _make_client()
        client.post = AsyncMock(return_value={"id": "po-1"})
        client.get = AsyncMock(return_value={"data": []})
        client.put = AsyncMock(return_value={"id": "po-1"})
        mcp = _FakeMCP()
        register_payout_tools(mcp, client)
        return mcp.tools, client

    # -- create_payout --

    @pytest.mark.asyncio
    async def test_create_upi_success(self, tools):
        t, client = tools
        result = await t["create_payout"](
            client_reference_id="cref-1",
            payee_name="John Doe",
            amount_value=10000,
            mode="UPI",
            remarks="payout",
        )
        assert json.loads(result)["id"] == "po-1"
        client.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_imps_success(self, tools):
        t, _ = tools
        result = await t["create_payout"](
            client_reference_id="cref-2",
            payee_name="John Doe",
            amount_value=10000,
            mode="IMPS",
            remarks="payout",
            account_number="123456789012",
            branch_code="HDFC0001234",
            phone="9876543210",
            email="x@y.com",
        )
        assert json.loads(result)["id"] == "po-1"

    @pytest.mark.asyncio
    async def test_create_invalid_client_ref(self, tools):
        t, _ = tools
        result = await t["create_payout"](
            client_reference_id="",
            payee_name="John Doe",
            amount_value=10000,
            mode="UPI",
            remarks="r",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_create_invalid_payee(self, tools):
        t, _ = tools
        result = await t["create_payout"](
            client_reference_id="cref-3",
            payee_name="bad@name",
            amount_value=10000,
            mode="UPI",
            remarks="r",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_create_invalid_mode(self, tools):
        t, _ = tools
        result = await t["create_payout"](
            client_reference_id="cref-4",
            payee_name="John",
            amount_value=10000,
            mode="WIRE",
            remarks="r",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_create_invalid_remarks(self, tools):
        t, _ = tools
        result = await t["create_payout"](
            client_reference_id="cref-5",
            payee_name="John",
            amount_value=10000,
            mode="UPI",
            remarks="@@@",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_create_invalid_amount(self, tools):
        t, _ = tools
        result = await t["create_payout"](
            client_reference_id="cref-6",
            payee_name="John",
            amount_value=0,
            mode="UPI",
            remarks="r",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_create_invalid_phone(self, tools):
        t, _ = tools
        result = await t["create_payout"](
            client_reference_id="cref-7",
            payee_name="John",
            amount_value=10000,
            mode="UPI",
            remarks="r",
            phone="123",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_create_imps_missing_account(self, tools):
        t, _ = tools
        result = await t["create_payout"](
            client_reference_id="cref-8",
            payee_name="John",
            amount_value=10000,
            mode="IMPS",
            remarks="r",
            branch_code="HDFC0001234",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_create_imps_missing_branch(self, tools):
        t, _ = tools
        result = await t["create_payout"](
            client_reference_id="cref-9",
            payee_name="John",
            amount_value=10000,
            mode="IMPS",
            remarks="r",
            account_number="123456789012",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_create_invalid_account(self, tools):
        t, _ = tools
        result = await t["create_payout"](
            client_reference_id="cref-10",
            payee_name="John",
            amount_value=10000,
            mode="IMPS",
            remarks="r",
            account_number="abc",
            branch_code="HDFC0001234",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_create_api_error(self, tools):
        t, client = tools
        client.post = AsyncMock(side_effect=_api_err())
        result = await t["create_payout"](
            client_reference_id="cref-e",
            payee_name="John",
            amount_value=10000,
            mode="UPI",
            remarks="r",
        )
        assert json.loads(result)["code"] == "UPSTREAM"

    @pytest.mark.asyncio
    async def test_create_unexpected(self, tools):
        t, client = tools
        client.post = AsyncMock(side_effect=RuntimeError("x"))
        result = await t["create_payout"](
            client_reference_id="cref-u",
            payee_name="John",
            amount_value=10000,
            mode="UPI",
            remarks="r",
        )
        assert json.loads(result)["code"] == "INTERNAL_ERROR"

    # -- get_payout_payments --

    @pytest.mark.asyncio
    async def test_list_no_filters(self, tools):
        t, _ = tools
        result = await t["get_payout_payments"]()
        assert "data" in json.loads(result)

    @pytest.mark.asyncio
    async def test_list_all_filters(self, tools):
        t, _ = tools
        result = await t["get_payout_payments"](
            payment_reference_id="pri-1",
            client_reference_id="cri-1",
            request_reference_id="rri-1",
            bank_transaction_reference_id="btx-1",
            mode="UPI",
            date_from="2024-10-01T00:00:00",
            date_to="2024-10-05T00:00:00",
            status="SUCCESS",
            page=1,
            count=10,
        )
        assert "data" in json.loads(result)

    @pytest.mark.asyncio
    async def test_list_invalid_mode(self, tools):
        t, _ = tools
        result = await t["get_payout_payments"](mode="WIRE")
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_list_invalid_status(self, tools):
        t, _ = tools
        result = await t["get_payout_payments"](status="OOPS")
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_list_invalid_date_range(self, tools):
        t, _ = tools
        result = await t["get_payout_payments"](
            date_from="2024-10-09T00:00:00", date_to="2024-10-01T00:00:00"
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_list_invalid_page(self, tools):
        t, _ = tools
        result = await t["get_payout_payments"](page=0)
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_list_invalid_count(self, tools):
        t, _ = tools
        result = await t["get_payout_payments"](count=50)
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_list_api_error(self, tools):
        t, client = tools
        client.get = AsyncMock(side_effect=_api_err())
        result = await t["get_payout_payments"]()
        assert json.loads(result)["code"] == "UPSTREAM"

    # -- get_payout_balance --

    @pytest.mark.asyncio
    async def test_balance_success(self, tools):
        t, _ = tools
        result = await t["get_payout_balance"]()
        assert "data" in json.loads(result)

    @pytest.mark.asyncio
    async def test_balance_api_error(self, tools):
        t, client = tools
        client.get = AsyncMock(side_effect=_api_err())
        result = await t["get_payout_balance"]()
        assert json.loads(result)["code"] == "UPSTREAM"

    @pytest.mark.asyncio
    async def test_balance_unexpected(self, tools):
        t, client = tools
        client.get = AsyncMock(side_effect=RuntimeError("x"))
        result = await t["get_payout_balance"]()
        assert json.loads(result)["code"] == "INTERNAL_ERROR"

    # -- update_payout --

    @pytest.mark.asyncio
    async def test_update_success(self, tools):
        t, _ = tools
        result = await t["update_payout"](
            payment_reference_id="pri-1",
            schedule_at="2025-04-21T10:00:00Z",
        )
        assert json.loads(result)["id"] == "po-1"

    @pytest.mark.asyncio
    async def test_update_invalid_ref(self, tools):
        t, _ = tools
        result = await t["update_payout"](
            payment_reference_id="",
            schedule_at="2025-04-21T10:00:00Z",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_update_invalid_schedule(self, tools):
        t, _ = tools
        result = await t["update_payout"](
            payment_reference_id="pri-1",
            schedule_at="bad-date",
        )
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_update_api_error(self, tools):
        t, client = tools
        client.put = AsyncMock(side_effect=_api_err())
        result = await t["update_payout"](
            payment_reference_id="pri-1",
            schedule_at="2025-04-21T10:00:00Z",
        )
        assert json.loads(result)["code"] == "UPSTREAM"

    # -- cancel_payout --

    @pytest.mark.asyncio
    async def test_cancel_success(self, tools):
        t, _ = tools
        result = await t["cancel_payout"](payment_reference_id="pri-1")
        assert json.loads(result)["id"] == "po-1"

    @pytest.mark.asyncio
    async def test_cancel_invalid(self, tools):
        t, _ = tools
        result = await t["cancel_payout"](payment_reference_id="")
        assert json.loads(result)["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_cancel_api_error(self, tools):
        t, client = tools
        client.put = AsyncMock(side_effect=_api_err())
        result = await t["cancel_payout"](payment_reference_id="pri-1")
        assert json.loads(result)["code"] == "UPSTREAM"
