# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Analysis Model (PostgreSQL)
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class AnalysisStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class InputType(str, enum.Enum):
    TEXT = "text"
    URL = "url"
    PDF = "pdf"
    IMAGE = "image"
    VIDEO = "video"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Analysis(Base):
    __tablename__ = "analyses"

    # ── Foreign Keys ──────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # ── Input ─────────────────────────────────────────────────
    input_type: Mapped[InputType] = mapped_column(
        Enum(InputType), nullable=False
    )
    original_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    article_title: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # ── Processing ────────────────────────────────────────────
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus),
        default=AnalysisStatus.PENDING,
        index=True,
        nullable=False,
    )
    celery_task_id: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True
    )
    processing_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # ── Scores ────────────────────────────────────────────────
    overall_risk_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    risk_level: Mapped[Optional[RiskLevel]] = mapped_column(
        Enum(RiskLevel), nullable=True
    )
    fake_probability: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    propaganda_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    credibility_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    bias_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    sentiment_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    emotional_manipulation_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    deepfake_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    classification_label: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    claim_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0
    )
    verified_true_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0
    )
    verified_false_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0
    )

    # ── JSON Payloads ─────────────────────────────────────────
    detected_claims: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    fact_verification_results: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    propaganda_techniques: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    sentiment_breakdown: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    suspicious_passages: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    evidence_references: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    knowledge_graph_data: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    credibility_breakdown: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    student_summary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    technical_explanation: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    model_confidence_data: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    explainability_data: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # SHAP / LIME

    # ── Blockchain ────────────────────────────────────────────
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )

    # ── MongoDB reference (full raw results) ──────────────────
    mongo_result_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )

    # ── Relationships ─────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="analyses")
