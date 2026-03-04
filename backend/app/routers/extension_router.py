# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Browser Extension API Router
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl

from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(tags=["Browser Extension"])


class QuickCheckRequest(BaseModel):
    url: str
    page_title: str | None = None
    selected_text: str | None = None


class QuickCheckResponse(BaseModel):
    risk_score: float
    risk_level: str
    fake_probability: float
    source_credibility: float
    summary: str
    is_cached: bool = False


@router.post("/quick-check", response_model=QuickCheckResponse)
async def quick_check(
    body: QuickCheckRequest,
    current_user: User = Depends(get_current_user),
):
    """Lightweight endpoint for browser extension quick-check.
    
    Returns a fast risk assessment without full pipeline analysis.
    Designed for sub-second response times.
    """
    # Check cache first (Redis)
    from app.services.cache_service import get_cached_quick_check, cache_quick_check
    
    cached = await get_cached_quick_check(body.url)
    if cached:
        cached["is_cached"] = True
        return QuickCheckResponse(**cached)

    # Run lightweight analysis
    from app.services.quick_analysis_service import run_quick_analysis

    result = await run_quick_analysis(
        url=body.url,
        text=body.selected_text,
    )

    await cache_quick_check(body.url, result)

    return QuickCheckResponse(**result)


@router.get("/domains/check/{domain}")
async def check_domain(domain: str):
    """Check if a domain is in the trusted/blacklisted database."""
    from app.services.source_service import check_domain_credibility

    result = await check_domain_credibility(domain)
    return result
