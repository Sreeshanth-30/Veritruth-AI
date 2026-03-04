# ──────────────────────────────────────────────────────────────
# VeriTruth AI — User Model (PostgreSQL)
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.analysis import Analysis


class UserRole(str, enum.Enum):
    STUDENT = "student"
    EDUCATOR = "educator"
    RESEARCHER = "researcher"
    JOURNALIST = "journalist"
    ADMIN = "admin"


class AuthProvider(str, enum.Enum):
    LOCAL = "local"
    GOOGLE = "google"


class User(Base):
    __tablename__ = "users"

    # ── Identity ──────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True  # nullable for OAuth users
    )

    # ── Profile ───────────────────────────────────────────────
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.STUDENT, nullable=False
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    institution: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # ── Auth ──────────────────────────────────────────────────
    auth_provider: Mapped[AuthProvider] = mapped_column(
        Enum(AuthProvider), default=AuthProvider.LOCAL, nullable=False
    )
    google_id: Mapped[Optional[str]] = mapped_column(
        String(128), unique=True, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # ── Rate Limiting ─────────────────────────────────────────
    analysis_count_today: Mapped[int] = mapped_column(default=0)

    # ── Relationships ─────────────────────────────────────────
    analyses: Mapped[list["Analysis"]] = relationship(
        "Analysis", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
