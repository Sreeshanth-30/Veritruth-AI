# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Fact Verification via RAG Pipeline
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def verify_claims(
    claims: list[dict[str, Any]],
    language: str = "en",
) -> list[dict[str, Any]]:
    """Verify extracted claims using Retrieval-Augmented Generation.
    
    Pipeline:
    1. Embed each claim using a sentence transformer
    2. Retrieve relevant evidence from vector DB + knowledge base
    3. Use LLM to synthesize verdict (SUPPORTED / REFUTED / UNVERIFIABLE)
    
    Args:
        claims: List of claim dicts from claim_extractor
        language: Target language for cross-lingual support
    
    Returns:
        [
            {
                "claim_text": "...",
                "verdict": "REFUTED" | "SUPPORTED" | "UNVERIFIABLE",
                "confidence": 0.97,
                "evidence": "explanation...",
                "sources": [{"title": "...", "url": "...", "relevance": 0.92}],
            }
        ]
    """
    results = []

    for claim in claims:
        claim_text = claim["claim_text"]

        # Step 1: Retrieve relevant evidence
        evidence_docs = await _retrieve_evidence(claim_text)

        # Step 2: Generate verdict with LLM
        verification = await _generate_verdict(claim_text, evidence_docs, language)

        results.append({
            "claim_text": claim_text,
            "verdict": verification["verdict"],
            "confidence": verification["confidence"],
            "evidence": verification["evidence"],
            "sources": verification.get("sources", []),
        })

    logger.info("Verified %d claims", len(results))
    return results


async def _retrieve_evidence(claim_text: str) -> list[dict]:
    """Retrieve relevant evidence documents for a claim.
    
    Sources:
    - Internal MongoDB knowledge base
    - Google Fact Check API
    - Cached verified facts
    """
    evidence = []

    # 1. Google Fact Check API
    try:
        import httpx
        from app.core.config import get_settings

        settings = get_settings()
        if settings.GOOGLE_FACT_CHECK_API_KEY:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://factchecktools.googleapis.com/v1alpha1/claims:search",
                    params={
                        "query": claim_text[:200],
                        "key": settings.GOOGLE_FACT_CHECK_API_KEY,
                        "languageCode": "en",
                    },
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for claim_review in data.get("claims", [])[:3]:
                        for review in claim_review.get("claimReview", []):
                            evidence.append({
                                "title": review.get("title", ""),
                                "url": review.get("url", ""),
                                "publisher": review.get("publisher", {}).get("name", ""),
                                "rating": review.get("textualRating", ""),
                                "text": claim_review.get("text", ""),
                                "source": "Google Fact Check",
                                "relevance": 0.9,
                            })
    except Exception as e:
        logger.warning("Fact check API error: %s", e)

    # 2. Internal MongoDB knowledge base
    try:
        from app.core.database import get_mongo_db

        db = get_mongo_db()
        cursor = db.verified_facts.find(
            {"$text": {"$search": claim_text[:200]}},
            {"score": {"$meta": "textScore"}},
        ).sort([("score", {"$meta": "textScore"})]).limit(5)

        async for doc in cursor:
            evidence.append({
                "title": doc.get("title", ""),
                "url": doc.get("url", ""),
                "text": doc.get("text", ""),
                "source": "Internal KB",
                "relevance": doc.get("score", 0.5),
            })
    except Exception as e:
        logger.warning("MongoDB evidence retrieval error: %s", e)

    return evidence


async def _generate_verdict(
    claim: str,
    evidence: list[dict],
    language: str = "en",
) -> dict[str, Any]:
    """Use LLM to synthesize a fact-check verdict from retrieved evidence.
    
    Falls back to rule-based analysis if LLM is unavailable.
    """
    from app.core.config import get_settings

    settings = get_settings()

    # Try OpenAI for verdict synthesis
    if settings.OPENAI_API_KEY:
        try:
            import openai

            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            evidence_text = "\n".join(
                f"- [{e.get('source', 'Unknown')}] {e.get('text', '')[:300]}"
                for e in evidence[:5]
            )

            prompt = f"""You are a fact-checking AI. Analyze the following claim against the provided evidence and determine if it is SUPPORTED, REFUTED, or UNVERIFIABLE.

CLAIM: "{claim}"

EVIDENCE:
{evidence_text if evidence_text else "No evidence found."}

Respond in JSON format:
{{"verdict": "SUPPORTED|REFUTED|UNVERIFIABLE", "confidence": 0.0-1.0, "evidence": "1-2 sentence explanation"}}"""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200,
                response_format={"type": "json_object"},
            )

            import json
            result = json.loads(response.choices[0].message.content)
            result["sources"] = [
                {"title": e.get("title", ""), "url": e.get("url", ""), "relevance": e.get("relevance", 0.5)}
                for e in evidence[:3]
            ]
            return result

        except Exception as e:
            logger.warning("LLM verdict generation failed: %s", e)

    # Fallback: rule-based verdict
    if not evidence:
        return {
            "verdict": "UNVERIFIABLE",
            "confidence": 0.5,
            "evidence": "No matching evidence found in fact-checking databases.",
            "sources": [],
        }

    # Simple heuristic based on evidence ratings
    ratings = [e.get("rating", "").lower() for e in evidence if e.get("rating")]
    if any(r in ("false", "pants on fire", "incorrect", "misleading") for r in ratings):
        return {
            "verdict": "REFUTED",
            "confidence": 0.85,
            "evidence": f"Fact-checkers have rated similar claims as false. Source: {evidence[0].get('publisher', 'Unknown')}",
            "sources": [{"title": e.get("title", ""), "url": e.get("url", "")} for e in evidence[:3]],
        }
    elif any(r in ("true", "correct", "accurate", "mostly true") for r in ratings):
        return {
            "verdict": "SUPPORTED",
            "confidence": 0.8,
            "evidence": f"Evidence supports this claim. Source: {evidence[0].get('publisher', 'Unknown')}",
            "sources": [{"title": e.get("title", ""), "url": e.get("url", "")} for e in evidence[:3]],
        }

    return {
        "verdict": "UNVERIFIABLE",
        "confidence": 0.4,
        "evidence": "Evidence found but verdict unclear. Manual review recommended.",
        "sources": [{"title": e.get("title", ""), "url": e.get("url", "")} for e in evidence[:3]],
    }
