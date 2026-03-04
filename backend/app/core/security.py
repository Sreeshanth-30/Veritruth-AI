# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Security Utilities (JWT, hashing, OAuth)
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

# ── Password Hashing (bcrypt direct — passlib incompatible with bcrypt 5+) ────
_BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ── JWT Tokens ────────────────────────────────────────────────
def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": now, "type": "access"})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        or timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "iat": now, "type": "refresh"})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises JWTError on failure."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


# ── CSRF Tokens ───────────────────────────────────────────────
def generate_csrf_token() -> str:
    return secrets.token_hex(32)


def verify_csrf_token(token: str, expected: str) -> bool:
    return secrets.compare_digest(token, expected)


# ── Blockchain Hash (verification stamp) ─────────────────────
def compute_article_hash(content: str) -> str:
    """SHA-256 hash used for blockchain verification of analyzed content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
