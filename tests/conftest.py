"""Shared fixtures for Pine Labs MCP Server tests."""

from unittest.mock import AsyncMock

import pytest

from pkg.pinelabs.client import PineLabsClient


class _FakeMCP:
    """Lightweight stub that captures tool registrations."""

    def __init__(self) -> None:
        self.tools: dict[str, object] = {}

    def tool(self, name: str, description: str):
        def decorator(fn):
            self.tools[name] = fn
            return fn
        return decorator


@pytest.fixture
def pinelabs_client():
    """Create a PineLabsClient pointed at a fake base URL."""
    return PineLabsClient(
        base_url="https://fake.pinelabs.test/api",
        token_url="https://fake.pinelabs.test/api/auth/v1/token",
        client_id="test-client-id",
        client_secret="test-client-secret",
        max_retries=0,
    )


@pytest.fixture()
def fake_mcp() -> _FakeMCP:
    return _FakeMCP()


@pytest.fixture()
def mock_client() -> AsyncMock:
    return AsyncMock(spec=PineLabsClient)
