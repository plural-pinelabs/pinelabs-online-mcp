"""
Async HTTP client for Pine Labs API.

Simplified from the original — no circuit breaker, Prometheus, OpenTelemetry,
or PII filter. Keeps httpx with connection pooling and retry with backoff.
Includes a simple in-memory token cache (dict + TTL) replacing Redis.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

logger = logging.getLogger("pinelabs-mcp-server.client")

_RETRYABLE_STATUS_CODES = frozenset({429, 502, 503, 504})

# UUID-style client_id pattern (hex + hyphens, 32-40 chars)
_CLIENT_ID_RE = re.compile(r"^[a-fA-F0-9\-]{32,40}$")


class PineLabsAPIError(Exception):
    """Raised when Pine Labs API returns an error response."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        payload: dict | None = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.payload = payload or {}
        super().__init__(f"[{status_code}] {code}: {message}")


class _TokenEntry:
    """In-memory cached token with expiry."""

    __slots__ = ("token", "expires_at")

    def __init__(self, token: str, ttl: int) -> None:
        self.token = token
        self.expires_at = time.monotonic() + ttl

    @property
    def is_valid(self) -> bool:
        return time.monotonic() < self.expires_at


class PineLabsClient:
    """Async HTTP client for Pine Labs API with retry and in-memory token cache."""

    def __init__(
        self,
        base_url: str,
        token_url: str,
        client_id: str,
        client_secret: str,
        max_retries: int = 3,
        base_backoff: float = 1.0,
        timeout: Optional[float] = None,
        token_ttl: int = 3000,
    ) -> None:
        self.base_url = base_url
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._max_retries = max_retries
        self._base_backoff = base_backoff
        self._timeout = timeout or 30.0
        self._token_ttl = token_ttl
        self._client: httpx.AsyncClient | None = None
        self._token_cache: dict[str, _TokenEntry] = {}

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self._timeout, verify=True
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Token management (in-memory cache, replaces Redis + TokenManager)
    # ------------------------------------------------------------------

    async def _get_access_token(self) -> str:
        """Return a cached token or fetch a new one from Pine Labs."""
        if not self._client_id or not self._client_secret:
            raise RuntimeError(
                "Client credentials not configured. "
                "Set PINELABS_CLIENT_ID and PINELABS_CLIENT_SECRET "
                "or pass --client-id / --client-secret."
            )

        if not _CLIENT_ID_RE.match(self._client_id):
            raise ValueError("Invalid client_id format.")

        cached = self._token_cache.get(self._client_id)
        if cached and cached.is_valid:
            return cached.token

        token = await self._fetch_token()
        self._token_cache[self._client_id] = _TokenEntry(
            token, self._token_ttl
        )
        return token

    async def _fetch_token(self) -> str:
        payload = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "grant_type": "client_credentials",
        }
        async with httpx.AsyncClient(
            timeout=self._timeout, verify=True
        ) as http:
            response = await http.post(
                self._token_url,
                json=payload,
                headers={
                    "accept": "application/json",
                    "content-type": "application/json",
                },
            )
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to obtain access token: HTTP {response.status_code}"
            )
        data = response.json()
        return data["access_token"]

    # ------------------------------------------------------------------
    # HTTP request helpers
    # ------------------------------------------------------------------

    def _build_headers(
        self,
        bearer_token: str,
        idempotency_key: Optional[str] = None,
    ) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Request-ID": str(uuid.uuid4()),
            "Request-Timestamp": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
        idempotency_key: Optional[str] = None,
        params: dict | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        bearer_token = await self._get_access_token()
        url = f"{self.base_url}{path}"
        headers = self._build_headers(bearer_token, idempotency_key)
        if extra_headers:
            headers.update(extra_headers)
        request_id = headers["Request-ID"]
        max_attempts = 1 + self._max_retries
        last_exc: Exception | None = None

        for attempt in range(max_attempts):
            try:
                client = self._get_client()
                kwargs: dict[str, Any] = {"headers": headers}
                if payload is not None:
                    kwargs["json"] = payload
                if params is not None:
                    kwargs["params"] = params
                response = await getattr(client, method)(url, **kwargs)

                if (
                    response.status_code in _RETRYABLE_STATUS_CODES
                    and attempt < max_attempts - 1
                ):
                    wait = self._base_backoff * (2**attempt)
                    logger.warning(
                        "Retryable status %d on %s %s (attempt %d/%d). "
                        "Retrying in %.1fs | Request-ID: %s",
                        response.status_code,
                        method.upper(),
                        path,
                        attempt + 1,
                        max_attempts,
                        wait,
                        request_id,
                    )
                    await asyncio.sleep(wait)
                    continue

                return self._handle_response(response)

            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt < max_attempts - 1:
                    wait = self._base_backoff * (2**attempt)
                    logger.warning(
                        "Transient error on %s %s (attempt %d/%d): %s. "
                        "Retrying in %.1fs | Request-ID: %s",
                        method.upper(),
                        path,
                        attempt + 1,
                        max_attempts,
                        type(exc).__name__,
                        wait,
                        request_id,
                    )
                    await asyncio.sleep(wait)
                    continue
                raise PineLabsAPIError(
                    status_code=0,
                    code="CONNECTION_ERROR",
                    message=(
                        f"Failed to connect after "
                        f"{max_attempts} attempts: {exc}"
                    ),
                ) from exc

            except PineLabsAPIError:
                raise

        if last_exc:
            raise PineLabsAPIError(
                status_code=0,
                code="CONNECTION_ERROR",
                message=f"Request failed after {max_attempts} attempts",
            ) from last_exc
        raise PineLabsAPIError(
            status_code=0,
            code="UNKNOWN_ERROR",
            message="Request failed unexpectedly",
        )

    async def post(
        self,
        path: str,
        payload: dict,
        idempotency_key: Optional[str] = None,
    ) -> dict[str, Any]:
        if idempotency_key is None:
            idempotency_key = str(uuid.uuid4())
        return await self._request(
            "post", path, payload, idempotency_key
        )

    async def get(
        self,
        path: str,
        params: dict | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            "get", path, params=params, extra_headers=extra_headers
        )

    async def put(
        self,
        path: str,
        payload: dict | None = None,
        idempotency_key: Optional[str] = None,
    ) -> dict[str, Any]:
        if idempotency_key is None:
            idempotency_key = str(uuid.uuid4())
        return await self._request(
            "put", path, payload, idempotency_key
        )

    async def patch(
        self,
        path: str,
        payload: dict | None = None,
        idempotency_key: Optional[str] = None,
    ) -> dict[str, Any]:
        return await self._request(
            "patch", path, payload, idempotency_key
        )

    async def delete(
        self,
        path: str,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            "delete", path, extra_headers=extra_headers
        )

    @staticmethod
    def _handle_response(response: httpx.Response) -> dict[str, Any]:
        if 200 <= response.status_code < 300:
            if response.status_code == 204 or not response.content:
                return {}
            return response.json()

        try:
            error_body = response.json()
            raise PineLabsAPIError(
                status_code=response.status_code,
                code=error_body.get("code", "UNKNOWN_ERROR"),
                message=error_body.get(
                    "message", "Unknown error occurred"
                ),
                payload=error_body.get("additionalErrorPayload"),
            )
        except json.JSONDecodeError:
            raise PineLabsAPIError(
                status_code=response.status_code,
                code="UNKNOWN_ERROR",
                message=response.text or "Unknown error occurred",
            )
