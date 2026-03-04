# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Source Service (Trusted Source Management)
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import TrustedSource
from app.services.cache_service import cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)


async def get_sources(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
) -> list[TrustedSource]:
    """Return paginated trusted sources, optionally filtered by domain search."""
    stmt = select(TrustedSource).order_by(TrustedSource.domain)
    if search:
        stmt = stmt.where(TrustedSource.domain.ilike(f"%{search}%"))
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_source_by_domain(db: AsyncSession, domain: str) -> TrustedSource | None:
    """Lookup a single source by exact domain match (cache-first)."""
    cached = await cache_get(f"source:{domain}")
    if cached:
        return TrustedSource(**cached) if isinstance(cached, dict) else None

    result = await db.execute(
        select(TrustedSource).where(TrustedSource.domain == domain)
    )
    source = result.scalar_one_or_none()
    if source:
        await cache_set(f"source:{domain}", {
            "domain": source.domain,
            "credibility_score": source.credibility_score,
            "historical_accuracy": source.historical_accuracy,
            "editorial_standards": source.editorial_standards,
            "ownership_transparency": source.ownership_transparency,
            "correction_record": source.correction_record,
            "is_approved": source.is_approved,
            "is_blacklisted": source.is_blacklisted,
        }, ttl=3600)
    return source


async def create_source(db: AsyncSession, data: dict[str, Any]) -> TrustedSource:
    """Create a new trusted source entry."""
    source = TrustedSource(**data)
    db.add(source)
    await db.commit()
    await db.refresh(source)
    await cache_delete(f"source:{source.domain}")
    logger.info("Created trusted source: %s", source.domain)
    return source


async def approve_source(db: AsyncSession, source_id: UUID, admin_id: UUID) -> TrustedSource | None:
    result = await db.execute(
        select(TrustedSource).where(TrustedSource.id == source_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        return None
    source.is_approved = True
    source.approved_by = admin_id
    await db.commit()
    await db.refresh(source)
    await cache_delete(f"source:{source.domain}")
    return source


async def blacklist_source(db: AsyncSession, source_id: UUID) -> TrustedSource | None:
    result = await db.execute(
        select(TrustedSource).where(TrustedSource.id == source_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        return None
    source.is_blacklisted = True
    source.is_approved = False
    await db.commit()
    await db.refresh(source)
    await cache_delete(f"source:{source.domain}")
    return source


async def check_domain_credibility(domain: str) -> dict:
    """Return credibility info for a domain without requiring a DB session.
    
    Used by the browser extension endpoint for quick domain lookups.
    Results are Redis-cached for 1 hour.
    """
    cached = await cache_get(f"source:{domain}")
    if cached:
        return cached
    # Without a DB session we return a neutral default;
    # the full lookup happens inside the Celery analysis pipeline.
    return {
        "domain": domain,
        "known": False,
        "credibility_score": None,
        "is_blacklisted": False,
        "bias_label": None,
    }


async def get_domain_stats(db: AsyncSession) -> list[dict]:
    """Aggregate domain credibility statistics for admin dashboard."""
    stmt = (
        select(
            TrustedSource.domain,
            TrustedSource.credibility_score,
            TrustedSource.fake_count,
            TrustedSource.is_blacklisted,
        )
        .order_by(TrustedSource.fake_count.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    return [
        {
            "domain": row.domain,
            "credibility_score": row.credibility_score,
            "fake_count": row.fake_count,
            "is_blacklisted": row.is_blacklisted,
        }
        for row in result.all()
    ]
