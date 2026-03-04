"""
v1 API router – register all sub-routers here.
"""
from fastapi import APIRouter

from app.api.v1.health import router as health_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)

# ── Domain routers ────────────────────────────────────────────
from app.api.v1.users import router as users_router

router.include_router(users_router)

from app.api.v1.auth import router as auth_router

router.include_router(auth_router)

from app.api.v1.products import router as products_router

router.include_router(products_router)

from app.api.v1.orders import router as orders_router

router.include_router(orders_router)

from app.api.v1.paseto_auth import router as paseto_auth_router

router.include_router(paseto_auth_router)
