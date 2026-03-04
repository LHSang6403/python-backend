"""PASETO authentication business logic."""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.paseto_security import (
    PasetoError,
    create_paseto_access_token,
    create_paseto_refresh_token,
    decode_paseto_token,
)
from app.core.security import verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse

settings = get_settings()

REFRESH_KEY = "paseto_refresh_token:{jti}"
BLACKLIST_KEY = "paseto_blacklist:{jti}"


async def login(
    db: AsyncSession,
    redis: Redis,
    email: str,
    password: str,
) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    user_id = str(user.id)
    access_token, _access_jti, _access_exp = create_paseto_access_token(user_id)
    refresh_token, refresh_jti, _refresh_exp = create_paseto_refresh_token(user_id)

    refresh_ttl = settings.paseto_refresh_token_expire_days * 86400
    await redis.set(
        REFRESH_KEY.format(jti=refresh_jti),
        user_id,
        ex=refresh_ttl,
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def logout(
    redis: Redis,
    access_payload: dict,
    refresh_token: str | None = None,
) -> None:
    access_jti = access_payload["jti"]
    exp_dt = datetime.fromisoformat(access_payload["exp"])
    remaining = int((exp_dt - datetime.now(timezone.utc)).total_seconds())
    if remaining > 0:
        await redis.set(BLACKLIST_KEY.format(jti=access_jti), "1", ex=remaining)

    if refresh_token:
        try:
            payload = decode_paseto_token(refresh_token)
            if payload.get("type") == "refresh":
                await redis.delete(REFRESH_KEY.format(jti=payload["jti"]))
        except Exception:
            pass  # Invalid refresh token — ignore during logout


async def refresh_tokens(
    redis: Redis,
    refresh_token: str,
) -> TokenResponse:
    try:
        payload = decode_paseto_token(refresh_token)
    except PasetoError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    old_jti = payload["jti"]
    user_id = payload["sub"]

    stored = await redis.get(REFRESH_KEY.format(jti=old_jti))
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or expired",
        )

    # Token rotation: delete old, issue new pair
    await redis.delete(REFRESH_KEY.format(jti=old_jti))

    new_access, _access_jti, _access_exp = create_paseto_access_token(user_id)
    new_refresh, new_refresh_jti, _refresh_exp = create_paseto_refresh_token(user_id)

    refresh_ttl = settings.paseto_refresh_token_expire_days * 86400
    await redis.set(
        REFRESH_KEY.format(jti=new_refresh_jti),
        user_id,
        ex=refresh_ttl,
    )

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)
