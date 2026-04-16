"""Tests for Pydantic models in models/payment_links.py."""

import pytest
from pydantic import ValidationError

from pkg.pinelabs.models.payment_links import (
    Address,
    AddressType,
    AllowedPaymentMethod,
    Amount,
    CreatePaymentLinkRequest,
    Customer,
    ProductDetail,
)


# ---------------------------------------------------------------------------
# Amount
# ---------------------------------------------------------------------------

class TestAmount:
    def test_valid_amount(self):
        a = Amount(value=50000, currency="INR")
        assert a.value == 50000
        assert a.currency == "INR"

    def test_default_currency(self):
        a = Amount(value=100)
        assert a.currency == "INR"

    def test_minimum_value(self):
        a = Amount(value=100)
        assert a.value == 100

    def test_maximum_value(self):
        a = Amount(value=100_000_000)
        assert a.value == 100_000_000

    def test_below_minimum_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            Amount(value=99)
        assert "greater than or equal to 100" in str(exc_info.value)

    def test_above_maximum_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            Amount(value=100_000_001)
        assert "less than or equal to 100000000" in str(exc_info.value)

    def test_missing_value_raises(self):
        with pytest.raises(ValidationError):
            Amount()


# ---------------------------------------------------------------------------
# Address
# ---------------------------------------------------------------------------

class TestAddress:
    def test_full_address(self):
        addr = Address(
            address1="123 Main St",
            address2="Apt 4",
            address3="Floor 2",
            pincode="560001",
            city="Bangalore",
            state="Karnataka",
            country="India",
            full_name="John Doe",
            address_type=AddressType.HOME,
            address_category="billing",
        )
        assert addr.address1 == "123 Main St"
        assert addr.address_type == AddressType.HOME
        assert addr.address_category == "billing"

    def test_minimal_address(self):
        addr = Address()
        assert addr.address1 is None
        assert addr.city is None

    def test_address_type_enum(self):
        assert AddressType.HOME.value == "HOME"
        assert AddressType.WORK.value == "WORK"
        assert AddressType.OTHER.value == "OTHER"

    def test_pincode_too_short(self):
        with pytest.raises(ValidationError):
            Address(pincode="12")  # min_length=3

    def test_address1_too_long(self):
        with pytest.raises(ValidationError):
            Address(address1="x" * 101)  # max_length=100

    def test_city_too_long(self):
        with pytest.raises(ValidationError):
            Address(city="x" * 51)  # max_length=50

    def test_pincode_max_length(self):
        with pytest.raises(ValidationError):
            Address(pincode="1" * 12)  # max_length=11


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------

class TestCustomer:
    def test_customer_with_email(self):
        c = Customer(email_id="test@example.com")
        assert c.email_id == "test@example.com"
        assert c.mobile_number is None

    def test_customer_with_mobile(self):
        c = Customer(mobile_number="9876543210")
        assert c.mobile_number == "9876543210"
        assert c.email_id is None

    def test_customer_with_both(self):
        c = Customer(email_id="a@b.com", mobile_number="9876543210")
        assert c.email_id == "a@b.com"
        assert c.mobile_number == "9876543210"

    def test_customer_missing_email_and_mobile_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            Customer()
        assert "email_id" in str(exc_info.value) or "mobile_number" in str(exc_info.value)

    def test_customer_full_details(self):
        c = Customer(
            email_id="kevin@example.com",
            first_name="Kevin",
            last_name="Bob",
            customer_id="1234567890",
            mobile_number="9876543210",
            country_code="+91",
            billing_address=Address(address1="Billing St", city="Mumbai"),
            shipping_address=Address(address1="Shipping St", city="Delhi"),
        )
        assert c.first_name == "Kevin"
        assert c.billing_address.city == "Mumbai"
        assert c.shipping_address.city == "Delhi"

    def test_mobile_too_short(self):
        with pytest.raises(ValidationError):
            Customer(mobile_number="123")  # min_length=10

    def test_mobile_too_long(self):
        with pytest.raises(ValidationError):
            Customer(mobile_number="1" * 21)  # max_length=20

    def test_email_too_long(self):
        with pytest.raises(ValidationError):
            Customer(email_id="a" * 50 + "@b.com")  # max_length=50

    def test_customer_id_too_long(self):
        with pytest.raises(ValidationError):
            Customer(email_id="a@b.com", customer_id="x" * 20)  # max_length=19

    def test_country_code_too_long(self):
        with pytest.raises(ValidationError):
            Customer(email_id="a@b.com", country_code="+12345678")  # max_length=5


# ---------------------------------------------------------------------------
# AllowedPaymentMethod enum
# ---------------------------------------------------------------------------

class TestAllowedPaymentMethod:
    def test_all_values(self):
        expected = {"CARD", "UPI", "POINTS", "NETBANKING", "WALLET", "CREDIT_EMI", "DEBIT_EMI"}
        actual = {m.value for m in AllowedPaymentMethod}
        assert actual == expected

    def test_invalid_method(self):
        with pytest.raises(ValueError):
            AllowedPaymentMethod("BITCOIN")


# ---------------------------------------------------------------------------
# ProductDetail
# ---------------------------------------------------------------------------

class TestProductDetail:
    def test_minimal_product(self):
        p = ProductDetail(product_code="redmi_10")
        assert p.product_code == "redmi_10"
        assert p.product_amount is None

    def test_product_with_amount(self):
        p = ProductDetail(
            product_code="iphone_15",
            product_amount=Amount(value=5000000, currency="INR"),
        )
        assert p.product_amount.value == 5000000

    def test_product_with_coupon_discount(self):
        p = ProductDetail(
            product_code="iphone_15",
            product_coupon_discount_amount=Amount(value=10000, currency="INR"),
        )
        assert p.product_coupon_discount_amount.value == 10000

    def test_missing_product_code_raises(self):
        with pytest.raises(ValidationError):
            ProductDetail()


# ---------------------------------------------------------------------------
# CreatePaymentLinkRequest
# ---------------------------------------------------------------------------

class TestCreatePaymentLinkRequest:
    def test_minimal_request(self):
        req = CreatePaymentLinkRequest(
            amount=Amount(value=50000),
            merchant_payment_link_reference="ref-001",
            customer=Customer(email_id="a@b.com"),
        )
        assert req.amount.value == 50000
        assert req.merchant_payment_link_reference == "ref-001"
        assert req.description is None

    def test_full_request(self):
        req = CreatePaymentLinkRequest(
            amount=Amount(value=100000, currency="INR"),
            merchant_payment_link_reference="ref-full",
            customer=Customer(email_id="a@b.com", mobile_number="9876543210"),
            description="Test payment",
            expire_by="2026-06-01T10:00Z",
            allowed_payment_methods=[AllowedPaymentMethod.CARD, AllowedPaymentMethod.UPI],
            product_details=[ProductDetail(product_code="item_1")],
            cart_coupon_discount_amount=Amount(value=500),
            merchant_metadata={"key1": "value1"},
        )
        assert req.description == "Test payment"
        assert len(req.allowed_payment_methods) == 2
        assert len(req.product_details) == 1
        assert req.merchant_metadata["key1"] == "value1"

    def test_missing_amount_raises(self):
        with pytest.raises(ValidationError):
            CreatePaymentLinkRequest(
                merchant_payment_link_reference="ref-001",
                customer=Customer(email_id="a@b.com"),
            )

    def test_missing_customer_raises(self):
        with pytest.raises(ValidationError):
            CreatePaymentLinkRequest(
                amount=Amount(value=50000),
                merchant_payment_link_reference="ref-001",
            )

    def test_missing_reference_raises(self):
        with pytest.raises(ValidationError):
            CreatePaymentLinkRequest(
                amount=Amount(value=50000),
                customer=Customer(email_id="a@b.com"),
            )

    def test_reference_too_long_raises(self):
        with pytest.raises(ValidationError):
            CreatePaymentLinkRequest(
                amount=Amount(value=50000),
                merchant_payment_link_reference="x" * 51,
                customer=Customer(email_id="a@b.com"),
            )

    def test_reference_empty_raises(self):
        with pytest.raises(ValidationError):
            CreatePaymentLinkRequest(
                amount=Amount(value=50000),
                merchant_payment_link_reference="",
                customer=Customer(email_id="a@b.com"),
            )

    def test_exclude_none_serialization(self):
        req = CreatePaymentLinkRequest(
            amount=Amount(value=50000),
            merchant_payment_link_reference="ref-001",
            customer=Customer(email_id="a@b.com"),
        )
        data = req.model_dump(exclude_none=True)
        assert "description" not in data
        assert "expire_by" not in data
        assert "allowed_payment_methods" not in data
        assert "product_details" not in data
        assert "amount" in data
        assert "customer" in data
