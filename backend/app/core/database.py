# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Database Connections (Async)
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase  # type: ignore[import-untyped]
from neo4j import AsyncGraphDatabase, AsyncDriver  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
# NOTE: models must be imported so metadata is populated before create_all
from app.models import base as _base_module  # noqa: F401

logger = logging.getLogger(__name__)
settings = get_settings()

# ── PostgreSQL / SQLite (SQLAlchemy async) ───────────────────
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
# Alias used throughout the codebase
async_session_factory = AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency – yields an async SQLAlchemy session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── MongoDB (Motor async) ────────────────────────────────────
_mongo_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
        )
    return _mongo_client


def get_mongo_db() -> AsyncIOMotorDatabase:
    return get_mongo_client()[settings.MONGODB_DB]


async def close_mongo() -> None:
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None


# ── Neo4j (async driver) ─────────────────────────────────────
_neo4j_driver: AsyncDriver | None = None


def get_neo4j_driver() -> AsyncDriver:
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_pool_size=50,
            connection_timeout=3.0,
        )
    return _neo4j_driver


async def close_neo4j() -> None:
    global _neo4j_driver
    if _neo4j_driver:
        await _neo4j_driver.close()
        _neo4j_driver = None


# ── Lifecycle ─────────────────────────────────────────────────
async def init_databases() -> None:
    """Validate all database connections at startup.
    
    Logs a warning for each unavailable database instead of crashing,
    so the API can start even in partial-infrastructure dev environments.
    """
    logger.info("Initializing database connections …")

    # SQLite / PostgreSQL
    try:
        if _is_sqlite:
            # Auto-create all tables for SQLite (development mode)
            from app.models.base import Base  # noqa: F401
            import app.models.user  # noqa: F401  ensure models are registered
            import app.models.analysis  # noqa: F401
            import app.models.source  # noqa: F401
            from sqlalchemy import text as _text
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            # ── Incremental migrations: add columns added after initial creation ──
            _new_columns = [
                "ALTER TABLE analyses ADD COLUMN knowledge_graph_data JSON",
                "ALTER TABLE analyses ADD COLUMN credibility_breakdown JSON",
                "ALTER TABLE analyses ADD COLUMN sentiment_score FLOAT",
                "ALTER TABLE analyses ADD COLUMN emotional_manipulation_score FLOAT",
            ]
            async with engine.begin() as conn:
                for _stmt in _new_columns:
                    try:
                        await conn.execute(_text(_stmt))
                    except Exception:
                        pass  # column already exists
            logger.info("✓ SQLite database initialised at veritruth.db")
        else:
            async with engine.begin() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            logger.info("✓ PostgreSQL connected")
    except Exception as exc:
        logger.warning("⚠ Database unavailable: %s — API will start with degraded DB functionality", exc)

    # MongoDB
    try:
        import asyncio as _asyncio
        client = get_mongo_client()
        await _asyncio.wait_for(client.admin.command("ping"), timeout=5.0)
        logger.info("✓ MongoDB connected")
    except Exception as exc:
        logger.warning("⚠ MongoDB unavailable: %s", exc)

    # Neo4j
    try:
        import asyncio as _asyncio
        driver = get_neo4j_driver()
        async def _neo4j_ping():
            async with driver.session() as neo_sess:
                await neo_sess.run("RETURN 1")
        await _asyncio.wait_for(_neo4j_ping(), timeout=5.0)
        logger.info("✓ Neo4j connected")
    except Exception as exc:
        logger.warning("⚠ Neo4j unavailable: %s", exc)


async def close_databases() -> None:
    """Graceful shutdown of all connections."""
    await engine.dispose()
    await close_mongo()
    await close_neo4j()
    logger.info("All database connections closed")
