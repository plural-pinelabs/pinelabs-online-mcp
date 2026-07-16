"""
Pine Labs API Documentation catalog.

Maps every public Pine Labs API to its Pine Labs Online documentation URL.
Used by the ``get_api_documentation`` and ``list_pinelabs_apis`` MCP tools
to look up and fetch documentation on demand.
"""

from pkg.pinelabs.config import DOCS_BASE_URL

API_DOCUMENTATION: dict[str, dict[str, str]] = {
    "generate_token": {
        "url": f"{DOCS_BASE_URL}/api/authentication/generate-token.md",
        "description": "Generate access token for API authentication using client credentials",
    },
    "create_order": {
        "url": f"{DOCS_BASE_URL}/api/orders/create-order.md",
        "description": "Create a new order for payment processing",
    },
    "capture_order": {
        "url": f"{DOCS_BASE_URL}/api/orders/capture-order.md",
        "description": "Capture an authorized payment order",
    },
    "cancel_order": {
        "url": f"{DOCS_BASE_URL}/api/orders/cancel-order.md",
        "description": "Cancel an existing payment order",
    },
    "get_order_by_order_id": {
        "url": f"{DOCS_BASE_URL}/api/orders/get-order-by-id.md",
        "description": "Retrieve order details by Pine Labs order ID",
    },
    "get_order_by_merchant_order_reference": {
        "url": f"{DOCS_BASE_URL}/api/orders/get-order-by-merchant-reference.md",
        "description": "Retrieve order details by merchant order reference",
    },
    "get_all_settlements": {
        "url": f"{DOCS_BASE_URL}/api/settlements/get-all-settlements.md",
        "description": "Get all settlements for a merchant account",
    },
    "get_settlements_by_utr": {
        "url": f"{DOCS_BASE_URL}/api/settlements/get-settlements-by-utr.md",
        "description": "Get settlements by UTR (Unique Transaction Reference)",
    },
    "release_settlement": {
        "url": f"{DOCS_BASE_URL}/api/split-settlements/release-settlement.md",
        "description": "Release a settlement against an order",
    },
    "cancel_settlement": {
        "url": f"{DOCS_BASE_URL}/api/split-settlements/cancel-settlement.md",
        "description": "Cancel a settlement against an order",
    },
    "create_payment_link": {
        "url": f"{DOCS_BASE_URL}/api/payment-links/create-payment-link.md",
        "description": "Create a new payment link for collecting payments",
    },
    "get_payment_link_by_payment_link_id": {
        "url": f"{DOCS_BASE_URL}/api/payment-links/get-payment-link-by-id.md",
        "description": "Get payment link details by Payment Link ID",
    },
    "cancel_payment_link": {
        "url": f"{DOCS_BASE_URL}/api/payment-links/cancel-payment-link.md",
        "description": "Cancel a payment link",
    },
    "resend_payment_link_notification": {
        "url": f"{DOCS_BASE_URL}/api/payment-links/resend-payment-link-notification.md",
        "description": "Resend payment link notification to the customer",
    },
    "get_payment_link_by_merchant_payment_link_reference": {
        "url": f"{DOCS_BASE_URL}/api/payment-links/get-payment-link-by-merchant-reference.md",
        "description": "Get payment link details by merchant payment link reference",
    },
    "hosted_checkout_create": {
        "url": f"{DOCS_BASE_URL}/api/checkout/generate-checkout-link.md",
        "description": "Create a hosted checkout session and get a redirect URL for payment",
    },
    "card_payment_create": {
        "url": f"{DOCS_BASE_URL}/api/card-payments/create-payment.md",
        "description": "Create a card payment",
    },
    "get_card_details": {
        "url": f"{DOCS_BASE_URL}/api/card-payments/get-card-details.md",
        "description": "Get card details",
    },
    "generate_otp": {
        "url": f"{DOCS_BASE_URL}/api/card-payments/generate-otp.md",
        "description": "Generate OTP for card payment",
    },
    "submit_otp": {
        "url": f"{DOCS_BASE_URL}/api/card-payments/submit-otp.md",
        "description": "Submit OTP for card payment",
    },
    "resend_otp": {
        "url": f"{DOCS_BASE_URL}/api/card-payments/resend-otp.md",
        "description": "Resend OTP for card payment",
    },
    "upi_collect_payment_create": {
        "url": f"{DOCS_BASE_URL}/api/upi-payments/create-payment.md",
        "description": "Create UPI collect payment",
    },
    "upi_intent_payment_create": {
        "url": f"{DOCS_BASE_URL}/api/upi-payments/create-payment.md",
        "description": "Create UPI intent payment",
    },
    "upi_intent_payment_qr": {
        "url": f"{DOCS_BASE_URL}/api/upi-payments/create-payment.md",
        "description": "Create UPI intent payment with QR flow",
    },
    "netbanking_payment_create": {
        "url": f"{DOCS_BASE_URL}/api/netbanking/create-payment.md",
        "description": "Create NetBanking payment",
    },
    "wallet_payment_create": {
        "url": f"{DOCS_BASE_URL}/api/wallet/create-payment.md",
        "description": "Create wallet payment",
    },
    "pay_by_point_check_balance": {
        "url": f"{DOCS_BASE_URL}/api/pay-by-points/get-payment-option.md",
        "description": "Check balance for pay by points",
    },
    "pay_by_point_payment_create": {
        "url": f"{DOCS_BASE_URL}/api/pay-by-points/get-payment-option.md",
        "description": "Create payment via pay by points",
    },
    "create_customer": {
        "url": f"{DOCS_BASE_URL}/api/customers/create-customer.md",
        "description": "Create a new customer profile",
    },
    "update_customer": {
        "url": f"{DOCS_BASE_URL}/api/customers/update-customer.md",
        "description": "Update an existing customer profile",
    },
    "get_customer_by_id": {
        "url": f"{DOCS_BASE_URL}/api/customers/get-customer-by-id.md",
        "description": "Get customer details by Customer ID",
    },
    "get_customer_details": {
        "url": f"{DOCS_BASE_URL}/api/customers/get-customer-details.md",
        "description": "Get detailed information about a customer",
    },
    "generate_card_token": {
        "url": f"{DOCS_BASE_URL}/api/tokenization/generate-card-token.md",
        "description": "Generate a token for card payments",
    },
    "get_customer_tokens_linked_to_customer_id": {
        "url": f"{DOCS_BASE_URL}/api/tokenization/get-customer-tokens-by-customer-id.md",
        "description": "Get all tokens linked to a customer ID",
    },
    "get_customer_token_by_token_id": {
        "url": f"{DOCS_BASE_URL}/api/tokenization/get-customer-token-by-token-id.md",
        "description": "Get customer token details by Token ID",
    },
    "delete_customer_token_by_customer_id": {
        "url": f"{DOCS_BASE_URL}/api/tokenization/delete-customer-token.md",
        "description": "Delete a customer token by Customer ID",
    },
    "generate_cryptogram": {
        "url": f"{DOCS_BASE_URL}/api/tokenization/generate-cryptogram.md",
        "description": "Generate a cryptogram",
    },
    "get_service_provider_token_by_customer_id": {
        "url": f"{DOCS_BASE_URL}/api/tokenization/get-service-provider-token.md",
        "description": "Get service provider token by Customer ID",
    },
    "get_service_provider_token_by_token_id": {
        "url": f"{DOCS_BASE_URL}/api/tokenization/get-service-provider-token.md",
        "description": "Get service provider token by Token ID",
    },
    "delete_token_by_token_id": {
        "url": f"{DOCS_BASE_URL}/api/tokenization/delete-token-by-token-id.md",
        "description": "Delete service provider token by Token ID",
    },
    "calculate_convenience_fee": {
        "url": f"{DOCS_BASE_URL}/api/convenience-fee/calculate-convenience-fee.md",
        "description": "Calculate convenience fee for a payment",
    },
    "affordability_suite_offer_discovery": {
        "url": f"{DOCS_BASE_URL}/api/affordability-suite/create-offer-discovery.md",
        "description": "Discover offers available on cart amount or product and calculate EMI",
    },
    "affordability_suite_offer_discovery_cardless": {
        "url": f"{DOCS_BASE_URL}/api/affordability-suite/create-cardless-offer-discovery.md",
        "description": "Discover cardless offers available on a product and calculate EMI",
    },
    "affordability_suite_offer_validation": {
        "url": f"{DOCS_BASE_URL}/api/affordability-suite/offer-validation-create.md",
        "description": "Validate applied offers",
    },
    "affordability_suite_create_order": {
        "url": f"{DOCS_BASE_URL}/api/affordability-suite/create-offer-discovery-v2.md",
        "description": "Create an order via affordability suite",
    },
    "affordability_suite_create_payment": {
        "url": f"{DOCS_BASE_URL}/api/affordability-suite/create-offer-discovery.md",
        "description": "Initiate a card payment via affordability suite",
    },
    "affordability_suite_imei_validation": {
        "url": f"{DOCS_BASE_URL}/api/affordability-suite/create-imeivalidation.md",
        "description": "Validate IMEI via affordability suite",
    },
    "subscriptions_create_plan": {
        "url": f"{DOCS_BASE_URL}/api/subscriptions-plans/create-plan.md",
        "description": "Create a subscription plan",
    },
    "subscriptions_get_all_plans": {
        "url": f"{DOCS_BASE_URL}/api/subscriptions-plans/list-plans.md",
        "description": "Get all available subscription plans",
    },
    "subscriptions_get_specific_plan": {
        "url": f"{DOCS_BASE_URL}/api/subscriptions-plans/get-plan-by-id.md",
        "description": "Get a specific subscription plan",
    },
    "subscriptions_update_plan": {
        "url": f"{DOCS_BASE_URL}/api/subscriptions-plans/update-plan.md",
        "description": "Update a subscription plan",
    },
    "subscriptions_delete_plan": {
        "url": f"{DOCS_BASE_URL}/api/subscriptions-plans/delete-plan.md",
        "description": "Delete a subscription plan",
    },
    "create_subscription": {
        "url": f"{DOCS_BASE_URL}/api/subscriptions-subscriptions/create-subscription.md",
        "description": "Create a subscription against a plan",
    },
    "get_all_subscriptions": {
        "url": f"{DOCS_BASE_URL}/api/subscriptions-subscriptions/list-subscriptions.md",
        "description": "Get all available subscriptions",
    },
    "get_specific_subscription": {
        "url": f"{DOCS_BASE_URL}/api/subscriptions-subscriptions/get-subscription-by-id.md",
        "description": "Get a specific subscription",
    },
    "pause_subscription": {
        "url": f"{DOCS_BASE_URL}/api/subscriptions-subscriptions/pause-subscription.md",
        "description": "Pause a subscription",
    },
    "resume_subscription": {
        "url": f"{DOCS_BASE_URL}/api/subscriptions-subscriptions/resume-subscription.md",
        "description": "Resume a paused subscription",
    },
    "subscription_create_merchant_retry": {
        "url": f"{DOCS_BASE_URL}/api/subscriptions-presentations/create-merchant-retry.md",
        "description": "Retry mandate execution for a subscription after automatic retries are exhausted",
    },
    "subscriptions_create_presentation": {
        "url": f"{DOCS_BASE_URL}/api/subscriptions-presentations/create-presentation.md",
        "description": "Submit mandate debit requests for AS and OT frequency transactions",
    },
    "subscriptions_get_presentation": {
        "url": f"{DOCS_BASE_URL}/api/subscriptions-presentations/get-presentation-by-id.md",
        "description": "Get a presentation request",
    },
    "subscriptions_delete_presentation": {
        "url": f"{DOCS_BASE_URL}/api/subscriptions-presentations/delete-presentation.md",
        "description": "Delete a presentation request",
    },
    "subscriptions_get_presentation_by_subscription_id": {
        "url": f"{DOCS_BASE_URL}/api/subscriptions-presentations/list-presentations-by-subscription.md",
        "description": "Get presentation requests by subscription ID",
    },
}