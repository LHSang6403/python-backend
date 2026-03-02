"""
v1 API router – register all sub-routers here.
"""
from fastapi import APIRouter

from app.api.v1.health import router as health_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)

# ── Add your domain routers below ─────────────────────────────
# from app.api.v1.items import router as items_router
# router.include_router(items_router)
