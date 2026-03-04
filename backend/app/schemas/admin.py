# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Admin Schemas
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    total_analyses: int
    fake_detected: int
    questionable: int
    credible: int
    active_users: int
    flagged_domains: int
    pending_reviews: int
    model_accuracy: float


class TrendDataPoint(BaseModel):
    date: str
    fake_count: int
    credible_count: int
    total_count: int


class TopicMisinformation(BaseModel):
    topic: str
    percentage: float
    article_count: int


class DomainRisk(BaseModel):
    domain: str
    risk_percentage: float
    total_analyses: int
    fake_count: int


class UserActivityLog(BaseModel):
    user_id: uuid.UUID
    username: str
    action: str
    article_title: Optional[str] = None
    verdict: Optional[str] = None
    timestamp: datetime


class TrustedSourceRequest(BaseModel):
    domain: str
    name: str
    credibility_score: float = Field(0.5, ge=0, le=1)
    category: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None


class TrustedSourceResponse(BaseModel):
    id: uuid.UUID
    domain: str
    name: str
    credibility_score: float
    is_approved: bool
    is_blacklisted: bool
    total_analyses: int
    fake_count: int
    category: Optional[str] = None
    country: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TrainingLabelRequest(BaseModel):
    analysis_id: uuid.UUID
    label: str  # "fake" | "credible" | "questionable"
    notes: Optional[str] = None


class AnalyticsResponse(BaseModel):
    daily_trends: list[TrendDataPoint]
    topic_breakdown: list[TopicMisinformation]
    sentiment_distribution: dict[str, float]
    top_flagged_domains: list[DomainRisk]
    detection_heatmap: list[list[int]]  # weeks x days
