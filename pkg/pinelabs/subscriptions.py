"""
Pine Labs Subscription MCP tools — Plans, Subscriptions, Presentations.

Registers 22 tools covering the full Pine Labs Subscription API surface.
"""

import json
import logging
from typing import Optional

from pydantic import ValidationError
from fastmcp import FastMCP

from pkg.pinelabs.client import PineLabsClient, PineLabsAPIError
from pkg.pinelabs.models.payment_links import Amount
from pkg.pinelabs.models.subscriptions import (
    BankAccount,
    CreateDebitRequest,
    CreateMerchantRetryRequest,
    CreatePlanRequest,
    CreatePresentationRequest,
    CreateSubscriptionRequest,
    PlanFrequency,
    SubscriptionIntegrationMode,
    SubscriptionNotificationRequest,
    UpdatePlanRequest,
    UpdateSubscriptionRequest,
)
from pkg.pinelabs.utils.validators import validate_resource_id
from pkg.pinelabs.utils.errors import (
    api_error_response,
    validation_error_response,
    unexpected_error_response,
)
from pkg.pinelabs import routes

logger = logging.getLogger("pinelabs-mcp-server.subscriptions")


def _sanitize_validation_error(e: Exception) -> str:
    if isinstance(e, ValidationError):
        return json.dumps(e.errors(include_input=False), default=str)
    return str(e)


def register_subscription_tools(  # noqa: C901
    mcp: FastMCP, client: PineLabsClient
) -> None:
    """Register all subscription tools on the FastMCP server."""

    # -------------------------------------------------------------------
    # PLANS
    # -------------------------------------------------------------------

    @mcp.tool(
        name="create_plan",
        description=(
            "Create a new subscription plan in Pine Labs. "
            "Requires plan_name, frequency, amount_value, "
            "max_limit_amount_value, end_date, and "
            "merchant_plan_reference. Returns plan details."
        ),
    )
    async def create_plan(
        plan_name: str,
        frequency: str,
        amount_value: int,
        max_limit_amount_value: int,
        end_date: str,
        merchant_plan_reference: str,
        currency: str = "INR",
        plan_description: Optional[str] = None,
        trial_period_in_days: Optional[int] = None,
        start_date: Optional[str] = None,
        initial_debit_amount_value: Optional[int] = None,
        auto_debit_ot: Optional[bool] = None,
        merchant_metadata: Optional[dict[str, str]] = None,
    ) -> str:
        try:
            freq = PlanFrequency(frequency)
        except ValueError:
            return validation_error_response(
                "Invalid frequency. Allowed: "
                f"{[e.value for e in PlanFrequency]}"
            )

        try:
            initial_debit = None
            if initial_debit_amount_value is not None:
                initial_debit = Amount(
                    value=initial_debit_amount_value,
                    currency=currency,
                )
            request_body = CreatePlanRequest(
                plan_name=plan_name,
                frequency=freq,
                amount=Amount(
                    value=amount_value, currency=currency,
                ),
                max_limit_amount=Amount(
                    value=max_limit_amount_value,
                    currency=currency,
                ),
                end_date=end_date,
                merchant_plan_reference=merchant_plan_reference,
                plan_description=plan_description,
                trial_period_in_days=trial_period_in_days,
                start_date=start_date,
                initial_debit_amount=initial_debit,
                auto_debit_ot=auto_debit_ot,
                merchant_metadata=merchant_metadata,
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info(
                "Creating plan: ref=%s",
                merchant_plan_reference,
            )
            response = await client.post(
                routes.PLAN_CREATE, payload,
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error creating plan: %s",
                type(e).__name__,
            )
            return unexpected_error_response(e, "create plan")

    @mcp.tool(
        name="get_plans",
        description=(
            "Retrieve subscription plans from Pine Labs. "
            "All parameters are optional filters."
        ),
    )
    async def get_plans(
        plan_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        amount_range: Optional[str] = None,
        frequency: Optional[str] = None,
        size: Optional[int] = None,
        page: Optional[int] = None,
        sort: Optional[str] = None,
    ) -> str:
        try:
            params: dict[str, str] = {}
            if plan_id is not None:
                params["plan_id"] = plan_id
            if start_date is not None:
                params["start_date"] = start_date
            if end_date is not None:
                params["end_date"] = end_date
            if amount_range is not None:
                params["amount[amount_range]"] = amount_range
            if frequency is not None:
                params["frequency"] = frequency
            if size is not None:
                params["size"] = str(size)
            if page is not None:
                params["page"] = str(page)
            if sort is not None:
                params["sort"] = sort

            logger.info("Fetching plans")
            response = await client.get(
                routes.PLAN_LIST,
                params=params if params else None,
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching plans: %s",
                type(e).__name__,
            )
            return unexpected_error_response(e, "get plans")

    @mcp.tool(
        name="get_plan_by_id",
        description=(
            "Retrieve a subscription plan by its plan ID "
            "from Pine Labs."
        ),
    )
    async def get_plan_by_id(plan_id: str) -> str:
        try:
            plan_id = validate_resource_id(
                plan_id, "plan_id", allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info("Fetching plan: plan_id=%s", plan_id)
            response = await client.get(
                routes.PLAN_GET.format(plan_id=plan_id),
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching plan: %s",
                type(e).__name__,
            )
            return unexpected_error_response(
                e, "get plan by id",
            )

    @mcp.tool(
        name="get_plan_by_merchant_reference",
        description=(
            "Retrieve a subscription plan by its merchant plan "
            "reference from Pine Labs."
        ),
    )
    async def get_plan_by_merchant_reference(
        merchant_plan_reference: str,
    ) -> str:
        try:
            merchant_plan_reference = validate_resource_id(
                merchant_plan_reference,
                "merchant_plan_reference",
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info(
                "Fetching plan by ref: ref=%s",
                merchant_plan_reference,
            )
            response = await client.get(
                routes.PLAN_GET_BY_REF.format(
                    ref=merchant_plan_reference,
                ),
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error: %s", type(e).__name__,
            )
            return unexpected_error_response(
                e, "get plan by merchant reference",
            )

    @mcp.tool(
        name="update_plan",
        description=(
            "Update an existing subscription plan in Pine Labs. "
            "Allows updating name, description, status, end date, "
            "max limit amount, or metadata."
        ),
    )
    async def update_plan(
        plan_id: str,
        plan_name: Optional[str] = None,
        plan_description: Optional[str] = None,
        status: Optional[str] = None,
        end_date: Optional[str] = None,
        max_limit_amount_value: Optional[int] = None,
        max_limit_amount_currency: str = "INR",
        merchant_metadata: Optional[dict[str, str]] = None,
    ) -> str:
        try:
            plan_id = validate_resource_id(
                plan_id, "plan_id", allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            max_limit = None
            if max_limit_amount_value is not None:
                max_limit = Amount(
                    value=max_limit_amount_value,
                    currency=max_limit_amount_currency,
                )
            request_body = UpdatePlanRequest(
                plan_name=plan_name,
                plan_description=plan_description,
                status=status,
                end_date=end_date,
                max_limit_amount=max_limit,
                merchant_metadata=merchant_metadata,
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info(
                "Updating plan: plan_id=%s", plan_id,
            )
            response = await client.patch(
                routes.PLAN_UPDATE.format(plan_id=plan_id),
                payload,
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error updating plan: %s",
                type(e).__name__,
            )
            return unexpected_error_response(e, "update plan")

    @mcp.tool(
        name="delete_plan",
        description=(
            "Delete a subscription plan from Pine Labs by plan ID."
        ),
    )
    async def delete_plan(plan_id: str) -> str:
        try:
            plan_id = validate_resource_id(
                plan_id, "plan_id", allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info("Deleting plan: plan_id=%s", plan_id)
            response = await client.delete(
                routes.PLAN_DELETE.format(plan_id=plan_id),
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error deleting plan: %s",
                type(e).__name__,
            )
            return unexpected_error_response(e, "delete plan")

    # -------------------------------------------------------------------
    # SUBSCRIPTIONS
    # -------------------------------------------------------------------

    @mcp.tool(
        name="create_subscription",
        description=(
            "Create a new subscription in Pine Labs against a "
            "plan. Requires merchant_subscription_reference, "
            "plan_id, start_date, end_date, customer_id, and "
            "integration_mode (SEAMLESS or REDIRECT)."
        ),
    )
    async def create_subscription(
        merchant_subscription_reference: str,
        plan_id: str,
        start_date: str,
        end_date: str,
        customer_id: str,
        integration_mode: str,
        payment_mode: Optional[str] = None,
        allowed_payment_methods: Optional[list[str]] = None,
        redirect_url: Optional[str] = None,
        failure_callback_url: Optional[str] = None,
        callback_url: Optional[str] = None,
        quantity: Optional[int] = None,
        is_tpv_enabled: Optional[bool] = None,
        bank_account_number: Optional[str] = None,
        bank_account_name: Optional[str] = None,
        bank_ifsc: Optional[str] = None,
        enable_notification: Optional[bool] = None,
        merchant_metadata: Optional[dict[str, str]] = None,
    ) -> str:
        try:
            mode = SubscriptionIntegrationMode(
                integration_mode.upper(),
            )
        except ValueError:
            return validation_error_response(
                "Invalid integration_mode. Allowed: "
                f"{[e.value for e in SubscriptionIntegrationMode]}"
            )

        try:
            bank_account = None
            if (bank_account_number
                    or bank_account_name or bank_ifsc):
                bank_account = BankAccount(
                    account_number=bank_account_number or "",
                    name=bank_account_name or "",
                    ifsc=bank_ifsc or "",
                )
            request_body = CreateSubscriptionRequest(
                merchant_subscription_reference=(
                    merchant_subscription_reference
                ),
                plan_id=plan_id,
                start_date=start_date,
                end_date=end_date,
                customer_id=customer_id,
                integration_mode=mode,
                payment_mode=payment_mode,
                allowed_payment_methods=allowed_payment_methods,
                redirect_url=redirect_url,
                failure_callback_url=failure_callback_url,
                callback_url=callback_url,
                quantity=quantity,
                is_tpv_enabled=is_tpv_enabled,
                bank_account=bank_account,
                enable_notification=enable_notification,
                merchant_metadata=merchant_metadata,
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info(
                "Creating subscription: ref=%s",
                merchant_subscription_reference,
            )
            response = await client.post(
                routes.SUBSCRIPTION_CREATE, payload,
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error creating subscription: %s",
                type(e).__name__,
            )
            return unexpected_error_response(
                e, "create subscription",
            )

    @mcp.tool(
        name="get_subscriptions",
        description=(
            "Retrieve subscriptions from Pine Labs. "
            "All parameters are optional filters."
        ),
    )
    async def get_subscriptions(
        plan_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        amount_range: Optional[str] = None,
        frequency: Optional[str] = None,
        size: Optional[int] = None,
        page: Optional[int] = None,
        sort: Optional[str] = None,
    ) -> str:
        try:
            params: dict[str, str] = {}
            if plan_id is not None:
                params["plan_id"] = plan_id
            if status is not None:
                params["status"] = status
            if start_date is not None:
                params["start_date"] = start_date
            if end_date is not None:
                params["end_date"] = end_date
            if amount_range is not None:
                params["amount[amount_range]"] = amount_range
            if frequency is not None:
                params["frequency"] = frequency
            if size is not None:
                params["size"] = str(size)
            if page is not None:
                params["page"] = str(page)
            if sort is not None:
                params["sort"] = sort

            logger.info("Fetching subscriptions")
            response = await client.get(
                routes.SUBSCRIPTION_LIST,
                params=params if params else None,
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching subscriptions: %s",
                type(e).__name__,
            )
            return unexpected_error_response(
                e, "get subscriptions",
            )

    @mcp.tool(
        name="get_subscription_by_id",
        description=(
            "Retrieve a subscription by its subscription ID "
            "from Pine Labs."
        ),
    )
    async def get_subscription_by_id(
        subscription_id: str,
    ) -> str:
        try:
            subscription_id = validate_resource_id(
                subscription_id, "subscription_id",
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info(
                "Fetching subscription: id=%s", subscription_id,
            )
            response = await client.get(
                routes.SUBSCRIPTION_GET.format(
                    subscription_id=subscription_id,
                ),
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error: %s", type(e).__name__,
            )
            return unexpected_error_response(
                e, "get subscription by id",
            )

    @mcp.tool(
        name="get_subscription_by_merchant_reference",
        description=(
            "Retrieve a subscription by its merchant subscription "
            "reference from Pine Labs."
        ),
    )
    async def get_subscription_by_merchant_reference(
        merchant_subscription_reference: str,
    ) -> str:
        try:
            merchant_subscription_reference = validate_resource_id(
                merchant_subscription_reference,
                "merchant_subscription_reference",
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info(
                "Fetching subscription by ref: ref=%s",
                merchant_subscription_reference,
            )
            response = await client.get(
                routes.SUBSCRIPTION_GET_BY_REF.format(
                    ref=merchant_subscription_reference,
                ),
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error: %s", type(e).__name__,
            )
            return unexpected_error_response(
                e,
                "get subscription by merchant reference",
            )

    @mcp.tool(
        name="pause_subscription",
        description=(
            "Pause an active subscription in Pine Labs "
            "by subscription ID."
        ),
    )
    async def pause_subscription(
        subscription_id: str,
    ) -> str:
        try:
            subscription_id = validate_resource_id(
                subscription_id, "subscription_id",
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info(
                "Pausing subscription: id=%s", subscription_id,
            )
            response = await client.post(
                routes.SUBSCRIPTION_PAUSE.format(
                    subscription_id=subscription_id,
                ),
                {},
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error pausing subscription: %s",
                type(e).__name__,
            )
            return unexpected_error_response(
                e, "pause subscription",
            )

    @mcp.tool(
        name="resume_subscription",
        description=(
            "Resume a paused subscription in Pine Labs "
            "by subscription ID."
        ),
    )
    async def resume_subscription(
        subscription_id: str,
    ) -> str:
        try:
            subscription_id = validate_resource_id(
                subscription_id, "subscription_id",
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info(
                "Resuming subscription: id=%s", subscription_id,
            )
            response = await client.post(
                routes.SUBSCRIPTION_RESUME.format(
                    subscription_id=subscription_id,
                ),
                {},
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error resuming subscription: %s",
                type(e).__name__,
            )
            return unexpected_error_response(
                e, "resume subscription",
            )

    @mcp.tool(
        name="cancel_subscription",
        description=(
            "Cancel an active subscription in Pine Labs "
            "by subscription ID."
        ),
    )
    async def cancel_subscription(
        subscription_id: str,
    ) -> str:
        try:
            subscription_id = validate_resource_id(
                subscription_id, "subscription_id",
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info(
                "Cancelling subscription: id=%s", subscription_id,
            )
            response = await client.post(
                routes.SUBSCRIPTION_CANCEL.format(
                    subscription_id=subscription_id,
                ),
                {},
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error cancelling subscription: %s",
                type(e).__name__,
            )
            return unexpected_error_response(
                e, "cancel subscription",
            )

    @mcp.tool(
        name="update_subscription",
        description=(
            "Update an existing subscription in Pine Labs. "
            "Requires subscription_id and reason. At least one "
            "of new_plan_id or new_end_date must be provided."
        ),
    )
    async def update_subscription(
        subscription_id: str,
        reason: str,
        new_plan_id: Optional[str] = None,
        new_end_date: Optional[str] = None,
    ) -> str:
        try:
            subscription_id = validate_resource_id(
                subscription_id, "subscription_id",
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            request_body = UpdateSubscriptionRequest(
                reason=reason,
                new_plan_id=new_plan_id,
                new_end_date=new_end_date,
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info(
                "Updating subscription: id=%s", subscription_id,
            )
            response = await client.patch(
                routes.SUBSCRIPTION_UPDATE.format(
                    subscription_id=subscription_id,
                ),
                payload,
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error updating subscription: %s",
                type(e).__name__,
            )
            return unexpected_error_response(
                e, "update subscription",
            )

    # -------------------------------------------------------------------
    # PRESENTATIONS
    # -------------------------------------------------------------------

    @mcp.tool(
        name="create_presentation",
        description=(
            "Create a presentation (payment request) for a "
            "subscription in Pine Labs. Requires subscription_id, "
            "due_date, amount_value, and "
            "merchant_presentation_reference."
        ),
    )
    async def create_presentation(
        subscription_id: str,
        due_date: str,
        amount_value: int,
        merchant_presentation_reference: str,
        currency: str = "INR",
    ) -> str:
        try:
            subscription_id = validate_resource_id(
                subscription_id, "subscription_id",
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            request_body = CreatePresentationRequest(
                due_date=due_date,
                amount=Amount(
                    value=amount_value, currency=currency,
                ),
                merchant_presentation_reference=(
                    merchant_presentation_reference
                ),
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info(
                "Creating presentation: sub_id=%s",
                subscription_id,
            )
            response = await client.post(
                routes.PRESENTATION_CREATE.format(
                    subscription_id=subscription_id,
                ),
                payload,
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error creating presentation: %s",
                type(e).__name__,
            )
            return unexpected_error_response(
                e, "create presentation",
            )

    @mcp.tool(
        name="get_presentation",
        description=(
            "Retrieve a presentation by its presentation ID "
            "from Pine Labs."
        ),
    )
    async def get_presentation(
        presentation_id: str,
    ) -> str:
        try:
            presentation_id = validate_resource_id(
                presentation_id, "presentation_id",
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info(
                "Fetching presentation: id=%s", presentation_id,
            )
            response = await client.get(
                routes.PRESENTATION_GET.format(
                    presentation_id=presentation_id,
                ),
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching presentation: %s",
                type(e).__name__,
            )
            return unexpected_error_response(
                e, "get presentation",
            )

    @mcp.tool(
        name="delete_presentation",
        description=(
            "Delete a presentation from Pine Labs by "
            "presentation ID."
        ),
    )
    async def delete_presentation(
        presentation_id: str,
    ) -> str:
        try:
            presentation_id = validate_resource_id(
                presentation_id, "presentation_id",
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info(
                "Deleting presentation: id=%s", presentation_id,
            )
            response = await client.delete(
                routes.PRESENTATION_DELETE.format(
                    presentation_id=presentation_id,
                ),
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error deleting presentation: %s",
                type(e).__name__,
            )
            return unexpected_error_response(
                e, "delete presentation",
            )

    @mcp.tool(
        name="get_presentations_by_subscription_id",
        description=(
            "Retrieve all presentations for a subscription "
            "from Pine Labs. Supports pagination."
        ),
    )
    async def get_presentations_by_subscription_id(
        subscription_id: str,
        size: Optional[int] = None,
        page: Optional[int] = None,
        sort: Optional[str] = None,
    ) -> str:
        try:
            subscription_id = validate_resource_id(
                subscription_id, "subscription_id",
                allow_dots=True,
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            params: dict[str, str] = {}
            if size is not None:
                params["size"] = str(size)
            if page is not None:
                params["page"] = str(page)
            if sort is not None:
                params["sort"] = sort

            logger.info(
                "Fetching presentations for sub: id=%s",
                subscription_id,
            )
            response = await client.get(
                routes.PRESENTATION_LIST_BY_SUB.format(
                    subscription_id=subscription_id,
                ),
                params=params if params else None,
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error: %s", type(e).__name__,
            )
            return unexpected_error_response(
                e,
                "get presentations by subscription id",
            )

    @mcp.tool(
        name="get_presentation_by_merchant_reference",
        description=(
            "Retrieve a presentation by its merchant "
            "presentation reference from Pine Labs."
        ),
    )
    async def get_presentation_by_merchant_reference(
        merchant_presentation_reference: str,
    ) -> str:
        try:
            merchant_presentation_reference = validate_resource_id(
                merchant_presentation_reference,
                "merchant_presentation_reference",
            )
        except ValueError as e:
            return validation_error_response(str(e))

        try:
            logger.info(
                "Fetching presentation by ref: ref=%s",
                merchant_presentation_reference,
            )
            response = await client.get(
                routes.PRESENTATION_GET_BY_REF.format(
                    ref=merchant_presentation_reference,
                ),
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error: %s", type(e).__name__,
            )
            return unexpected_error_response(
                e,
                "get presentation by merchant reference",
            )

    # -------------------------------------------------------------------
    # NOTIFICATION, DEBIT, MERCHANT RETRY
    # -------------------------------------------------------------------

    @mcp.tool(
        name="send_subscription_notification",
        description=(
            "Send a pre-debit notification for a subscription "
            "in Pine Labs. Requires subscription_id, due_date, "
            "amount_value, and merchant_presentation_reference."
        ),
    )
    async def send_subscription_notification(
        subscription_id: str,
        due_date: str,
        amount_value: int,
        merchant_presentation_reference: str,
        currency: str = "INR",
        is_merchant_retry: Optional[bool] = None,
    ) -> str:
        try:
            request_body = SubscriptionNotificationRequest(
                subscription_id=subscription_id,
                due_date=due_date,
                amount=Amount(
                    value=amount_value, currency=currency,
                ),
                merchant_presentation_reference=(
                    merchant_presentation_reference
                ),
                is_merchant_retry=is_merchant_retry,
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info(
                "Sending notification: sub_id=%s",
                subscription_id,
            )
            response = await client.post(
                routes.SUBSCRIPTION_NOTIFY,
                payload,
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error: %s", type(e).__name__,
            )
            return unexpected_error_response(
                e, "send subscription notification",
            )

    @mcp.tool(
        name="create_debit",
        description=(
            "Execute a debit (payment collection) against a "
            "subscription in Pine Labs. Requires at least one of "
            "presentation_id or merchant_presentation_reference."
        ),
    )
    async def create_debit(
        presentation_id: Optional[str] = None,
        merchant_presentation_reference: Optional[str] = None,
        is_merchant_retry: Optional[str] = None,
    ) -> str:
        try:
            request_body = CreateDebitRequest(
                presentation_id=presentation_id,
                merchant_presentation_reference=(
                    merchant_presentation_reference
                ),
                is_merchant_retry=is_merchant_retry,
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info("Creating debit")
            response = await client.post(
                routes.SUBSCRIPTION_EXECUTE,
                payload,
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error creating debit: %s",
                type(e).__name__,
            )
            return unexpected_error_response(e, "create debit")

    @mcp.tool(
        name="create_merchant_retry",
        description=(
            "Retry mandate execution for a subscription when "
            "in DEBIT FAILED stage (max 3 retries). Requires "
            "at least one of presentation_id or "
            "merchant_presentation_reference."
        ),
    )
    async def create_merchant_retry(
        presentation_id: Optional[str] = None,
        merchant_presentation_reference: Optional[str] = None,
    ) -> str:
        try:
            request_body = CreateMerchantRetryRequest(
                presentation_id=presentation_id,
                merchant_presentation_reference=(
                    merchant_presentation_reference
                ),
            )
        except (ValidationError, ValueError) as e:
            return validation_error_response(
                _sanitize_validation_error(e)
            )

        try:
            payload = request_body.model_dump(exclude_none=True)
            logger.info("Creating merchant retry")
            response = await client.post(
                routes.MANDATE_MERCHANT_RETRY, payload,
            )
            return json.dumps(response, indent=2)
        except PineLabsAPIError as e:
            logger.error(
                "Pine Labs API error: code=%s status=%d",
                e.code, e.status_code,
            )
            return api_error_response(
                e.message, e.code, e.status_code,
                e.payload or None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error creating merchant retry: %s",
                type(e).__name__,
            )
            return unexpected_error_response(
                e, "create merchant retry",
            )
