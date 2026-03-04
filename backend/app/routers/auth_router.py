# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Auth Router
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import AuthProvider, User
from app.schemas.auth import (
    AuthResponse,
    GoogleOAuthRequest,
    LoginRequest,
    RefreshTokenRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(tags=["Authentication"])


def _build_tokens(user: User) -> TokenResponse:
    """Helper to generate access + refresh token pair."""
    access = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    refresh = create_refresh_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        role=user.role,
        avatar_url=user.avatar_url,
        institution=user.institution,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )


# ── Signup ────────────────────────────────────────────────────
@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account with email + password."""
    # Check for duplicate email
    exists = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    if exists.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=body.email.lower(),
        first_name=body.first_name,
        last_name=body.last_name,
        hashed_password=hash_password(body.password),
        role=body.role,
        institution=body.institution,
        auth_provider=AuthProvider.LOCAL,
        is_verified=False,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    tokens = _build_tokens(user)
    logger.info("User registered: %s (%s)", user.email, user.role.value)
    return AuthResponse(user=_user_response(user), tokens=tokens)


# ── Login ─────────────────────────────────────────────────────
@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with email + password and receive JWT tokens."""
    result = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated",
        )

    tokens = _build_tokens(user)
    logger.info("User logged in: %s", user.email)
    return AuthResponse(user=_user_response(user), tokens=tokens)


# ── Refresh Token ─────────────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
):
    """Exchange a valid refresh token for a new token pair."""
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(400, "Invalid token type")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    result = await db.execute(
        select(User).where(User.id == payload["sub"])
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(404, "User not found or inactive")

    return _build_tokens(user)


# ── Google OAuth ──────────────────────────────────────────────
@router.post("/google", response_model=AuthResponse)
async def google_oauth(
    body: GoogleOAuthRequest, db: AsyncSession = Depends(get_db)
):
    """Authenticate or register via Google OAuth2 authorization code."""
    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": body.code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": body.redirect_uri or settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(400, "Failed to exchange Google auth code")

        google_tokens = token_resp.json()
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {google_tokens['access_token']}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(400, "Failed to fetch Google user info")

        info = userinfo_resp.json()

    # Find or create user
    result = await db.execute(
        select(User).where(User.google_id == info["id"])
    )
    user = result.scalar_one_or_none()

    if not user:
        # Check if email already registered locally
        result = await db.execute(
            select(User).where(User.email == info["email"].lower())
        )
        user = result.scalar_one_or_none()
        if user:
            # Link Google account
            user.google_id = info["id"]
            user.auth_provider = AuthProvider.GOOGLE
            if not user.avatar_url:
                user.avatar_url = info.get("picture")
        else:
            # Create new user
            user = User(
                email=info["email"].lower(),
                first_name=info.get("given_name", ""),
                last_name=info.get("family_name", ""),
                google_id=info["id"],
                avatar_url=info.get("picture"),
                auth_provider=AuthProvider.GOOGLE,
                is_verified=info.get("verified_email", False),
            )
            db.add(user)

    await db.flush()
    await db.refresh(user)

    tokens = _build_tokens(user)
    return AuthResponse(user=_user_response(user), tokens=tokens)


# ── Current User Profile ─────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return _user_response(current_user)
