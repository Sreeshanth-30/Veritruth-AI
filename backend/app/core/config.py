# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Backend Configuration (Pydantic Settings)
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised application configuration loaded from env vars / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "VeriTruth AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_VERSION: str = "v1"
    API_PREFIX: str = "/api/v1"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    SECRET_KEY: str = "change-me-to-a-random-64-char-hex-string"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"

    # ── JWT ───────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-jwt-secret-key-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── PostgreSQL / SQLite ──────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./veritruth.db"

    # ── MongoDB ───────────────────────────────────────────────
    MONGODB_URL: str = "mongodb://localhost:27017/veritruth_news"
    MONGODB_DB: str = "veritruth_news"

    # ── Neo4j ─────────────────────────────────────────────────
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "change-me-neo4j-password"

    # ── Redis / Celery ────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── Google OAuth ──────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ── AI Models ─────────────────────────────────────────────
    MODEL_CACHE_DIR: str = "./models"
    FAKE_NEWS_MODEL: str = "roberta-base"
    PROPAGANDA_MODEL: str = "bert-base-uncased"
    SENTIMENT_MODEL: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    DEEPFAKE_MODEL: str = "./models/deepfake_cnn.pth"
    SPACY_MODEL: str = "en_core_web_trf"

    # ── External APIs ─────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    GOOGLE_FACT_CHECK_API_KEY: str = ""

    # ── Rate Limiting ─────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_ANALYSIS_PER_HOUR: int = 20

    # ── CORS ──────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000"

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # ── Computed Properties ───────────────────────────────────
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def allowed_hosts_list(self) -> List[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


@lru_cache()
def get_settings() -> Settings:
    """Singleton factory – cached after first call."""
    return Settings()
