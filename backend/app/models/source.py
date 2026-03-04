# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Trusted Source Model (PostgreSQL)
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, Float, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TrustedSource(Base):
    __tablename__ = "trusted_sources"

    domain: Mapped[str] = mapped_column(
        String(512), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    credibility_score: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False
    )
    historical_accuracy: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False
    )
    editorial_standards: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False
    )
    ownership_transparency: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False
    )
    correction_record: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False
    )

    is_approved: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_blacklisted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )
    country: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    total_analyses: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    fake_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, nullable=True
    )
