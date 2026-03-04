"""Sliding-window rate limiter middleware using Redis sorted sets."""
from __future__ import annotations

import time
import uuid

from jose import jwt
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.clients.redis import _get_client
from app.core.config import get_settings

settings = get_settings()

# Paths to skip
_SKIP_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/api/v1/health", "/graphql")


def _classify_request(path: str, method: str) -> tuple[str, int]:
    """Return (category, limit_per_minute) based on path and method."""
    if "/auth/" in path:
        return "auth", settings.rate_limit_auth_per_minute
    if method in ("POST", "PUT", "PATCH", "DELETE"):
        return "write", settings.rate_limit_write_per_minute
    return "read", settings.rate_limit_read_per_minute


def _extract_identifier(request: Request) -> str:
    """Try to extract user ID from JWT; fall back to client IP."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                options={"verify_exp": False},
            )
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        method = request.method

        # Skip non-API / docs / health endpoints
        if any(path.startswith(prefix) for prefix in _SKIP_PREFIXES):
            return await call_next(request)

        identifier = _extract_identifier(request)
        category, limit = _classify_request(path, method)
        key = f"rate_limit:{identifier}:{category}"
        window = 60  # seconds

        try:
            redis = _get_client()
            now = time.time()
            window_start = now - window

            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(uuid.uuid4()): now})
            pipe.expire(key, window)
            results = await pipe.execute()

            current_count = results[1]  # ZCARD result

            # Build rate-limit headers
            remaining = max(0, limit - current_count - 1)
            reset_at = int(now + window)
            headers = {
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_at),
            }

            if current_count >= limit:
                retry_after = int(window_start + window - now) + 1
                headers["Retry-After"] = str(retry_after)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"},
                    headers=headers,
                )

            response = await call_next(request)
            for k, v in headers.items():
                response.headers[k] = v
            return response

        except RuntimeError:
            # Redis not initialised – fail open
            return await call_next(request)
        except Exception as exc:
            # Redis down – fail open
            logger.warning(f"Rate limiter error (failing open): {exc}")
            return await call_next(request)
