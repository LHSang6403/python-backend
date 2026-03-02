"""
Redis async client – singleton connection pool + high-level helpers.

Usage (FastAPI DI):
    from app.clients.redis import get_redis, get_cache

    async def endpoint(redis: Redis = Depends(get_redis)):
        ...

    async def endpoint(cache: RedisCache = Depends(get_cache)):
        ...
"""
import json
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()

_redis_client: Redis | None = None


# ── Lifecycle ─────────────────────────────────────────────────────────────────

async def connect_redis() -> None:
    global _redis_client
    _redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
    )
    await _redis_client.ping()


async def disconnect_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


def _get_client() -> Redis:
    if _redis_client is None:
        raise RuntimeError("Redis not initialised. Call connect_redis() first.")
    return _redis_client


# ── FastAPI dependencies ───────────────────────────────────────────────────────

async def get_redis() -> Redis:
    """Yields the raw Redis client."""
    return _get_client()


async def get_cache() -> "RedisCache":
    """Yields a high-level RedisCache wrapper."""
    return RedisCache(_get_client())


# ── High-level cache wrapper ───────────────────────────────────────────────────

class RedisCache:
    def __init__(self, client: Redis) -> None:
        self._client = client

    # -- string / raw --
    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        await self._client.set(key, value, ex=ttl)

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def delete(self, *keys: str) -> int:
        return await self._client.delete(*keys)

    async def exists(self, key: str) -> bool:
        return bool(await self._client.exists(key))

    async def expire(self, key: str, seconds: int) -> None:
        await self._client.expire(key, seconds)

    # -- json --
    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self.set(key, json.dumps(value, default=str), ttl)

    async def get_json(self, key: str) -> Any | None:
        raw = await self.get(key)
        return json.loads(raw) if raw is not None else None

    # -- hash --
    async def hset(self, name: str, mapping: dict[str, Any]) -> None:
        await self._client.hset(name, mapping={k: str(v) for k, v in mapping.items()})

    async def hgetall(self, name: str) -> dict[str, str]:
        return await self._client.hgetall(name)

    # -- list / queue --
    async def lpush(self, key: str, *values: str) -> int:
        return await self._client.lpush(key, *values)

    async def rpop(self, key: str) -> str | None:
        return await self._client.rpop(key)
