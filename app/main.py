"""
FastAPI application factory.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.v1 import router as api_v1_router
from app.clients.postgres import connect_db, disconnect_db
from app.clients.rabbitmq import connect_rabbitmq, disconnect_rabbitmq
from app.clients.redis import connect_redis, disconnect_redis
from app.clients.rest import connect_http_client, disconnect_http_client
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.graphql.schema import graphql_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(f"Starting [{settings.app_name}] env={settings.app_env} …")

    await connect_db()
    await connect_redis()
    await connect_rabbitmq()
    await connect_http_client()

    logger.info("All clients connected ✓")
    yield

    logger.info("Shutting down …")
    await disconnect_http_client()
    await disconnect_rabbitmq()
    await disconnect_redis()
    await disconnect_db()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=(
            "FastAPI backend scaffold with "
            "PostgreSQL · Redis · RabbitMQ · REST API · GraphQL clients."
        ),
        version="0.1.0",
        debug=settings.app_debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── CORS ──────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global error handler ───────────────────────────────────
    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled error on {request.method} {request.url}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "Internal server error."},
        )

    # ── Routers ────────────────────────────────────────────────
    app.include_router(api_v1_router)
    app.include_router(graphql_router, prefix="/graphql")

    return app


app = create_app()
