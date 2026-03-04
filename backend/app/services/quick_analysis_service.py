# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Quick Analysis Service (Browser Extension)
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import hashlib
import logging
from typing import Any

from app.services.cache_service import cache_get, cache_set

logger = logging.getLogger(__name__)


async def run_quick_analysis(text: str | None = None, url: str | None = None) -> dict[str, Any]:
    """Alias used by the browser extension router."""
    return await quick_analyse(text=text or "", url=url)


async def quick_analyse(text: str, url: str | None = None) -> dict[str, Any]:
    """Lightweight analysis for browser extension — fast response (<2s target).
    
    Runs only classifier + basic claim extraction (no RAG / KG / deepfake).
    """
    content_hash = hashlib.sha256(text.encode()).hexdigest()

    # Check cache first
    cached = await cache_get(f"quick:{content_hash}")
    if cached:
        return cached

    from app.ai_models.classifier import classify_fake_news
    from app.ai_models.claim_extractor import extract_claims

    classification = classify_fake_news(text[:5000])  # limit for speed
    claims = extract_claims(text[:5000])

    fake_p = classification["fake_probability"]
    if fake_p >= 0.8:
        risk = "CRITICAL"
    elif fake_p >= 0.6:
        risk = "HIGH"
    elif fake_p >= 0.35:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    result = {
        "risk_level": risk,
        "fake_probability": fake_p,
        "confidence": classification["confidence"],
        "label": classification["label"],
        "claim_count": len(claims),
        "top_claims": [c["claim_text"] for c in claims[:3]],
        "source_url": url,
    }

    await cache_set(f"quick:{content_hash}", result, ttl=1800)
    return result
