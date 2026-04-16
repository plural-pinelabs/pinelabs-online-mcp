"""Tests for config.py — Settings and Environment."""

import os
from unittest.mock import patch


from pkg.pinelabs.config import Environment, BASE_URLS, Settings


class TestEnvironmentEnum:
    def test_uat(self):
        assert Environment.UAT.value == "uat"

    def test_prod(self):
        assert Environment.PROD.value == "prod"


class TestBaseURLs:
    def test_uat_url(self):
        assert BASE_URLS[Environment.UAT] == "https://pluraluat.v2.pinepg.in/api"

    def test_prod_url(self):
        assert BASE_URLS[Environment.PROD] == "https://api.pluralpay.in/api"


class TestSettings:
    @patch.dict(os.environ, {
        "PINELABS_ENV": "uat",
        "LOG_LEVEL": "debug",
    }, clear=True)
    def test_uat_settings(self):
        s = Settings()
        assert s.environment == Environment.UAT
        assert s.base_url == BASE_URLS[Environment.UAT]
        assert s.log_level == "DEBUG"

    @patch.dict(os.environ, {"PINELABS_ENV": "prod"}, clear=True)
    def test_prod_settings(self):
        s = Settings()
        assert s.environment == Environment.PROD
        assert s.base_url == BASE_URLS[Environment.PROD]

    @patch.dict(os.environ, {
        "PINELABS_ENV": "invalid_env_value",
    }, clear=True)
    def test_invalid_env_falls_back_to_uat(self):
        s = Settings()
        assert s.environment == Environment.UAT

    @patch.dict(os.environ, {
        "PINELABS_BASE_URL": "https://custom.url/api",
    }, clear=False)
    def test_custom_base_url_override(self):
        s = Settings()
        assert s.base_url == "https://custom.url/api"

    @patch.dict(os.environ, {}, clear=True)
    def test_all_defaults(self):
        s = Settings()
        assert s.environment == Environment.UAT
        assert s.log_level == "INFO"
        assert s.base_url == BASE_URLS[Environment.UAT]
        assert s.http_timeout == 30.0

    @patch.dict(os.environ, {"PINELABS_ENV": "UAT"}, clear=True)
    def test_uppercase_env_is_lowered(self):
        s = Settings()
        assert s.environment == Environment.UAT

    @patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}, clear=True)
    def test_log_level_uppercased(self):
        s = Settings()
        assert s.log_level == "WARNING"

    @patch.dict(os.environ, {"HTTP_TIMEOUT": "15.0"}, clear=True)
    def test_http_timeout_from_env(self):
        s = Settings()
        assert s.http_timeout == 15.0

    @patch.dict(os.environ, {}, clear=True)
    def test_http_timeout_default(self):
        s = Settings()
        assert s.http_timeout == 30.0

    def test_constructor_overrides(self):
        s = Settings(
            client_id="my-id",
            client_secret="my-secret",
            environment="prod",
        )
        assert s.client_id == "my-id"
        assert s.client_secret == "my-secret"
        assert s.environment == Environment.PROD
