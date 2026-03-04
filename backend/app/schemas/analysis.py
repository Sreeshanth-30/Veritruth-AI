# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Analysis Schemas (Pydantic v2)
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from app.models.analysis import AnalysisStatus, InputType, RiskLevel


# ── Sub-schemas ───────────────────────────────────────────────
class ClaimVerification(BaseModel):
    claim_text: str
    verdict: str  # "REFUTED" | "UNVERIFIABLE" | "SUPPORTED"
    confidence: float = Field(..., ge=0, le=1)
    evidence: str
    source: Optional[str] = None


class SuspiciousPassage(BaseModel):
    text: str
    start_index: int
    end_index: int
    severity: str  # "high" | "medium" | "low"
    reason: str
    technique: Optional[str] = None


class EvidenceReference(BaseModel):
    title: str
    source: str
    url: Optional[str] = None
    relationship: str  # "CONTRADICTS" | "SUPPORTS" | "REFUTES"
    summary: str


class SentimentBreakdown(BaseModel):
    fear: float = Field(0, ge=0, le=100)
    excitement: float = Field(0, ge=0, le=100)
    anger: float = Field(0, ge=0, le=100)
    trust: float = Field(0, ge=0, le=100)
    surprise: float = Field(0, ge=0, le=100)
    disgust: float = Field(0, ge=0, le=100)


class PropagandaTechnique(BaseModel):
    technique: str
    confidence: float = Field(..., ge=0, le=1)
    instances: list[str] = []


class DeepfakeResult(BaseModel):
    is_manipulated: bool
    manipulation_probability: float = Field(..., ge=0, le=1)
    exif_metadata: Optional[dict[str, Any]] = None
    analysis_details: Optional[str] = None


class KnowledgeGraphNode(BaseModel):
    id: str
    label: str
    type: str  # "Claim" | "VerifiedFact" | "DisputedFact" | "Source" | "Entity"
    color: str


class KnowledgeGraphEdge(BaseModel):
    source: str
    target: str
    label: str


class KnowledgeGraphData(BaseModel):
    nodes: list[KnowledgeGraphNode] = []
    edges: list[KnowledgeGraphEdge] = []
    conflicts: int = 0
    verified: int = 0


class ModelConfidenceData(BaseModel):
    classifier_confidence: float = Field(0, ge=0, le=1)
    propaganda_confidence: float = Field(0, ge=0, le=1)
    fact_check_confidence: float = Field(0, ge=0, le=1)
    bias_confidence: float = Field(0, ge=0, le=1)
    credibility_confidence: float = Field(0, ge=0, le=1)
    ensemble_agreement: float = Field(0, ge=0, le=1)


# ── Request Schemas ───────────────────────────────────────────
class AnalysisTextRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=100_000)
    language: str = Field("en", max_length=5)
    enable_deepfake: bool = False
    enable_propaganda: bool = True
    enable_fact_check: bool = True
    enable_bias: bool = True

    @field_validator("text")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        """Basic XSS prevention — strip script tags."""
        import re
        return re.sub(r"<script[^>]*>.*?</script>", "", v, flags=re.DOTALL | re.IGNORECASE)


class AnalysisURLRequest(BaseModel):
    url: HttpUrl
    language: str = Field("en", max_length=5)
    enable_deepfake: bool = False
    enable_propaganda: bool = True
    enable_fact_check: bool = True
    enable_bias: bool = True


# ── Response Schemas ──────────────────────────────────────────
class AnalysisCreateResponse(BaseModel):
    id: uuid.UUID
    status: AnalysisStatus
    celery_task_id: Optional[str] = None
    message: str = "Analysis queued successfully"


class AnalysisStatusResponse(BaseModel):
    id: uuid.UUID
    status: AnalysisStatus
    progress: Optional[int] = None  # 0-100
    current_step: Optional[str] = None


class AnalysisResultResponse(BaseModel):
    id: uuid.UUID
    status: AnalysisStatus
    input_type: InputType
    article_title: Optional[str] = None
    title: Optional[str] = None  # frontend-compatible alias for article_title
    source_url: Optional[str] = None
    processing_time_ms: Optional[int] = None

    # ── Scores ────────────────────────────────────────────────
    overall_risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    fake_probability: Optional[float] = None
    propaganda_score: Optional[float] = None
    credibility_score: Optional[float] = None
    bias_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    emotional_manipulation_score: Optional[float] = None
    deepfake_score: Optional[float] = None

    # ── Detailed Results (flexible JSON — accept any shape) ───
    detected_claims: Optional[Any] = None
    suspicious_passages: Optional[Any] = None
    evidence_references: Optional[Any] = None
    sentiment_breakdown: Optional[Any] = None
    propaganda_techniques: Optional[Any] = None
    fact_verification_results: Optional[Any] = None
    deepfake_result: Optional[Any] = None
    knowledge_graph: Optional[Any] = None
    knowledge_graph_data: Optional[Any] = None
    model_confidence: Optional[Any] = None
    explainability_data: Optional[Any] = None
    classification_label: Optional[str] = None
    confidence_score: Optional[float] = None
    claim_count: Optional[int] = None
    verified_true_count: Optional[int] = None
    verified_false_count: Optional[int] = None
    credibility_breakdown: Optional[Any] = None
    error_message: Optional[str] = None

    # ── Summaries ─────────────────────────────────────────────
    student_summary: Optional[str] = None
    technical_explanation: Optional[str] = None

    # ── Blockchain ────────────────────────────────────────────
    content_hash: Optional[str] = None

    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def populate_title(self) -> "AnalysisResultResponse":
        """Populate the frontend-friendly `title` field from `article_title`."""
        if not self.title and self.article_title:
            self.title = self.article_title
        return self


class AnalysisListResponse(BaseModel):
    items: list[AnalysisResultResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
