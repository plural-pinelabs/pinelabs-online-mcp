"""Tests for utils/errors.py — structured error response utilities."""

import json

from pkg.pinelabs.utils.errors import (
    error_response,
    api_error_response,
    validation_error_response,
    unexpected_error_response,
)


class TestErrorResponse:
    def test_basic_error(self):
        result = json.loads(error_response(error="Something failed"))
        assert result["error"] == "Something failed"
        assert result["code"] == "INTERNAL_ERROR"
        assert "status_code" not in result

    def test_with_status_code(self):
        result = json.loads(
            error_response(error="Bad input", code="BAD_REQUEST", status_code=400)
        )
        assert result["code"] == "BAD_REQUEST"
        assert result["status_code"] == 400

    def test_with_details(self):
        result = json.loads(
            error_response(error="err", details={"field": "amount"})
        )
        assert result["details"] == {"field": "amount"}


class TestApiErrorResponse:
    def test_shape(self):
        result = json.loads(api_error_response("Not found", "NOT_FOUND", 404))
        assert result["error"] == "Not found"
        assert result["code"] == "NOT_FOUND"
        assert result["status_code"] == 404

    def test_with_details(self):
        result = json.loads(
            api_error_response("err", "ERR", 400, details={"min": 100})
        )
        assert result["details"] == {"min": 100}


class TestValidationErrorResponse:
    def test_shape(self):
        result = json.loads(validation_error_response("Field required"))
        assert result["error"] == "Field required"
        assert result["code"] == "VALIDATION_ERROR"
        assert result["status_code"] == 422


class TestUnexpectedErrorResponse:
    def test_shape(self):
        result = json.loads(
            unexpected_error_response(RuntimeError("boom"), "create link")
        )
        assert "internal error" in result["error"].lower()
        assert "create link" in result["error"]
        assert "boom" not in result["error"]
        assert result["code"] == "INTERNAL_ERROR"
        assert result["status_code"] == 500

    def test_default_context(self):
        result = json.loads(unexpected_error_response(RuntimeError("x")))
        assert "operation" in result["error"]
