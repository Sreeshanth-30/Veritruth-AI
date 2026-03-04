# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Analysis Router
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional, cast

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.core.config import get_settings
from app.core.database import get_db, get_mongo_db
from app.core.security import compute_article_hash
from app.models.analysis import Analysis, AnalysisStatus, InputType
from app.models.user import User
from app.schemas.analysis import (
    AnalysisCreateResponse,
    AnalysisListResponse,
    AnalysisResultResponse,
    AnalysisStatusResponse,
    AnalysisTextRequest,
    AnalysisURLRequest,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(tags=["Analysis"])

# ── Helper: check if Celery workers are online ────────────────
_celery_available: bool | None = None
_celery_checked_at: float = 0

def _is_celery_available() -> bool:
    """Quick cached check for active Celery workers (cache 30s)."""
    import time as _t
    global _celery_available, _celery_checked_at
    now = _t.time()
    if _celery_available is not None and (now - _celery_checked_at) < 30:
        return _celery_available
    try:
        from app.worker.celery_app import celery_app
        resp = celery_app.control.ping(timeout=1.0)
        _celery_available = bool(resp)
    except Exception:
        _celery_available = False
    _celery_checked_at = now
    return _celery_available


# ── Submit Text for Analysis ──────────────────────────────────
@router.post(
    "/text",
    response_model=AnalysisCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_text(
    body: AnalysisTextRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Submit article text for multi-layer AI analysis.
    
    Starts an async Celery task that runs all AI pipelines in parallel.
    Poll the status endpoint or use WebSocket for real-time updates.
    """
    # Rate limiting check
    if current_user:
        if current_user.analysis_count_today >= settings.RATE_LIMIT_ANALYSIS_PER_HOUR:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Analysis rate limit exceeded. Try again later.",
            )

    # Create analysis record
    analysis = Analysis(
        user_id=current_user.id if current_user else uuid.UUID("00000000-0000-0000-0000-000000000000"),
        input_type=InputType.TEXT,
        original_text=body.text,
        content_hash=compute_article_hash(body.text),
        status=AnalysisStatus.PENDING,
    )
    db.add(analysis)
    await db.flush()
    await db.refresh(analysis)

    # Dispatch — prefer Celery if workers are up, else run inline
    from app.worker.tasks import run_analysis_pipeline, _run_pipeline

    task_id: str | None = None
    use_celery = _is_celery_available()

    if use_celery:
        try:
            task = cast(Any, run_analysis_pipeline).delay(
                analysis_id=str(analysis.id),
                text=body.text,
            )
            task_id = task.id
            analysis.celery_task_id = task_id
            analysis.status = AnalysisStatus.PROCESSING
            logger.info("Analysis dispatched to Celery: %s", task_id)
        except Exception as exc:
            logger.warning("Celery dispatch failed — falling back to inline: %s", exc)
            use_celery = False

    if not use_celery:
        analysis.status = AnalysisStatus.PROCESSING
        background_tasks.add_task(_run_pipeline, str(analysis.id), body.text)
        logger.info("Analysis running inline (no Celery worker)")

    if current_user:
        current_user.analysis_count_today += 1

    await db.commit()
    await db.refresh(analysis)
    logger.info("Analysis queued: %s (task: %s)", analysis.id, task_id)

    return AnalysisCreateResponse(
        id=analysis.id,
        status=analysis.status,
        celery_task_id=task_id,
    )


# ── Submit URL for Analysis ───────────────────────────────────
@router.post(
    "/url",
    response_model=AnalysisCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_url(
    body: AnalysisURLRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Submit a news article URL for extraction and multi-layer analysis."""
    analysis = Analysis(
        user_id=current_user.id if current_user else uuid.UUID("00000000-0000-0000-0000-000000000000"),
        input_type=InputType.URL,
        source_url=str(body.url),
        status=AnalysisStatus.PENDING,
    )
    db.add(analysis)
    await db.flush()
    await db.refresh(analysis)

    from app.worker.tasks import run_url_analysis_pipeline, _run_url_content_and_pipeline

    task_id: str | None = None
    use_celery = _is_celery_available()

    if use_celery:
        try:
            task = cast(Any, run_url_analysis_pipeline).delay(
                analysis_id=str(analysis.id),
                url=str(body.url),
            )
            task_id = task.id
            analysis.celery_task_id = task_id
            analysis.status = AnalysisStatus.PROCESSING
        except Exception as exc:
            logger.warning("Celery dispatch failed for URL — falling back to inline: %s", exc)
            use_celery = False

    if not use_celery:
        analysis.status = AnalysisStatus.PROCESSING
        background_tasks.add_task(_run_url_content_and_pipeline, str(analysis.id), str(body.url))

    await db.commit()
    await db.refresh(analysis)

    return AnalysisCreateResponse(
        id=analysis.id,
        status=analysis.status,
        celery_task_id=task_id,
    )


# ── Upload File for Analysis ─────────────────────────────────
@router.post(
    "/upload",
    response_model=AnalysisCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a PDF, image, or video file for analysis."""
    # Validate file type
    allowed_types = {
        "application/pdf": InputType.PDF,
        "image/jpeg": InputType.IMAGE,
        "image/png": InputType.IMAGE,
        "image/webp": InputType.IMAGE,
        "video/mp4": InputType.VIDEO,
    }

    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    # Check file size (50MB max)
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum 50 MB.")

    # Save file
    import os

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if file.filename else "bin"
    file_path = os.path.join(upload_dir, f"{file_id}.{ext}")

    with open(file_path, "wb") as f:
        f.write(contents)

    input_type = allowed_types[file.content_type]
    analysis = Analysis(
        user_id=current_user.id,
        input_type=input_type,
        file_path=file_path,
        status=AnalysisStatus.PENDING,
    )
    db.add(analysis)
    await db.flush()
    await db.refresh(analysis)

    from app.worker.tasks import run_file_analysis_pipeline, _extract_file_content, _run_pipeline

    task_id: str | None = None
    use_celery = _is_celery_available()

    if use_celery:
        try:
            task = cast(Any, run_file_analysis_pipeline).delay(
                analysis_id=str(analysis.id),
                file_path=file_path,
                input_type=input_type.value,
            )
            task_id = task.id
            analysis.celery_task_id = task_id
            analysis.status = AnalysisStatus.PROCESSING
        except Exception as exc:
            logger.warning("Celery dispatch failed for file — falling back to inline: %s", exc)
            use_celery = False

    if not use_celery:
        analysis.status = AnalysisStatus.PROCESSING

        async def _inline_file_pipeline(aid: str, fpath: str) -> None:
            text, _ = await _extract_file_content(fpath)
            await _run_pipeline(aid, text)

        background_tasks.add_task(_inline_file_pipeline, str(analysis.id), file_path)

    await db.commit()
    await db.refresh(analysis)

    return AnalysisCreateResponse(
        id=analysis.id,
        status=analysis.status,
        celery_task_id=task_id,
    )


# ── Get Analysis Status ──────────────────────────────────────
@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Poll the processing status of an analysis."""
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(404, "Analysis not found")

    return AnalysisStatusResponse(
        id=analysis.id,
        status=analysis.status,
    )


# ── Get Analysis Results ─────────────────────────────────────
@router.get("/{analysis_id}", response_model=AnalysisResultResponse)
async def get_analysis_results(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the full results of a completed analysis."""
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(404, "Analysis not found")

    return AnalysisResultResponse.model_validate(analysis)


# ── List User's Analyses ──────────────────────────────────────
@router.get("/", response_model=AnalysisListResponse)
async def list_analyses(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[AnalysisStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the current user's analyses with pagination."""
    query = select(Analysis).where(Analysis.user_id == current_user.id)
    if status_filter:
        query = query.where(Analysis.status == status_filter)
    query = query.order_by(desc(Analysis.created_at))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    analyses = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return AnalysisListResponse(
        items=[AnalysisResultResponse.model_validate(a) for a in analyses],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
