"""
Health-check endpoints.

GET /api/v1/health        – liveness (always 200 if app is up)
GET /api/v1/health/ready  – readiness (checks Postgres + Redis)
"""
from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.postgres import get_db
from app.clients.redis import get_redis

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="Liveness probe")
async def liveness() -> dict:
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe – checks Postgres & Redis")
async def readiness(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    try:
        await redis.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    return {
        "status": "ready" if (db_ok and redis_ok) else "degraded",
        "postgres": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
    }
