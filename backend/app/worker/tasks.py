# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Celery Task Definitions
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import traceback
import uuid as _uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from celery import shared_task
from sqlalchemy import select, update

from app.worker.celery_app import celery_app  # noqa: F401 — ensure app is loaded

logger = logging.getLogger(__name__)

# ────────────────────── Helpers ──────────────────────────────

def _run_async(coro):
    """Bridge async coroutines into Celery (sync) worker threads."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _publish_progress(analysis_id: str, stage: str, pct: int, detail: str = ""):
    """Push a progress payload to Redis pub/sub so the WebSocket router can relay it.
    Silently ignored if Redis is unavailable."""
    try:
        import redis
        from app.core.config import get_settings
        settings = get_settings()
        r = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1)
        payload = json.dumps({
            "analysis_id": analysis_id,
            "stage": stage,
            "progress": pct,
            "detail": detail,
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        r.publish(f"analysis:{analysis_id}:progress", payload)
    except Exception as _e:
        logger.debug("Redis progress publish skipped (%s)", _e)


async def _set_status(analysis_id: str, status: str, **extra):
    """Update the analysis row status (and optional extra columns)."""
    from app.core.database import async_session_factory
    from app.models.analysis import Analysis

    async with async_session_factory() as session:
        stmt = (
            update(Analysis)
            .where(Analysis.id == _uuid.UUID(analysis_id))
            .values(status=status, updated_at=datetime.now(timezone.utc), **extra)
        )
        await session.execute(stmt)
        await session.commit()


async def _fetch_analysis(analysis_id: str):
    from app.core.database import async_session_factory
    from app.models.analysis import Analysis

    async with async_session_factory() as session:
        result = await session.execute(
            select(Analysis).where(Analysis.id == _uuid.UUID(analysis_id))
        )
        return result.scalar_one_or_none()


# ────────────────────── Pipeline core ─────────────────────────

async def _run_pipeline(analysis_id: str, text: str, source_url: str | None = None):
    """Execute the full multi-layer AI pipeline on a text input."""

    from app.ai_models.classifier import classify_fake_news, get_shap_explanations
    from app.ai_models.claim_extractor import extract_claims, extract_entities
    from app.ai_models.propaganda_detector import detect_propaganda
    from app.ai_models.fact_verifier import verify_claims
    from app.ai_models.sentiment_analyzer import analyze_sentiment
    from app.ai_models.credibility_scorer import compute_credibility_score
    from app.ai_models.knowledge_graph import build_knowledge_graph
    from app.core.database import async_session_factory, get_mongo_db
    from app.models.analysis import Analysis

    try:
        await _set_status(analysis_id, "PROCESSING")

        results: dict[str, Any] = {}

        # ─── Stage 1: Classification (RoBERTa / DeBERTa) ──────────
        _publish_progress(analysis_id, "classification", 10, "Running AI classifier…")
        try:
            classification = classify_fake_news(text)
            results["fake_probability"] = classification["fake_probability"]
            results["confidence_score"] = classification["confidence"]
            results["classification_label"] = classification["label"]
        except Exception as e:
            logger.error("Classification failed: %s", e)
            results["fake_probability"] = 0.5
            results["confidence_score"] = 0.0

        # ─── Stage 2: Claim Extraction (spaCy) ─────────────────────
        _publish_progress(analysis_id, "claims", 20, "Extracting claims…")
        try:
            claims = extract_claims(text)
            entities = extract_entities(text)
            results["detected_claims"] = claims
            results["claim_count"] = len(claims)
        except Exception as e:
            logger.error("Claim extraction failed: %s", e)
            claims, entities = [], []
            results["detected_claims"] = []

        # ─── Stage 3: Fact Verification (RAG) ──────────────────────
        _publish_progress(analysis_id, "fact_check", 35, "Verifying claims against sources…")
        try:
            fact_results = await verify_claims(claims)
            results["fact_verification_results"] = fact_results
            supported = sum(1 for f in fact_results if f.get("verdict") == "SUPPORTED")
            refuted = sum(1 for f in fact_results if f.get("verdict") == "REFUTED")
            results["verified_true_count"] = supported
            results["verified_false_count"] = refuted
        except Exception as e:
            logger.error("Fact verification failed: %s", e)
            fact_results = []
            results["fact_verification_results"] = []

        # ─── Stage 4: Propaganda Detection ─────────────────────────
        _publish_progress(analysis_id, "propaganda", 50, "Detecting propaganda techniques…")
        try:
            propaganda = detect_propaganda(text)
            results["propaganda_score"] = propaganda["overall_score"]
            results["propaganda_techniques"] = propaganda["techniques"]
        except Exception as e:
            logger.error("Propaganda detection failed: %s", e)
            results["propaganda_score"] = 0.0
            results["propaganda_techniques"] = []

        # ─── Stage 5: Sentiment & Manipulation ─────────────────────
        _publish_progress(analysis_id, "sentiment", 62, "Analysing sentiment & manipulation…")
        try:
            sentiment = analyze_sentiment(text)
            results["sentiment_breakdown"] = sentiment
            results["bias_score"] = sentiment.get("manipulation_score", 0.0)
        except Exception as e:
            logger.error("Sentiment analysis failed: %s", e)
            results["sentiment_breakdown"] = {}

        # ─── Stage 6: SHAP Explainability ──────────────────────────
        _publish_progress(analysis_id, "explainability", 72, "Generating explanations…")
        try:
            shap_data = get_shap_explanations(text)
            results["explainability_data"] = shap_data
            results["suspicious_passages"] = [
                {
                    "text": tok["token"],
                    "score": tok["shap_value"],
                    "reason": "High fake-signal contribution",
                }
                for tok in shap_data.get("tokens", [])
                if tok.get("shap_value", 0) > 0.1
            ][:20]
        except Exception as e:
            logger.error("SHAP explainability failed: %s", e)
            results["explainability_data"] = {}
            results["suspicious_passages"] = []

        # ─── Stage 7: Credibility Scoring ──────────────────────────
        _publish_progress(analysis_id, "credibility", 82, "Computing credibility score…")
        try:
            credibility = await compute_credibility_score(
                text=text,
                url=source_url,
                fact_results=fact_results,
                claims=claims,
            )
            results["credibility_score"] = credibility["overall_score"]
            results["credibility_breakdown"] = credibility["breakdown"]
        except Exception as e:
            logger.error("Credibility scoring failed: %s", e)
            results["credibility_score"] = 0.5

        # ─── Stage 8: Knowledge Graph ──────────────────────────────
        _publish_progress(analysis_id, "knowledge_graph", 90, "Building knowledge graph…")
        try:
            kg = await build_knowledge_graph(
                entities=entities,
                claims=claims,
                fact_results=fact_results,
                source_url=source_url,
            )
            results["knowledge_graph_data"] = kg
        except Exception as e:
            logger.error("Knowledge graph failed: %s", e)
            results["knowledge_graph_data"] = {"nodes": [], "edges": [], "conflicts": 0, "verified": 0}

        # ─── Compute overall risk level ────────────────────────────
        fake_p = results.get("fake_probability", 0.5)
        if fake_p >= 0.8:
            risk_level = "CRITICAL"
        elif fake_p >= 0.6:
            risk_level = "HIGH"
        elif fake_p >= 0.35:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        results["risk_level"] = risk_level

        # ─── Compute content hash ──────────────────────────────────
        content_hash = hashlib.sha256(text.encode()).hexdigest()

        # ─── Store full results in MongoDB ─────────────────────────
        _publish_progress(analysis_id, "storing", 95, "Saving results…")
        mongo_id = None
        try:
            db = get_mongo_db()
            doc = {
                "analysis_id": analysis_id,
                "results": results,
                "text_snippet": text[:500],
                "created_at": datetime.now(timezone.utc),
            }
            insert = await db.analysis_results.insert_one(doc)
            mongo_id = str(insert.inserted_id)
        except Exception as e:
            logger.error("MongoDB storage failed: %s", e)

        # ─── Update PostgreSQL row ─────────────────────────────────
        async with async_session_factory() as session:
            update_vals = {
                "status": "COMPLETED",
                "completed_at": datetime.now(timezone.utc),
                "content_hash": content_hash,
                "risk_level": risk_level,
                "fake_probability": results.get("fake_probability"),
                "confidence_score": results.get("confidence_score"),
                "classification_label": results.get("classification_label"),
                "propaganda_score": results.get("propaganda_score"),
                "credibility_score": results.get("credibility_score"),
                "bias_score": results.get("bias_score"),
                "claim_count": results.get("claim_count", 0),
                "verified_true_count": results.get("verified_true_count", 0),
                "verified_false_count": results.get("verified_false_count", 0),
                "detected_claims": results.get("detected_claims"),
                "fact_verification_results": results.get("fact_verification_results"),
                "propaganda_techniques": results.get("propaganda_techniques"),
                "sentiment_breakdown": results.get("sentiment_breakdown"),
                "suspicious_passages": results.get("suspicious_passages"),
                "explainability_data": results.get("explainability_data"),
                "evidence_references": [
                    ref
                    for fr in fact_results
                    for ref in fr.get("sources", [])
                ],
                "knowledge_graph_data": results.get("knowledge_graph_data"),
                "credibility_breakdown": results.get("credibility_breakdown"),
                "sentiment_score": results.get("sentiment_breakdown", {}).get("manipulation_score"),
                "emotional_manipulation_score": results.get("sentiment_breakdown", {}).get("manipulation_score"),
            }
            if mongo_id:
                update_vals["mongo_result_id"] = mongo_id

            stmt = (
                update(Analysis)
                .where(Analysis.id == _uuid.UUID(analysis_id))
                .values(**update_vals)
            )
            await session.execute(stmt)
            await session.commit()

        _publish_progress(analysis_id, "done", 100, "Analysis complete")
        logger.info("Analysis %s completed successfully", analysis_id)
        return results

    except Exception as exc:
        logger.error("Pipeline FATAL error for %s: %s\n%s", analysis_id, exc, traceback.format_exc())
        try:
            await _set_status(analysis_id, "FAILED", error_message=str(exc)[:2000])
        except Exception:
            logger.error("Could not set FAILED status for %s", analysis_id)
        return {}


# ────────────────────── URL content fetcher ───────────────────

async def _fetch_url_content(url: str) -> tuple[str, dict]:
    """Scrape article text and metadata from a URL."""
    import httpx
    from bs4 import BeautifulSoup

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "VeriTruthBot/1.0"})
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
        tag.decompose()

    # Extract metadata
    meta: dict[str, Any] = {}
    title_tag = soup.find("title")
    meta["title"] = title_tag.get_text(strip=True) if title_tag else ""

    og_desc = soup.find("meta", attrs={"property": "og:description"})
    meta_desc = soup.find("meta", attrs={"name": "description"})
    meta["description"] = (
        og_desc["content"] if og_desc and og_desc.get("content")
        else meta_desc["content"] if meta_desc and meta_desc.get("content")
        else ""
    )

    author_tag = soup.find("meta", attrs={"name": "author"})
    meta["author"] = author_tag["content"] if author_tag and author_tag.get("content") else ""

    pub_date = soup.find("meta", attrs={"property": "article:published_time"})
    meta["published_date"] = pub_date["content"] if pub_date and pub_date.get("content") else None

    # Extract article text — prefer <article> or main content
    article = soup.find("article") or soup.find("main") or soup.find("body")
    paragraphs = article.find_all("p") if article else []
    text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

    if len(text) < 100:
        text = soup.get_text(separator="\n", strip=True)

    return text[:50000], meta


# ────────────────────── File content extractor ────────────────

async def _extract_file_content(file_path: str) -> tuple[str, str]:
    """Extract text from uploaded file. Returns (text, mime_type)."""
    import mimetypes
    path = Path(file_path)
    mime, _ = mimetypes.guess_type(str(path))

    if mime == "application/pdf":
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(path))
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            return text[:50000], mime
        except ImportError:
            logger.warning("PyMuPDF not installed; falling back to raw text read")

    # Fallback: read as plain text
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text[:50000], mime or "text/plain"


# ────────────────────── Celery Tasks ─────────────────────────

async def _run_url_content_and_pipeline(analysis_id: str, url: str) -> None:
    """Fetch URL content then run the full pipeline (used as BackgroundTask fallback)."""
    text, meta = await _fetch_url_content(url)
    await _set_status(
        analysis_id,
        "PROCESSING",
    )
    await _run_pipeline(analysis_id, text, source_url=url)


@shared_task(bind=True, name="app.worker.tasks.run_analysis_pipeline")
def run_analysis_pipeline(self, analysis_id: str, text: str, source_url: str | None = None, **kwargs):
    """Main analysis task: analyse a raw text input."""
    try:
        return _run_async(_run_pipeline(analysis_id, text, source_url))
    except Exception as exc:
        logger.error("Pipeline failed for %s: %s\n%s", analysis_id, exc, traceback.format_exc())
        _run_async(_set_status(analysis_id, "FAILED", error_message=str(exc)[:2000]))
        raise self.retry(exc=exc, countdown=60, max_retries=2)


@shared_task(bind=True, name="app.worker.tasks.run_url_analysis_pipeline")
def run_url_analysis_pipeline(self, analysis_id: str, url: str, **kwargs):
    """Fetch URL content then run full pipeline."""
    try:
        text, meta = _run_async(_fetch_url_content(url))
        _run_async(
            _set_status(
                analysis_id,
                "PROCESSING",
                article_title=meta.get("title", "")[:500],
                author=meta.get("author", "")[:300],
            )
        )
        return _run_async(_run_pipeline(analysis_id, text, source_url=url))
    except Exception as exc:
        logger.error("URL pipeline failed for %s: %s\n%s", analysis_id, exc, traceback.format_exc())
        _run_async(_set_status(analysis_id, "FAILED", error_message=str(exc)[:2000]))
        raise self.retry(exc=exc, countdown=60, max_retries=2)


@shared_task(bind=True, name="app.worker.tasks.run_file_analysis_pipeline")
def run_file_analysis_pipeline(self, analysis_id: str, file_path: str, **kwargs):
    """Extract file content then run full pipeline."""
    try:
        text, mime = _run_async(_extract_file_content(file_path))
        return _run_async(_run_pipeline(analysis_id, text))
    except Exception as exc:
        logger.error("File pipeline failed for %s: %s\n%s", analysis_id, exc, traceback.format_exc())
        _run_async(_set_status(analysis_id, "FAILED", error_message=str(exc)[:2000]))
        raise self.retry(exc=exc, countdown=60, max_retries=2)


# ────────────────────── Periodic Tasks ────────────────────────

@shared_task(name="app.worker.tasks.cleanup_stale_analyses")
def cleanup_stale_analyses():
    """Mark analyses stuck in processing for > 15 min as failed."""
    from datetime import timedelta
    from app.core.database import async_session_factory
    from app.models.analysis import Analysis

    async def _cleanup():
        async with async_session_factory() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
            stmt = (
                update(Analysis)
                .where(Analysis.status == "PROCESSING", Analysis.updated_at < cutoff)
                .values(status="FAILED", error_message="Timed out after 15 minutes")
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount

    count = _run_async(_cleanup())
    if count:
        logger.info("Cleaned up %d stale analyses", count)
    return count


@shared_task(name="app.worker.tasks.refresh_source_cache")
def refresh_source_cache():
    """Refresh trusted source cache in Redis."""
    import redis as redis_lib
    from app.core.config import get_settings
    from app.core.database import async_session_factory
    from app.models.source import TrustedSource

    async def _refresh():
        async with async_session_factory() as session:
            result = await session.execute(
                select(TrustedSource).where(TrustedSource.is_approved == True)  # noqa: E712
            )
            sources = result.scalars().all()

        settings = get_settings()
        r = redis_lib.Redis.from_url(settings.REDIS_URL)
        pipe = r.pipeline()
        pipe.delete("trusted_sources")
        for src in sources:
            pipe.hset("trusted_sources", src.domain, json.dumps({
                "credibility": src.credibility_score,
                "historical_accuracy": src.historical_accuracy,
            }))
        pipe.execute()
        return len(sources)

    count = _run_async(_refresh())
    logger.info("Refreshed %d trusted sources in cache", count)
    return count
