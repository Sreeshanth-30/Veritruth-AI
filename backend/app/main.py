# ──────────────────────────────────────────────────────────────
# VeriTruth AI — FastAPI Application Entry Point
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware

from app.core.config import get_settings
from app.core.database import init_databases, close_databases
from app.services.cache_service import close_redis

logger = logging.getLogger(__name__)
settings = get_settings()

# ────────────────────── Logging ───────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Silence noisy third-party loggers
for _noisy in ("pymongo", "motor", "neo4j", "httpx", "httpcore", "celery.utils"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)


# ────────────────────── Lifespan ──────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle hook."""
    logger.info("VeriTruth AI starting up (env=%s)", settings.APP_ENV)
    await init_databases()
    logger.info("Database connections established")
    yield
    logger.info("VeriTruth AI shutting down")
    await close_databases()
    await close_redis()
    logger.info("All connections closed")


# ────────────────────── App Factory ───────────────────────────

app = FastAPI(
    title="VeriTruth AI — Multi-Layer Fake News Intelligence",
    description=(
        "Enterprise-grade AI system that analyses news content for misinformation, "
        "propaganda, sentiment manipulation, and source credibility. "
        "Designed for students, educators, researchers, and journalists."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

# ────────────────────── Middleware ─────────────────────────────

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted hosts (production)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.cors_origins_list + ["localhost"],
    )


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response: Response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}"
    return response


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ────────────────────── Exception Handlers ────────────────────

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": "Resource not found"})


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error("Internal server error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


# ────────────────────── Routers ───────────────────────────────

from app.routers.auth_router import router as auth_router
from app.routers.analysis_router import router as analysis_router
from app.routers.admin_router import router as admin_router
from app.routers.websocket_router import router as ws_router
from app.routers.extension_router import router as extension_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(ws_router, prefix="/api/v1", tags=["WebSocket"])
app.include_router(extension_router, prefix="/api/v1/extension", tags=["Browser Extension"])


# ────────────────────── Health ────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
    }


@app.get("/", tags=["Health"])
async def root():
    return {
        "app": "VeriTruth AI",
        "version": "1.0.0",
        "docs": "/docs",
    }
