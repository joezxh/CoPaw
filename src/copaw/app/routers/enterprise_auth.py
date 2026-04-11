# -*- coding: utf-8 -*-
"""
Enterprise Authentication API Router
POST /api/enterprise/auth/login
POST /api/enterprise/auth/register
POST /api/enterprise/auth/logout
GET  /api/enterprise/auth/me
PUT  /api/enterprise/auth/password
POST /api/enterprise/auth/mfa/setup
POST /api/enterprise/auth/mfa/verify
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from ...db.postgresql import get_db_session
from ...enterprise.auth_service import AuthService
from ...enterprise.audit_service import AuditService, AuditAction
from ...enterprise.middleware import get_current_user
from ...enterprise.alert_service import check_login_anomaly

router = APIRouter(prefix="/api/enterprise/auth", tags=["enterprise-auth"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str
    mfa_code: Optional[str] = None


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8)
    email: Optional[str] = None
    display_name: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class MFASetupResponse(BaseModel):
    secret: str
    otpauth_url: str


class MFAVerifyRequest(BaseModel):
    secret: str
    code: str


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/login")
async def login(body: LoginRequest, request: Request):
    """Authenticate and receive JWT token pair."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    async with get_db_session() as session:
        try:
            result = await AuthService.login(
                session,
                username=body.username,
                password=body.password,
                ip_address=client_ip,
                user_agent=user_agent,
            )
            # MFA verification if required
            if body.mfa_code is None:
                # Check if user has MFA enabled — load user
                from sqlalchemy import select
                from ...db.models.user import User
                user = await session.scalar(
                    select(User).where(User.username == body.username)
                )
                if user and user.mfa_enabled:
                    raise HTTPException(
                        status_code=428,
                        detail="MFA code required",
                    )

            await AuditService.log(
                session,
                action_type=AuditAction.USER_LOGIN,
                resource_type="user",
                resource_id=body.username,
                result="success",
                client_ip=client_ip,
            )
            return result
        except HTTPException:
            raise
        except ValueError as exc:
            await AuditService.log(
                session,
                action_type=AuditAction.USER_LOGIN,
                resource_type="user",
                resource_id=body.username,
                result="failure",
                client_ip=client_ip,
                context={"reason": str(exc)},
            )
            await check_login_anomaly(body.username, client_ip)
            raise HTTPException(status_code=401, detail=str(exc))

@router.post("/register", status_code=201)
async def register(body: RegisterRequest, request: Request):
    """Register a new user (admin or first-user bootstrap)."""
    async with get_db_session() as session:
        try:
            user = await AuthService.register(
                session,
                username=body.username,
                password=body.password,
                email=body.email,
                display_name=body.display_name,
            )
            await AuditService.log(
                session,
                action_type=AuditAction.USER_REGISTER,
                resource_type="user",
                resource_id=str(user.id),
                result="success",
                client_ip=request.client.host if request.client else None,
            )
            return {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name,
            }
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Revoke the current session."""
    jti = current_user["jti"]
    async with get_db_session() as session:
        await AuthService.logout(session, jti)
        await AuditService.log(
            session,
            action_type=AuditAction.USER_LOGOUT,
            resource_type="user",
            resource_id=current_user["user_id"],
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
        )
    return {"detail": "Logged out"}


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    """Return current user information from token payload."""
    return current_user


@router.put("/password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
):
    """Change the current user's password."""
    user_id = uuid.UUID(current_user["user_id"])
    async with get_db_session() as session:
        try:
            await AuthService.change_password(
                session,
                user_id=user_id,
                current_password=body.current_password,
                new_password=body.new_password,
            )
            await AuditService.log(
                session,
                action_type=AuditAction.PASSWORD_CHANGE,
                resource_type="user",
                resource_id=str(user_id),
                result="success",
                user_id=user_id,
                is_sensitive=True,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    return {"detail": "Password updated"}


@router.post("/mfa/setup")
async def mfa_setup(current_user: dict = Depends(get_current_user)):
    """Generate MFA secret and provisioning URI for QR code display."""
    secret, uri = AuthService.generate_mfa_secret()
    return MFASetupResponse(secret=secret, otpauth_url=uri)


@router.post("/mfa/verify")
async def mfa_verify(
    body: MFAVerifyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Confirm and enable MFA for the current user."""
    user_id = uuid.UUID(current_user["user_id"])
    async with get_db_session() as session:
        try:
            await AuthService.enable_mfa(session, user_id, body.secret, body.code)
            await AuditService.log(
                session,
                action_type=AuditAction.MFA_ENABLE,
                resource_type="user",
                resource_id=str(user_id),
                result="success",
                user_id=user_id,
                is_sensitive=True,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    return {"detail": "MFA enabled"}
