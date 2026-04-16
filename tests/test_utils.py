"""Tests for utils/validators.py — validate_path_param."""


from pkg.pinelabs.utils.validators import validate_path_param


# ---------------------------------------------------------------------------
# validate_path_param
# ---------------------------------------------------------------------------

class TestValidatePathParam:
    def test_valid_alphanumeric(self):
        assert validate_path_param("abc123", "id") is None

    def test_valid_with_hyphens(self):
        assert validate_path_param("v1-250513055632-aa-rjIIWX", "order_id") is None

    def test_empty_value(self):
        err = validate_path_param("", "order_id")
        assert err is not None
        assert "order_id" in err

    def test_whitespace_only(self):
        err = validate_path_param("   ", "utr")
        assert err is not None

    def test_path_traversal(self):
        err = validate_path_param("../../../etc/passwd", "utr")
        assert err is not None
        assert "invalid characters" in err.lower()

    def test_special_chars_rejected(self):
        err = validate_path_param("val; DROP TABLE", "id")
        assert err is not None
        assert "invalid characters" in err.lower()

    def test_slashes_rejected(self):
        err = validate_path_param("a/b/c", "id")
        assert err is not None

    def test_max_length_enforced(self):
        """Values exceeding 128 characters should be rejected."""
        long_val = "a" * 129
        err = validate_path_param(long_val, "id")
        assert err is not None
        assert "invalid characters" in err.lower()

    def test_at_max_length_accepted(self):
        """Values exactly at 128 characters should be accepted."""
        val = "a" * 128
        assert validate_path_param(val, "id") is None
