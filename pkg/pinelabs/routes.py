"""
Centralized API route constants for all Pine Labs endpoints.

Every API path used by tool modules is defined here so that
source files contain no inline endpoint strings.
"""

# ---------------------------------------------------------------------------
# Payment Links  (/pay/v1/paymentlink)
# ---------------------------------------------------------------------------
PAYMENT_LINK_CREATE = "/pay/v1/paymentlink"
PAYMENT_LINK_GET = "/pay/v1/paymentlink/{payment_link_id}"
PAYMENT_LINK_GET_BY_REF = "/pay/v1/paymentlink/ref/{ref}"
PAYMENT_LINK_CANCEL = "/pay/v1/paymentlink/{payment_link_id}/cancel"
PAYMENT_LINK_NOTIFY = "/pay/v1/paymentlink/{payment_link_id}/notify"

# ---------------------------------------------------------------------------
# Orders  (/pay/v1/orders)
# ---------------------------------------------------------------------------
ORDER_CREATE = "/pay/v1/orders"
ORDER_GET = "/pay/v1/orders/{order_id}"
ORDER_CANCEL = "/pay/v1/orders/{order_id}/cancel"
ORDER_PAYMENTS = "/pay/v1/orders/{order_id}/payments"

# ---------------------------------------------------------------------------
# Checkout Orders  (/checkout/v1/orders)
# ---------------------------------------------------------------------------
CHECKOUT_ORDER_CREATE = "/checkout/v1/orders"

# ---------------------------------------------------------------------------
# Subscriptions  (/v1/public/...)
# ---------------------------------------------------------------------------
_SUB_PREFIX = "/v1/public"

PLAN_CREATE = f"{_SUB_PREFIX}/plans"
PLAN_LIST = f"{_SUB_PREFIX}/plans"
PLAN_GET = f"{_SUB_PREFIX}/plans/{{plan_id}}"
PLAN_GET_BY_REF = f"{_SUB_PREFIX}/plans/reference/{{ref}}"
PLAN_UPDATE = f"{_SUB_PREFIX}/plans/{{plan_id}}"
PLAN_DELETE = f"{_SUB_PREFIX}/plans/{{plan_id}}"

SUBSCRIPTION_CREATE = f"{_SUB_PREFIX}/subscriptions"
SUBSCRIPTION_LIST = f"{_SUB_PREFIX}/subscriptions"
SUBSCRIPTION_GET = f"{_SUB_PREFIX}/subscriptions/{{subscription_id}}"
SUBSCRIPTION_GET_BY_REF = (
    f"{_SUB_PREFIX}/subscriptions/reference/{{ref}}"
)
SUBSCRIPTION_PAUSE = (
    f"{_SUB_PREFIX}/subscriptions/{{subscription_id}}/pause"
)
SUBSCRIPTION_RESUME = (
    f"{_SUB_PREFIX}/subscriptions/{{subscription_id}}/resume"
)
SUBSCRIPTION_CANCEL = (
    f"{_SUB_PREFIX}/subscriptions/{{subscription_id}}/cancel"
)
SUBSCRIPTION_UPDATE = (
    f"{_SUB_PREFIX}/subscriptions/{{subscription_id}}"
)

PRESENTATION_CREATE = (
    f"{_SUB_PREFIX}/subscriptions/{{subscription_id}}/presentations"
)
PRESENTATION_GET = f"{_SUB_PREFIX}/presentations/{{presentation_id}}"
PRESENTATION_DELETE = (
    f"{_SUB_PREFIX}/presentations/{{presentation_id}}"
)
PRESENTATION_LIST_BY_SUB = (
    f"{_SUB_PREFIX}/subscriptions/{{subscription_id}}/presentations"
)
PRESENTATION_GET_BY_REF = (
    f"{_SUB_PREFIX}/presentations/reference/{{ref}}"
)

SUBSCRIPTION_NOTIFY = f"{_SUB_PREFIX}/subscriptions/notify"
SUBSCRIPTION_EXECUTE = f"{_SUB_PREFIX}/subscriptions/execute"

MANDATE_MERCHANT_RETRY = "/v1/mandate/merchant-retry"

# ---------------------------------------------------------------------------
# MCP API / Reports  (/mcp/v1/...)
# ---------------------------------------------------------------------------
MCP_PAYMENT_LINK_DETAILS = "/mcp/v1/payment-link/details"
MCP_ORDER_DETAILS = "/mcp/v1/order/details"
MCP_REFUND_ORDER_DETAILS = "/mcp/v1/refund/order/details"
MCP_SEARCH_TRANSACTION = "/mcp/v1/search/transaction/{transaction_id}"

# ---------------------------------------------------------------------------
# Success Rate  (/mcp/v1/merchant/...)
# ---------------------------------------------------------------------------
SUCCESS_RATE = "/mcp/v1/merchant/transactions/success-rate"
