# -*- coding: utf-8 -*-
"""
Enterprise AuthService — multi-user JWT authentication with bcrypt passwords.

Responsibilities:
- Register / login / logout users (stored in PostgreSQL)
- Issue / verify / revoke JWT access tokens (python-jose)
- Hash passwords with bcrypt (passlib)
- TOTP MFA verification (pyotp)
- Session lifecycle management (Redis TTL mirror + PostgreSQL audit row)
"""
from __future__ import annotations

import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models.user import User
from ..db.models.session import UserSession, RefreshToken

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
_JWT_SECRET = os.environ.get("COPAW_JWT_SECRET", "change-me-in-production")
_JWT_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("COPAW_JWT_ACCESS_EXPIRE_MINUTES", "60")
)
_REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.environ.get("COPAW_JWT_REFRESH_EXPIRE_DAYS", "7")
)

_pwd_ctx = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Password helpers ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> tuple[str, str]:
    """Return (bcrypt_hash, empty_salt).  Salt is embedded in bcrypt hash."""
    salt = secrets.token_hex(16)          # stored for legacy compat column
    hashed = _pwd_ctx.hash(plain)
    return hashed, salt


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


# ── JWT helpers ──────────────────────────────────────────────────────────────

def _create_access_token(
    user_id: str,
    username: str,
    roles: list[str],
    jti: str,
    expires_delta: timedelta | None = None,
) -> str:
    expire = _utcnow() + (
        expires_delta or timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": user_id,
        "username": username,
        "roles": roles,
        "jti": jti,
        "exp": expire,
        "iat": _utcnow(),
        "type": "access",
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


def _create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def decode_access_token(token: str) -> dict | None:
    """Decode and verify access token. Returns payload dict or None."""
    try:
        payload = jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError as exc:
        logger.debug("JWT decode failed: %s", exc)
        return None


# ── AuthService ──────────────────────────────────────────────────────────────

class AuthService:
    """Stateless service; inject an AsyncSession per request."""

    # ── Registration ────────────────────────────────────────────────────────

    @staticmethod
    async def register(
        session: AsyncSession,
        username: str,
        password: str,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> User:
        """Create a new user. Raises ValueError on duplicate username/email."""
        # Check uniqueness
        existing = await session.scalar(
            select(User).where(User.username == username)
        )
        if existing:
            raise ValueError(f"Username '{username}' already taken")

        if email:
            existing_email = await session.scalar(
                select(User).where(User.email == email)
            )
            if existing_email:
                raise ValueError(f"Email '{email}' already registered")

        pw_hash, pw_salt = hash_password(password)
        user = User(
            username=username,
            email=email,
            password_hash=pw_hash,
            password_salt=pw_salt,
            display_name=display_name or username,
            status="active",
        )
        session.add(user)
        await session.flush()  # populate user.id without committing
        logger.info("Registered new user: %s (id=%s)", username, user.id)
        return user

    # ── Login ────────────────────────────────────────────────────────────────

    @staticmethod
    async def login(
        session: AsyncSession,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """Authenticate user, create session, return token pair.

        Returns dict with ``access_token``, ``refresh_token``, ``token_type``.
        Raises ValueError on invalid credentials or disabled account.
        """
        user: Optional[User] = await session.scalar(
            select(User).where(User.username == username)
        )
        if not user:
            raise ValueError("Invalid credentials")
        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")
        if user.status != "active":
            raise ValueError(f"Account is {user.status}")

        # Update last login
        user.last_login_at = _utcnow()

        # Create session record
        jti = secrets.token_hex(32)
        now = _utcnow()
        access_expires = now + timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_expires = now + timedelta(days=_REFRESH_TOKEN_EXPIRE_DAYS)

        # Collect role names for JWT
        await session.refresh(user, ["roles"])
        role_names: list[str] = []
        for ur in user.roles:
            await session.refresh(ur, ["role"])
            role_names.append(ur.role.name)

        db_session = UserSession(
            user_id=user.id,
            access_token_jti=jti,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
            expires_at=access_expires,
        )
        session.add(db_session)
        await session.flush()

        # Refresh token (hashed)
        raw_refresh = _create_refresh_token()
        import hashlib
        refresh_hash = hashlib.sha256(raw_refresh.encode()).hexdigest()
        rt = RefreshToken(
            session_id=db_session.id,
            token_hash=refresh_hash,
            created_at=now,
            expires_at=refresh_expires,
        )
        session.add(rt)

        access_token = _create_access_token(
            user_id=str(user.id),
            username=user.username,
            roles=role_names,
            jti=jti,
        )

        logger.info("User %s logged in from %s", username, ip_address)
        return {
            "access_token": access_token,
            "refresh_token": raw_refresh,
            "token_type": "bearer",
            "expires_in": _ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user_id": str(user.id),
            "username": user.username,
            "roles": role_names,
        }

    # ── Token verification ───────────────────────────────────────────────────

    @staticmethod
    async def verify_access_token(
        session: AsyncSession,
        token: str,
    ) -> Optional[dict]:
        """Verify token and ensure session is not revoked. Returns payload."""
        payload = decode_access_token(token)
        if not payload:
            return None

        jti = payload.get("jti")
        if not jti:
            return None

        # Check session in DB (revocation check)
        db_session = await session.scalar(
            select(UserSession).where(
                UserSession.access_token_jti == jti,
                UserSession.revoked.is_(False),
                UserSession.expires_at > _utcnow(),
            )
        )
        if not db_session:
            return None

        return payload

    # ── Logout ───────────────────────────────────────────────────────────────

    @staticmethod
    async def logout(session: AsyncSession, jti: str) -> None:
        """Revoke the session identified by jti."""
        await session.execute(
            update(UserSession)
            .where(UserSession.access_token_jti == jti)
            .values(revoked=True, revoked_at=_utcnow())
        )
        logger.debug("Session jti=%s revoked", jti)

    # ── Password change ──────────────────────────────────────────────────────

    @staticmethod
    async def change_password(
        session: AsyncSession,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        user = await session.get(User, user_id)
        if not user:
            raise ValueError("User not found")
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password incorrect")
        new_hash, new_salt = hash_password(new_password)
        user.password_hash = new_hash
        user.password_salt = new_salt
        # Revoke all existing sessions
        await session.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked.is_(False))
            .values(revoked=True, revoked_at=_utcnow())
        )
        logger.info("Password changed for user_id=%s", user_id)

    # ── MFA ──────────────────────────────────────────────────────────────────

    @staticmethod
    def generate_mfa_secret() -> tuple[str, str]:
        """Return (secret, otpauth_url) for QR code display."""
        import pyotp
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name="CoPaw Enterprise", issuer_name="CoPaw")
        return secret, uri

    @staticmethod
    def verify_mfa_code(secret: str, code: str) -> bool:
        import pyotp
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)

    @staticmethod
    async def enable_mfa(
        session: AsyncSession,
        user_id: uuid.UUID,
        secret: str,
        code: str,
    ) -> None:
        if not AuthService.verify_mfa_code(secret, code):
            raise ValueError("Invalid MFA code")
        user = await session.get(User, user_id)
        if not user:
            raise ValueError("User not found")
        user.mfa_enabled = True
        user.mfa_secret = secret
    @staticmethod
    async def create_access_token(
        session: AsyncSession,
        user_id: str,
        username: str,
        roles: list[str],
        tenant_id: str = "default-tenant",
    ) -> dict:
        """Create a new access token for an existing user (e.g., after SSO login)."""
        jti = secrets.token_hex(32)
        now = _utcnow()
        access_expires = now + timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)

        # Create session record
        db_session = UserSession(
            user_id=uuid.UUID(user_id),
            access_token_jti=jti,
            ip_address=None,
            user_agent="SSO",
            created_at=now,
            expires_at=access_expires,
        )
        session.add(db_session)
        await session.flush()

        access_token = _create_access_token(
            user_id=user_id,
            username=username,
            roles=roles,
            jti=jti,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": _ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user_id": user_id,
            "username": username,
            "roles": roles,
        }