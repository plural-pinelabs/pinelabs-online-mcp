"""Tests for utils/validators.py — shared validation utilities."""

from datetime import datetime, timedelta, timezone

import pytest

from pkg.pinelabs.utils.validators import (
    validate_resource_id,
    validate_expire_by,
)


# ---------------------------------------------------------------------------
# validate_resource_id
# ---------------------------------------------------------------------------

class TestValidateResourceId:
    def test_valid_id(self):
        assert validate_resource_id("pl-123", "payment_link_id") == "pl-123"

    def test_alphanumeric(self):
        assert validate_resource_id("abc123", "id") == "abc123"

    def test_dots_and_underscores(self):
        assert validate_resource_id("ref.001_test", "ref", allow_dots=True) == "ref.001_test"

    def test_dots_rejected_by_default(self):
        with pytest.raises(ValueError, match="invalid characters"):
            validate_resource_id("ref.001", "merchant_ref")

    def test_strips_whitespace(self):
        assert validate_resource_id("  pl-123  ", "id") == "pl-123"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="required and must not be empty"):
            validate_resource_id("", "id")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="required and must not be empty"):
            validate_resource_id("   ", "id")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="at most 50 characters"):
            validate_resource_id("x" * 51, "id")

    def test_custom_max_length(self):
        with pytest.raises(ValueError, match="at most 10 characters"):
            validate_resource_id("x" * 11, "id", max_length=10)

    def test_unsafe_chars_slash(self):
        with pytest.raises(ValueError, match="invalid characters"):
            validate_resource_id("../etc/passwd", "id")

    def test_unsafe_chars_space(self):
        # After strip, "a b" still has space in the middle
        with pytest.raises(ValueError, match="invalid characters"):
            validate_resource_id("a b", "id")

    def test_unsafe_chars_semicolon(self):
        with pytest.raises(ValueError, match="invalid characters"):
            validate_resource_id("id;DROP", "id")

    def test_field_name_in_error(self):
        with pytest.raises(ValueError, match="order_id"):
            validate_resource_id("", "order_id")


# ---------------------------------------------------------------------------
# validate_expire_by
# ---------------------------------------------------------------------------

class TestValidateExpireBy:
    def test_valid_future_timestamp(self):
        future = (datetime.now(timezone.utc) + timedelta(days=10)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        # Should not raise
        validate_expire_by(future)

    def test_valid_with_offset(self):
        future = (datetime.now(timezone.utc) + timedelta(days=10)).strftime(
            "%Y-%m-%dT%H:%M:%S+00:00"
        )
        validate_expire_by(future)

    def test_past_timestamp_raises(self):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        with pytest.raises(ValueError, match="future timestamp"):
            validate_expire_by(past)

    def test_too_far_future_raises(self):
        far_future = (datetime.now(timezone.utc) + timedelta(days=200)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        with pytest.raises(ValueError, match="within 180 days"):
            validate_expire_by(far_future)

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="valid ISO 8601"):
            validate_expire_by("not-a-date")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="valid ISO 8601"):
            validate_expire_by("")

    def test_naive_datetime_treated_as_utc(self):
        """A valid ISO 8601 without timezone info should be treated as UTC."""
        future = (datetime.now(timezone.utc) + timedelta(days=10)).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        # No Z or offset — should still work (treated as UTC)
        validate_expire_by(future)
