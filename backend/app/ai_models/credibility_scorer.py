# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Credibility Scoring Engine
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
from typing import Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


async def score_credibility(
    text: str,
    source_url: Optional[str] = None,
    claims_results: Optional[list[dict]] = None,
) -> dict[str, Any]:
    """Compute a comprehensive credibility score for an article.
    
    Factors:
    - Source domain reputation
    - Writing quality indicators
    - Citation density
    - Claim verification rate
    - Author identification
    - Bias indicators
    
    Returns:
        {
            "overall_score": float (0-100),
            "breakdown": {
                "source_reputation": float,
                "writing_quality": float,
                "citation_density": float,
                "claim_support_ratio": float,
                "author_transparency": float,
            },
            "domain_info": {...},
            "risk_factors": [str],
        }
    """
    breakdown = {}
    risk_factors = []

    # 1. Source domain reputation
    domain_info = {}
    if source_url:
        domain_info = await _check_domain(source_url)
        breakdown["source_reputation"] = domain_info.get("score", 50)
        if domain_info.get("is_blacklisted"):
            risk_factors.append("Domain is on known misinformation blacklist")
    else:
        breakdown["source_reputation"] = 30  # Unknown source
        risk_factors.append("No source URL provided")

    # 2. Writing quality
    breakdown["writing_quality"] = _assess_writing_quality(text)
    if breakdown["writing_quality"] < 40:
        risk_factors.append("Low writing quality indicators")

    # 3. Citation density
    breakdown["citation_density"] = _assess_citations(text)
    if breakdown["citation_density"] < 20:
        risk_factors.append("Very few or no citations/references")

    # 4. Claim support ratio
    if claims_results:
        supported = sum(1 for c in claims_results if c.get("verdict") == "SUPPORTED")
        refuted = sum(1 for c in claims_results if c.get("verdict") == "REFUTED")
        total = len(claims_results)
        if total > 0:
            ratio = supported / total * 100
            breakdown["claim_support_ratio"] = ratio
            if refuted > 0:
                risk_factors.append(f"{refuted} claim(s) refuted by fact-checkers")
        else:
            breakdown["claim_support_ratio"] = 50
    else:
        breakdown["claim_support_ratio"] = 50

    # 5. Author transparency
    breakdown["author_transparency"] = _assess_authorship(text)
    if breakdown["author_transparency"] < 30:
        risk_factors.append("No identifiable author or attribution")

    # Weighted aggregate
    weights = {
        "source_reputation": 0.30,
        "writing_quality": 0.15,
        "citation_density": 0.20,
        "claim_support_ratio": 0.25,
        "author_transparency": 0.10,
    }

    overall = sum(breakdown[k] * weights[k] for k in weights)

    return {
        "overall_score": round(overall, 1),
        "breakdown": {k: round(v, 1) for k, v in breakdown.items()},
        "domain_info": domain_info,
        "risk_factors": risk_factors,
    }


async def _check_domain(url: str) -> dict[str, Any]:
    """Look up domain in trusted sources database."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")

        from sqlalchemy import select
        from app.core.database import AsyncSessionLocal
        from app.models.source import TrustedSource

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TrustedSource).where(TrustedSource.domain == domain)
            )
            source = result.scalar_one_or_none()

            if source:
                return {
                    "domain": domain,
                    "name": source.name,
                    "score": source.credibility_score * 100,
                    "is_approved": source.is_approved,
                    "is_blacklisted": source.is_blacklisted,
                    "historical_accuracy": source.historical_accuracy * 100,
                    "editorial_standards": source.editorial_standards * 100,
                }

        # Domain not in DB — assign neutral score
        return {
            "domain": domain,
            "score": 50,
            "is_approved": False,
            "is_blacklisted": False,
            "note": "Domain not in trusted sources database",
        }

    except Exception as e:
        logger.warning("Domain check failed: %s", e)
        return {"score": 50, "error": str(e)}


def _assess_writing_quality(text: str) -> float:
    """Heuristic writing quality assessment."""
    score = 50.0  # Start neutral

    word_count = len(text.split())
    sentence_count = max(text.count(".") + text.count("!") + text.count("?"), 1)
    avg_sentence_length = word_count / sentence_count

    # Reasonable article length
    if word_count > 200:
        score += 10
    if word_count > 500:
        score += 10

    # Sentence variety (not all very short or very long)
    if 12 < avg_sentence_length < 25:
        score += 10

    # ALL CAPS abuse
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    if caps_ratio > 0.15:
        score -= 20

    # Excessive punctuation
    if text.count("!!!") > 0 or text.count("???") > 0:
        score -= 15
    if text.count("!") > 5:
        score -= 10

    # Proper paragraphs
    if text.count("\n\n") > 2:
        score += 5

    return max(0, min(score, 100))


def _assess_citations(text: str) -> float:
    """Estimate citation density in the article."""
    score = 0.0
    text_lower = text.lower()

    # URL presence
    import re
    urls = re.findall(r"https?://\S+", text)
    score += min(len(urls) * 15, 40)

    # Attribution phrases
    attributions = [
        "according to", "study shows", "research indicates",
        "published in", "reported by", "data from",
        "source:", "reference:", "cited in",
    ]
    attr_count = sum(1 for phrase in attributions if phrase in text_lower)
    score += min(attr_count * 12, 45)

    # Quoted sources
    quote_count = text.count('"') // 2
    score += min(quote_count * 5, 15)

    return min(score, 100)


def _assess_authorship(text: str) -> float:
    """Check for author identification and transparency."""
    score = 20.0  # Base
    text_lower = text.lower()

    if any(p in text_lower for p in ["by ", "author:", "written by", "reporter:"]):
        score += 30

    if any(p in text_lower for p in ["editor:", "editorial", "staff writer"]):
        score += 20

    if any(p in text_lower for p in ["contact:", "email:", "@"]):
        score += 15

    if "anonymous" in text_lower or "unnamed" in text_lower:
        score -= 20

    return max(0, min(score, 100))

# ── Alias for tasks.py ────────────────────────────────────────
async def compute_credibility_score(
    text: str,
    url: str | None = None,
    fact_results: list | None = None,
    claims: list | None = None,
) -> dict:
    """Alias for score_credibility — called by the Celery/BackgroundTask pipeline."""
    return await score_credibility(
        text=text,
        source_url=url,
        claims_results=fact_results,
    )