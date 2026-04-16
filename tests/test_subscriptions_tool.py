"""Tests for tools/subscriptions.py — all 22 subscription tools."""

import json
from unittest.mock import AsyncMock

import pytest

from pkg.pinelabs.client import PineLabsAPIError
from pkg.pinelabs.subscriptions import register_subscription_tools


@pytest.fixture()
def tools(fake_mcp, mock_client):
    register_subscription_tools(fake_mcp, mock_client)
    return fake_mcp.tools


# ---------------------------------------------------------------------------
# PLANS
# ---------------------------------------------------------------------------


class TestCreatePlan:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={
            "plan_id": "v1-plan-123",
            "status": "ACTIVE",
            "plan_name": "Monthly Plan",
        })

        result = json.loads(await tools["create_plan"](
            plan_name="Monthly Plan",
            frequency="Month",
            amount_value=50000,
            max_limit_amount_value=500000,
            end_date="2025-12-31T00:00:00Z",
            merchant_plan_reference="mp-ref-001",
        ))
        assert result["plan_id"] == "v1-plan-123"
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/public/plans"
        payload = call_args[0][1]
        assert payload["plan_name"] == "Monthly Plan"
        assert payload["frequency"] == "Month"
        assert payload["amount"]["value"] == 50000

    @pytest.mark.asyncio
    async def test_invalid_frequency(self, tools, mock_client) -> None:
        result = json.loads(await tools["create_plan"](
            plan_name="Bad Plan",
            frequency="InvalidFreq",
            amount_value=50000,
            max_limit_amount_value=500000,
            end_date="2025-12-31T00:00:00Z",
            merchant_plan_reference="mp-ref-bad",
        ))
        assert result["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_api_error(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(
            side_effect=PineLabsAPIError(400, "INVALID_REQUEST", "Bad request")
        )
        result = json.loads(await tools["create_plan"](
            plan_name="Plan",
            frequency="Month",
            amount_value=50000,
            max_limit_amount_value=500000,
            end_date="2025-12-31T00:00:00Z",
            merchant_plan_reference="mp-ref-err",
        ))
        assert result["code"] == "INVALID_REQUEST"
        assert result["status_code"] == 400


class TestGetPlans:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(return_value=[{"plan_id": "p1"}, {"plan_id": "p2"}])
        result = json.loads(await tools["get_plans"]())
        assert len(result) == 2
        mock_client.get.assert_awaited_once_with("/v1/public/plans", params=None)

    @pytest.mark.asyncio
    async def test_with_filters(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(return_value=[{"plan_id": "p1"}])
        result = json.loads(await tools["get_plans"](
            plan_id="v1-plan-123",
            frequency="Month",
            amount_range="isMore",
            size=5,
            page=0,
            sort="frequency,asc",
        ))
        assert len(result) == 1
        mock_client.get.assert_awaited_once_with(
            "/v1/public/plans",
            params={
                "plan_id": "v1-plan-123",
                "frequency": "Month",
                "amount[amount_range]": "isMore",
                "size": "5",
                "page": "0",
                "sort": "frequency,asc",
            },
        )


class TestGetPlanById:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(return_value={"plan_id": "v1-plan-123", "status": "ACTIVE"})
        result = json.loads(await tools["get_plan_by_id"](plan_id="v1-plan-123"))
        assert result["plan_id"] == "v1-plan-123"
        mock_client.get.assert_awaited_once_with("/v1/public/plans/v1-plan-123")

    @pytest.mark.asyncio
    async def test_invalid_id(self, tools, mock_client) -> None:
        result = json.loads(await tools["get_plan_by_id"](plan_id=""))
        assert result["code"] == "VALIDATION_ERROR"


class TestGetPlanByMerchantReference:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(return_value={"plan_id": "v1-plan-ref", "merchant_plan_reference": "ref-001"})
        result = json.loads(await tools["get_plan_by_merchant_reference"](
            merchant_plan_reference="ref-001",
        ))
        assert result["merchant_plan_reference"] == "ref-001"
        mock_client.get.assert_awaited_once_with("/v1/public/plans/reference/ref-001")


class TestUpdatePlan:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.patch = AsyncMock(return_value={"plan_id": "v1-plan-123", "plan_name": "Updated"})
        result = json.loads(await tools["update_plan"](
            plan_id="v1-plan-123",
            plan_name="Updated",
        ))
        assert result["plan_name"] == "Updated"
        call_args = mock_client.patch.call_args
        assert call_args[0][0] == "/v1/public/plans/v1-plan-123"
        assert call_args[0][1]["plan_name"] == "Updated"

    @pytest.mark.asyncio
    async def test_invalid_id(self, tools, mock_client) -> None:
        result = json.loads(await tools["update_plan"](plan_id=""))
        assert result["code"] == "VALIDATION_ERROR"


class TestDeletePlan:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.delete = AsyncMock(return_value={})
        result = json.loads(await tools["delete_plan"](plan_id="v1-plan-123"))
        assert result == {}
        mock_client.delete.assert_awaited_once_with("/v1/public/plans/v1-plan-123")

    @pytest.mark.asyncio
    async def test_api_error(self, tools, mock_client) -> None:
        mock_client.delete = AsyncMock(
            side_effect=PineLabsAPIError(404, "NOT_FOUND", "Plan not found")
        )
        result = json.loads(await tools["delete_plan"](plan_id="v1-plan-notfound"))
        assert result["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# SUBSCRIPTIONS
# ---------------------------------------------------------------------------


class TestCreateSubscription:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={
            "subscription_id": "v1-sub-123",
            "order_id": "v1-ord-123",
            "redirect_url": "https://checkout.example.com/sub",
        })
        result = json.loads(await tools["create_subscription"](
            merchant_subscription_reference="ms-ref-001",
            plan_id="v1-plan-123",
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-12-31T00:00:00Z",
            customer_id="cust-001",
            integration_mode="REDIRECT",
        ))
        assert result["subscription_id"] == "v1-sub-123"
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/public/subscriptions"
        payload = call_args[0][1]
        assert payload["plan_id"] == "v1-plan-123"
        assert payload["integration_mode"] == "REDIRECT"

    @pytest.mark.asyncio
    async def test_with_bank_account(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={"subscription_id": "v1-sub-tpv"})
        result = json.loads(await tools["create_subscription"](
            merchant_subscription_reference="ms-tpv",
            plan_id="v1-plan-123",
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-12-31T00:00:00Z",
            customer_id="cust-002",
            integration_mode="SEAMLESS",
            is_tpv_enabled=True,
            bank_account_number="41620100006421",
            bank_account_name="John Doe",
            bank_ifsc="HDFC0001234",
        ))
        assert result["subscription_id"] == "v1-sub-tpv"
        payload = mock_client.post.call_args[0][1]
        assert payload["bank_account"]["account_number"] == "41620100006421"
        assert payload["is_tpv_enabled"] is True

    @pytest.mark.asyncio
    async def test_invalid_integration_mode(self, tools, mock_client) -> None:
        result = json.loads(await tools["create_subscription"](
            merchant_subscription_reference="ms-bad",
            plan_id="v1-plan-123",
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-12-31T00:00:00Z",
            customer_id="cust-001",
            integration_mode="INVALID",
        ))
        assert result["code"] == "VALIDATION_ERROR"


class TestGetSubscriptions:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(return_value=[{"subscription_id": "s1"}])
        result = json.loads(await tools["get_subscriptions"]())
        assert len(result) == 1
        mock_client.get.assert_awaited_once_with("/v1/public/subscriptions", params=None)

    @pytest.mark.asyncio
    async def test_with_filters(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(return_value=[{"subscription_id": "s1"}])
        result = json.loads(await tools["get_subscriptions"](
            plan_id="v1-plan-123",
            status="ACTIVE",
            start_date="2022-02-01T17:32:28Z",
            frequency="Month",
            amount_range="isEqual",
            size=10,
            page=1,
        ))
        assert len(result) == 1
        mock_client.get.assert_awaited_once_with(
            "/v1/public/subscriptions",
            params={
                "plan_id": "v1-plan-123",
                "status": "ACTIVE",
                "start_date": "2022-02-01T17:32:28Z",
                "frequency": "Month",
                "amount[amount_range]": "isEqual",
                "size": "10",
                "page": "1",
            },
        )


class TestGetSubscriptionById:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(return_value={"subscription_id": "v1-sub-123", "status": "ACTIVE"})
        result = json.loads(await tools["get_subscription_by_id"](subscription_id="v1-sub-123"))
        assert result["status"] == "ACTIVE"
        mock_client.get.assert_awaited_once_with("/v1/public/subscriptions/v1-sub-123")


class TestGetSubscriptionByMerchantReference:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(return_value={"subscription_id": "v1-sub-ref", "merchant_subscription_reference": "ref-001"})
        result = json.loads(await tools["get_subscription_by_merchant_reference"](
            merchant_subscription_reference="ref-001",
        ))
        assert result["merchant_subscription_reference"] == "ref-001"
        mock_client.get.assert_awaited_once_with("/v1/public/subscriptions/reference/ref-001")


class TestPauseSubscription:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={"subscription_id": "v1-sub-123", "status": "PAUSED"})
        result = json.loads(await tools["pause_subscription"](subscription_id="v1-sub-123"))
        assert result["status"] == "PAUSED"
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/public/subscriptions/v1-sub-123/pause"

    @pytest.mark.asyncio
    async def test_invalid_id(self, tools, mock_client) -> None:
        result = json.loads(await tools["pause_subscription"](subscription_id=""))
        assert result["code"] == "VALIDATION_ERROR"


class TestResumeSubscription:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={"subscription_id": "v1-sub-123", "status": "ACTIVE"})
        result = json.loads(await tools["resume_subscription"](subscription_id="v1-sub-123"))
        assert result["status"] == "ACTIVE"
        mock_client.post.assert_awaited_once()
        assert mock_client.post.call_args[0][0] == "/v1/public/subscriptions/v1-sub-123/resume"


class TestCancelSubscription:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={"subscription_id": "v1-sub-123", "status": "CANCELLED"})
        result = json.loads(await tools["cancel_subscription"](subscription_id="v1-sub-123"))
        assert result["status"] == "CANCELLED"
        assert mock_client.post.call_args[0][0] == "/v1/public/subscriptions/v1-sub-123/cancel"

    @pytest.mark.asyncio
    async def test_api_error(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(
            side_effect=PineLabsAPIError(400, "INVALID_STATE", "Cannot cancel")
        )
        result = json.loads(await tools["cancel_subscription"](subscription_id="v1-sub-123"))
        assert result["code"] == "INVALID_STATE"


class TestUpdateSubscription:
    @pytest.mark.asyncio
    async def test_success_with_new_plan(self, tools, mock_client) -> None:
        mock_client.patch = AsyncMock(return_value={"subscription_id": "v1-sub-123", "status": "ACTIVE"})
        result = json.loads(await tools["update_subscription"](
            subscription_id="v1-sub-123",
            reason="Switching plan",
            new_plan_id="v1-plan-456",
        ))
        assert result["subscription_id"] == "v1-sub-123"
        call_args = mock_client.patch.call_args
        assert call_args[0][0] == "/v1/public/subscriptions/v1-sub-123"
        assert call_args[0][1]["reason"] == "Switching plan"
        assert call_args[0][1]["new_plan_id"] == "v1-plan-456"

    @pytest.mark.asyncio
    async def test_success_with_new_end_date(self, tools, mock_client) -> None:
        mock_client.patch = AsyncMock(return_value={"subscription_id": "v1-sub-123"})
        result = json.loads(await tools["update_subscription"](
            subscription_id="v1-sub-123",
            reason="Extending",
            new_end_date="2026-12-31T00:00:00Z",
        ))
        assert result["subscription_id"] == "v1-sub-123"

    @pytest.mark.asyncio
    async def test_missing_both_optional_fields(self, tools, mock_client) -> None:
        result = json.loads(await tools["update_subscription"](
            subscription_id="v1-sub-123",
            reason="No changes",
        ))
        assert result["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# PRESENTATIONS
# ---------------------------------------------------------------------------


class TestCreatePresentation:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={
            "presentation_id": "v1-pre-123",
            "subscription_id": "v1-sub-123",
            "status": "CREATED",
        })
        result = json.loads(await tools["create_presentation"](
            subscription_id="v1-sub-123",
            due_date="2025-03-15T10:30:00Z",
            amount_value=50000,
            merchant_presentation_reference="mpr-001",
        ))
        assert result["presentation_id"] == "v1-pre-123"
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/public/subscriptions/v1-sub-123/presentations"
        payload = call_args[0][1]
        assert payload["amount"]["value"] == 50000
        assert payload["merchant_presentation_reference"] == "mpr-001"

    @pytest.mark.asyncio
    async def test_invalid_amount(self, tools, mock_client) -> None:
        result = json.loads(await tools["create_presentation"](
            subscription_id="v1-sub-123",
            due_date="2025-03-15T10:30:00Z",
            amount_value=10,  # below minimum of 100
            merchant_presentation_reference="mpr-bad",
        ))
        assert result["code"] == "VALIDATION_ERROR"


class TestGetPresentation:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(return_value={"presentation_id": "v1-pre-123", "status": "CREATED"})
        result = json.loads(await tools["get_presentation"](presentation_id="v1-pre-123"))
        assert result["presentation_id"] == "v1-pre-123"
        mock_client.get.assert_awaited_once_with("/v1/public/presentations/v1-pre-123")


class TestDeletePresentation:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.delete = AsyncMock(return_value={})
        result = json.loads(await tools["delete_presentation"](presentation_id="v1-pre-123"))
        assert result == {}
        mock_client.delete.assert_awaited_once_with("/v1/public/presentations/v1-pre-123")


class TestGetPresentationsBySubscriptionId:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(return_value=[{"presentation_id": "p1"}, {"presentation_id": "p2"}])
        result = json.loads(await tools["get_presentations_by_subscription_id"](
            subscription_id="v1-sub-123",
        ))
        assert len(result) == 2
        mock_client.get.assert_awaited_once_with(
            "/v1/public/subscriptions/v1-sub-123/presentations",
            params=None,
        )

    @pytest.mark.asyncio
    async def test_with_pagination(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(return_value=[{"presentation_id": "p1"}])
        result = json.loads(await tools["get_presentations_by_subscription_id"](
            subscription_id="v1-sub-123",
            size=10,
            page=0,
            sort="due_date,desc",
        ))
        assert len(result) == 1
        mock_client.get.assert_awaited_once_with(
            "/v1/public/subscriptions/v1-sub-123/presentations",
            params={"size": "10", "page": "0", "sort": "due_date,desc"},
        )


class TestGetPresentationByMerchantReference:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.get = AsyncMock(return_value={
            "presentation_id": "v1-pre-ref",
            "merchant_presentation_reference": "mpr-001",
        })
        result = json.loads(await tools["get_presentation_by_merchant_reference"](
            merchant_presentation_reference="mpr-001",
        ))
        assert result["merchant_presentation_reference"] == "mpr-001"
        mock_client.get.assert_awaited_once_with("/v1/public/presentations/reference/mpr-001")


# ---------------------------------------------------------------------------
# NOTIFICATION, DEBIT, MERCHANT RETRY
# ---------------------------------------------------------------------------


class TestSendSubscriptionNotification:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={
            "subscription_id": "v1-sub-123",
            "presentation_id": "v1-pre-123",
            "pdn_status": "CREATED",
            "status": "WAITING_FOR_EXECUTION",
        })
        result = json.loads(await tools["send_subscription_notification"](
            subscription_id="v1-sub-123",
            due_date="2025-03-15T10:30:00Z",
            amount_value=50000,
            merchant_presentation_reference="mpr-001",
        ))
        assert result["pdn_status"] == "CREATED"
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/public/subscriptions/notify"
        payload = call_args[0][1]
        assert payload["subscription_id"] == "v1-sub-123"
        assert payload["amount"]["value"] == 50000

    @pytest.mark.asyncio
    async def test_api_error(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(
            side_effect=PineLabsAPIError(400, "INVALID_REQUEST", "Invalid sub")
        )
        result = json.loads(await tools["send_subscription_notification"](
            subscription_id="v1-sub-bad",
            due_date="2025-03-15T10:30:00Z",
            amount_value=50000,
            merchant_presentation_reference="mpr-bad",
        ))
        assert result["code"] == "INVALID_REQUEST"


class TestCreateDebit:
    @pytest.mark.asyncio
    async def test_success_with_presentation_id(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={
            "subscription_id": "v1-sub-123",
            "presentation_id": "v1-pre-123",
            "status": "CREATED",
        })
        result = json.loads(await tools["create_debit"](
            presentation_id="v1-pre-123",
        ))
        assert result["status"] == "CREATED"
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/public/subscriptions/execute"
        assert call_args[0][1]["presentation_id"] == "v1-pre-123"

    @pytest.mark.asyncio
    async def test_success_with_merchant_ref(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={"status": "CREATED"})
        result = json.loads(await tools["create_debit"](
            merchant_presentation_reference="mpr-001",
        ))
        assert result["status"] == "CREATED"

    @pytest.mark.asyncio
    async def test_missing_both_identifiers(self, tools, mock_client) -> None:
        result = json.loads(await tools["create_debit"]())
        assert result["code"] == "VALIDATION_ERROR"


class TestCreateMerchantRetry:
    @pytest.mark.asyncio
    async def test_success(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(return_value={})
        result = json.loads(await tools["create_merchant_retry"](
            presentation_id="v1-pre-123",
        ))
        assert result == {}
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/mandate/merchant-retry"
        assert call_args[0][1]["presentation_id"] == "v1-pre-123"

    @pytest.mark.asyncio
    async def test_missing_both_identifiers(self, tools, mock_client) -> None:
        result = json.loads(await tools["create_merchant_retry"]())
        assert result["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_api_error(self, tools, mock_client) -> None:
        mock_client.post = AsyncMock(
            side_effect=PineLabsAPIError(400, "MAX_RETRIES", "Max retries exceeded")
        )
        result = json.loads(await tools["create_merchant_retry"](
            merchant_presentation_reference="mpr-001",
        ))
        assert result["code"] == "MAX_RETRIES"
