# -*- coding: utf-8 -*-
"""
SSO Router for OpenID Connect (OIDC) authentication endpoints.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...db.postgresql import get_db_session
from ...db.models.user import User
from ...db.models.tenant import Tenant
from ...enterprise.sso_client import oauth, get_sso_client
from ...enterprise.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sso", tags=["sso"])


@router.get("/login/{provider}")
async def sso_login(provider: str, request: Request):
    """
    Redirects the user to the SSO provider's authorization page.
    """
    client = await get_sso_client(provider)
    if not client:
        raise HTTPException(status_code=404, detail="SSO provider not configured.")

    redirect_uri = str(request.url_for("sso_callback", provider=provider))
    # We use authlib's starlette client mapping
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/callback/{provider}")
async def sso_callback(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Handles the callback from the SSO provider, maps the user, and issues a JWT token.
    For the mock provider, we simulate receiving a payload.
    """
    client = await get_sso_client(provider)
    if not client:
        raise HTTPException(status_code=404, detail="SSO provider not found.")

    try:
        # In actual OIDC: token = await client.authorize_access_token(request)
        # user_info = token.get('userinfo') or await client.userinfo()
        # Mocking the payload since we do not have a real server to return it
        if provider == "mock":
            user_info = {
                "email": "admin@enterprise.local",
                "name": "OIDC Admin",
                "sub": "mock-admin-sub"
            }
        else:
            token = await client.authorize_access_token(request)
            user_info = token.get('userinfo')
            if not user_info:
                user_info = await client.userinfo()

    except Exception as e:
        logger.error(f"SSO Callback failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Authentication failed from SSO Provider.")

    # 1. Check if user exists by email
    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="SSO Provider did not return an email.")

    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # 2. Auto-provision user if new
    if not user:
        # Default tenant resolution logic (Mocked to the system default here)
        user = User(
            username=user_info.get("name", email.split("@")[0]),
            email=email,
            password_hash="sso-managed",  # No local password via SSO
            tenant_id="default-tenant"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # 3. Create CoPaw Enterprise Access Token
    roles = []  # Usually mapped during provisioning
    token_dict = await create_access_token(
        db=db,
        user_id=str(user.id),
        username=user.username,
        roles=roles,
        tenant_id=user.tenant_id
    )

    return {
        "success": True,
        "message": "SSO authentication successful.",
        "access_token": token_dict["access_token"],
        "token_type": "bearer",
        "expires_in": token_dict["expires_in"]
    }
