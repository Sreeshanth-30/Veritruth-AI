# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Redis Cache Service
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return _pool


async def cache_get(key: str) -> Any | None:
    """Read a JSON-serialised value from cache."""
    try:
        r = await get_redis()
        raw = await r.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.warning("Cache GET failed for %s: %s", key, e)
        return None


async def cache_set(key: str, value: Any, ttl: int = 3600) -> None:
    """Write a JSON-serialisable value to cache with TTL."""
    try:
        r = await get_redis()
        await r.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception as e:
        logger.warning("Cache SET failed for %s: %s", key, e)


async def cache_delete(key: str) -> None:
    try:
        r = await get_redis()
        await r.delete(key)
    except Exception as e:
        logger.warning("Cache DELETE failed for %s: %s", key, e)


async def get_cached_analysis(content_hash: str) -> dict | None:
    """Return a cached analysis result by content hash (dedup)."""
    return await cache_get(f"analysis:hash:{content_hash}")


async def set_cached_analysis(content_hash: str, result: dict, ttl: int = 7200) -> None:
    await cache_set(f"analysis:hash:{content_hash}", result, ttl=ttl)


async def get_rate_limit_count(user_id: str, window: str = "day") -> int:
    """Return the number of analyses a user has run in the current window."""
    r = await get_redis()
    key = f"rate:{user_id}:{window}"
    val = await r.get(key)
    return int(val) if val else 0


async def increment_rate_limit(user_id: str, window: str = "day", ttl: int = 86400) -> int:
    r = await get_redis()
    key = f"rate:{user_id}:{window}"
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, ttl)
    results = await pipe.execute()
    return results[0]


async def get_cached_quick_check(url: str) -> dict | None:
    """Return a cached quick-check result for a URL."""
    return await cache_get(f"quick_check:{url}")


async def cache_quick_check(url: str, result: dict, ttl: int = 1800) -> None:
    """Cache a quick-check result for a URL (30-minute TTL by default)."""
    await cache_set(f"quick_check:{url}", result, ttl=ttl)


async def close_redis():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
