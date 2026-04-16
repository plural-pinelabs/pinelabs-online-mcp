"""
Pine Labs API Documentation catalog.

Maps every public Pine Labs API to its developer-portal markdown URL.
Used by the ``get_api_documentation`` and ``list_pinelabs_apis`` MCP tools
to look up and fetch documentation on demand.
"""

from pkg.pinelabs.config import DOCS_BASE_URL

API_DOCUMENTATION: dict[str, dict[str, str]] = {
    "generate_token": {
        "url": f"{DOCS_BASE_URL}/reference/generate-token.md",
        "description": "Generate access token for API authentication using client credentials",
    },
    "create_order": {
        "url": f"{DOCS_BASE_URL}/reference/orders-create.md",
        "description": "Create a new order for payment processing",
    },
    "capture_order": {
        "url": f"{DOCS_BASE_URL}/reference/orders-capture.md",
        "description": "Capture an authorized payment order",
    },
    "cancel_order": {
        "url": f"{DOCS_BASE_URL}/reference/orders-cancel.md",
        "description": "Cancel an existing payment order",
    },
    "get_order_by_order_id": {
        "url": f"{DOCS_BASE_URL}/reference/orders-get-by-order-id.md",
        "description": "Retrieve order details by Pine Labs order ID",
    },
    "get_order_by_merchant_order_reference": {
        "url": f"{DOCS_BASE_URL}/reference/orders-get-by-merchant-order-reference.md",
        "description": "Retrieve order details by merchant order reference",
    },
    "get_all_settlements": {
        "url": f"{DOCS_BASE_URL}/reference/get-all-settlements.md",
        "description": "Get all settlements for a merchant account",
    },
    "get_settlements_by_utr": {
        "url": f"{DOCS_BASE_URL}/reference/get-settlements-by-utr.md",
        "description": "Get settlements by UTR (Unique Transaction Reference)",
    },
    "release_settlement": {
        "url": f"{DOCS_BASE_URL}/reference/release-settlement.md",
        "description": "Release a settlement against an order",
    },
    "cancel_settlement": {
        "url": f"{DOCS_BASE_URL}/reference/cancel-settlement.md",
        "description": "Cancel a settlement against an order",
    },
    "create_payment_link": {
        "url": f"{DOCS_BASE_URL}/reference/payment-link-create.md",
        "description": "Create a new payment link for collecting payments",
    },
    "get_payment_link_by_payment_link_id": {
        "url": f"{DOCS_BASE_URL}/reference/payment-link-get-by-payment-link-id.md",
        "description": "Get payment link details by Payment Link ID",
    },
    "cancel_payment_link": {
        "url": f"{DOCS_BASE_URL}/reference/payment-link-cancel.md",
        "description": "Cancel a payment link",
    },
    "resend_payment_link_notification": {
        "url": f"{DOCS_BASE_URL}/reference/payment-link-resend.md",
        "description": "Resend payment link notification to the customer",
    },
    "get_payment_link_by_merchant_payment_link_reference": {
        "url": f"{DOCS_BASE_URL}/reference/payment-link-get-by-merchant-payment-link-reference.md",
        "description": "Get payment link details by merchant payment link reference",
    },
    "hosted_checkout_create": {
        "url": f"{DOCS_BASE_URL}/reference/hosted-checkout-create.md",
        "description": "Create a hosted checkout session and get a redirect URL for payment",
    },
    "card_payment_create": {
        "url": f"{DOCS_BASE_URL}/reference/card-payment-create.md",
        "description": "Create a card payment",
    },
    "get_card_details": {
        "url": f"{DOCS_BASE_URL}/reference/get-card-details.md",
        "description": "Get card details",
    },
    "generate_otp": {
        "url": f"{DOCS_BASE_URL}/reference/card-payments-generate-otp.md",
        "description": "Generate OTP for card payment",
    },
    "submit_otp": {
        "url": f"{DOCS_BASE_URL}/reference/card-payments-submit-otp.md",
        "description": "Submit OTP for card payment",
    },
    "resend_otp": {
        "url": f"{DOCS_BASE_URL}/reference/card-payments-resend-otp.md",
        "description": "Resend OTP for card payment",
    },
    "upi_collect_payment_create": {
        "url": f"{DOCS_BASE_URL}/reference/upi-payments-collect.md",
        "description": "Create UPI collect payment",
    },
    "upi_intent_payment_create": {
        "url": f"{DOCS_BASE_URL}/reference/upi-payments-intent.md",
        "description": "Create UPI intent payment",
    },
    "upi_intent_payment_qr": {
        "url": f"{DOCS_BASE_URL}/reference/create-intent-payment-with-qr-image.md",
        "description": "Create UPI intent payment with QR flow",
    },
    "netbanking_payment_create": {
        "url": f"{DOCS_BASE_URL}/reference/create-netbanking-payment.md",
        "description": "Create NetBanking payment",
    },
    "wallet_payment_create": {
        "url": f"{DOCS_BASE_URL}/reference/create-wallet-payment.md",
        "description": "Create wallet payment",
    },
    "pay_by_point_check_balance": {
        "url": f"{DOCS_BASE_URL}/reference/pay-by-point-check-point-balance.md",
        "description": "Check balance for pay by points",
    },
    "pay_by_point_payment_create": {
        "url": f"{DOCS_BASE_URL}/reference/pay-by-point-payment-create.md",
        "description": "Create payment via pay by points",
    },
    "create_customer": {
        "url": f"{DOCS_BASE_URL}/reference/customer-create.md",
        "description": "Create a new customer profile",
    },
    "update_customer": {
        "url": f"{DOCS_BASE_URL}/reference/customer-update.md",
        "description": "Update an existing customer profile",
    },
    "get_customer_by_id": {
        "url": f"{DOCS_BASE_URL}/reference/get-customer-by-customer-id.md",
        "description": "Get customer details by Customer ID",
    },
    "get_customer_details": {
        "url": f"{DOCS_BASE_URL}/reference/get-customer-details.md",
        "description": "Get detailed information about a customer",
    },
    "generate_card_token": {
        "url": f"{DOCS_BASE_URL}/reference/generate-card-token.md",
        "description": "Generate a token for card payments",
    },
    "get_customer_tokens_linked_to_customer_id": {
        "url": f"{DOCS_BASE_URL}/reference/get-customer-token-by-customer-id.md",
        "description": "Get all tokens linked to a customer ID",
    },
    "get_customer_token_by_token_id": {
        "url": f"{DOCS_BASE_URL}/reference/get-customer-token-by-token-id.md",
        "description": "Get customer token details by Token ID",
    },
    "delete_customer_token_by_customer_id": {
        "url": f"{DOCS_BASE_URL}/reference/delete-customer-token.md",
        "description": "Delete a customer token by Customer ID",
    },
    "generate_cryptogram": {
        "url": f"{DOCS_BASE_URL}/reference/generate-cryptogram.md",
        "description": "Generate a cryptogram",
    },
    "get_service_provider_token_by_customer_id": {
        "url": f"{DOCS_BASE_URL}/reference/get-token-by-customer-id.md",
        "description": "Get service provider token by Customer ID",
    },
    "get_service_provider_token_by_token_id": {
        "url": f"{DOCS_BASE_URL}/reference/get-token-by-token-id.md",
        "description": "Get service provider token by Token ID",
    },
    "delete_token_by_token_id": {
        "url": f"{DOCS_BASE_URL}/reference/delete-token-by-token-id.md",
        "description": "Delete service provider token by Token ID",
    },
    "calculate_convenience_fee": {
        "url": f"{DOCS_BASE_URL}/reference/calculate-convenience-fee.md",
        "description": "Calculate convenience fee for a payment",
    },
    "affordability_suite_offer_discovery": {
        "url": f"{DOCS_BASE_URL}/reference/offer-discovery-create.md",
        "description": "Discover offers available on cart amount or product and calculate EMI",
    },
    "affordability_suite_offer_discovery_cardless": {
        "url": f"{DOCS_BASE_URL}/reference/offer-discovery-cardless-create.md",
        "description": "Discover cardless offers available on a product and calculate EMI",
    },
    "affordability_suite_offer_validation": {
        "url": f"{DOCS_BASE_URL}/reference/offer-validation-create.md",
        "description": "Validate applied offers",
    },
    "affordability_suite_create_order": {
        "url": f"{DOCS_BASE_URL}/reference/affordability-suite-orders-create.md",
        "description": "Create an order via affordability suite",
    },
    "affordability_suite_create_payment": {
        "url": f"{DOCS_BASE_URL}/reference/affordability-suite-create-payment.md",
        "description": "Initiate a card payment via affordability suite",
    },
    "affordability_suite_imei_validation": {
        "url": f"{DOCS_BASE_URL}/reference/imei-validation-create.md",
        "description": "Validate IMEI via affordability suite",
    },
    "subscriptions_create_plan": {
        "url": f"{DOCS_BASE_URL}/reference/create-plan.md",
        "description": "Create a subscription plan",
    },
    "subscriptions_get_all_plans": {
        "url": f"{DOCS_BASE_URL}/reference/get-all-plans.md",
        "description": "Get all available subscription plans",
    },
    "subscriptions_get_specific_plan": {
        "url": f"{DOCS_BASE_URL}/reference/get-specific-plan.md",
        "description": "Get a specific subscription plan",
    },
    "subscriptions_update_plan": {
        "url": f"{DOCS_BASE_URL}/reference/update-plan.md",
        "description": "Update a subscription plan",
    },
    "subscriptions_delete_plan": {
        "url": f"{DOCS_BASE_URL}/reference/delete-plan.md",
        "description": "Delete a subscription plan",
    },
    "create_subscription": {
        "url": f"{DOCS_BASE_URL}/reference/create-subscription.md",
        "description": "Create a subscription against a plan",
    },
    "get_all_subscriptions": {
        "url": f"{DOCS_BASE_URL}/reference/get-all-subscriptions.md",
        "description": "Get all available subscriptions",
    },
    "get_specific_subscription": {
        "url": f"{DOCS_BASE_URL}/reference/get-specific-subscription.md",
        "description": "Get a specific subscription",
    },
    "pause_subscription": {
        "url": f"{DOCS_BASE_URL}/reference/pause-subscription.md",
        "description": "Pause a subscription",
    },
    "resume_subscription": {
        "url": f"{DOCS_BASE_URL}/reference/resume-subscription.md",
        "description": "Resume a paused subscription",
    },
    "subscription_create_merchant_retry": {
        "url": f"{DOCS_BASE_URL}/reference/create-merchant-retry.md",
        "description": "Retry mandate execution for a subscription after automatic retries are exhausted",
    },
    "subscriptions_create_presentation": {
        "url": f"{DOCS_BASE_URL}/reference/create-presentation.md",
        "description": "Submit mandate debit requests for AS and OT frequency transactions",
    },
    "subscriptions_get_presentation": {
        "url": f"{DOCS_BASE_URL}/reference/get-presentation.md",
        "description": "Get a presentation request",
    },
    "subscriptions_delete_presentation": {
        "url": f"{DOCS_BASE_URL}/reference/delete-presentation.md",
        "description": "Delete a presentation request",
    },
    "subscriptions_get_presentation_by_subscription_id": {
        "url": f"{DOCS_BASE_URL}/reference/get-presentation-by-subscription-id.md",
        "description": "Get presentation requests by subscription ID",
    },
}
