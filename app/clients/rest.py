"""
External REST API async client – HTTPX with retry + backoff.

Usage (FastAPI DI):
    from app.clients.rest import get_rest_client, RestClient

    async def endpoint(client: RestClient = Depends(get_rest_client)):
        data = await client.get("/resource")
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx
from loguru import logger

from app.core.config import get_settings

settings = get_settings()

_http_client: httpx.AsyncClient | None = None


# ── Lifecycle ─────────────────────────────────────────────────────────────────

async def connect_http_client() -> None:
    global _http_client
    _http_client = httpx.AsyncClient(
        base_url=settings.external_api_base_url,
        headers={
            "Authorization": f"Bearer {settings.external_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=httpx.Timeout(settings.external_api_timeout),
        limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
    )
    logger.info(f"HTTP client ready → {settings.external_api_base_url}")


async def disconnect_http_client() -> None:
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None
    logger.info("HTTP client closed.")


def _get_client() -> httpx.AsyncClient:
    if _http_client is None:
        raise RuntimeError("HTTP client not initialised. Call connect_http_client() first.")
    return _http_client


# ── FastAPI dependency ────────────────────────────────────────────────────────

async def get_rest_client() -> "RestClient":
    return RestClient(_get_client())


# ── High-level client wrapper ─────────────────────────────────────────────────

class RestClient:
    """Wraps HTTPX with automatic retry and exponential backoff."""

    def __init__(self, client: httpx.AsyncClient, *, max_retries: int = 3) -> None:
        self._client = client
        self._max_retries = max_retries

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 2):
            try:
                response = await self._client.request(method, path, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500:
                    raise          # don't retry 4xx
                last_exc = exc
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_exc = exc

            wait = 2 ** (attempt - 1)   # 1s → 2s → 4s
            logger.warning(f"[attempt {attempt}] {method} {path} failed, retrying in {wait}s …")
            await asyncio.sleep(wait)

        raise last_exc  # type: ignore[misc]

    async def get(self, path: str, *, params: dict | None = None, **kw: Any) -> Any:
        return (await self._request("GET", path, params=params, **kw)).json()

    async def post(self, path: str, *, json: Any = None, **kw: Any) -> Any:
        return (await self._request("POST", path, json=json, **kw)).json()

    async def put(self, path: str, *, json: Any = None, **kw: Any) -> Any:
        return (await self._request("PUT", path, json=json, **kw)).json()

    async def patch(self, path: str, *, json: Any = None, **kw: Any) -> Any:
        return (await self._request("PATCH", path, json=json, **kw)).json()

    async def delete(self, path: str, **kw: Any) -> Any:
        return (await self._request("DELETE", path, **kw)).json()
