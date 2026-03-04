"""Auth endpoints: login, logout, refresh."""
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.clients.postgres import get_db
from app.clients.redis import get_redis
from app.core.security import decode_token
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])
bearer_scheme = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TokenResponse:
    return await auth_service.login(db, redis, body.email, body.password)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest | None = None,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    redis: Redis = Depends(get_redis),
    _current_user: User = Depends(get_current_user),
) -> None:
    payload = decode_token(credentials.credentials)
    await auth_service.logout(
        redis,
        payload,
        refresh_token=body.refresh_token if body else None,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    redis: Redis = Depends(get_redis),
) -> TokenResponse:
    return await auth_service.refresh_tokens(redis, body.refresh_token)
