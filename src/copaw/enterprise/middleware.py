# -*- coding: utf-8 -*-
"""
EnterpriseAuthMiddleware — replaces the legacy single-user AuthMiddleware.

Features:
- Verifies JWT Bearer tokens via AuthService
- Injects request.state.user_id, .username, .roles, .jti
- Supports token revocation check (via PostgreSQL session table)
- Skips public paths and OPTIONS
- Returns JSON 401/403 for clear API client error handling
"""
from __future__ import annotations

import json
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..db.postgresql import get_db_session
from ..enterprise.auth_service import decode_access_token
from ..enterprise.dlp_service import check_text_with_db, log_dlp_event

logger = logging.getLogger(__name__)

# ── Public paths (no auth required) ─────────────────────────────────────────
_PUBLIC_PATHS: frozenset[str] = frozenset({
    "/api/enterprise/auth/login",
    "/api/enterprise/auth/register",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/status",
    "/api/version",
    "/api/settings/language",
    "/docs",
    "/redoc",
    "/openapi.json",
})

_PUBLIC_PREFIXES: tuple[str, ...] = (
    "/assets/",
    "/logo.png",
    "/copaw-symbol.svg",
    "/api/enterprise/auth/",   # all auth sub-paths (register, login, refresh)
)


def _json_response(status: int, detail: str) -> Response:
    return Response(
        content=json.dumps({"detail": detail}),
        status_code=status,
        media_type="application/json",
    )


class EnterpriseAuthMiddleware(BaseHTTPMiddleware):
    """JWT-based auth middleware for enterprise multi-user mode.

    Validates access token on every protected /api/ route.
    Does NOT hit the database (that's AuthService's job in the router).
    Token signature + expiry is verified inline for speed.
    Session revocation can be checked per-route via AuthService.verify_access_token().
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Always pass OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Static assets and non-API paths pass through
        if not path.startswith("/api/"):
            return await call_next(request)

        # Public paths pass through
        if path in _PUBLIC_PATHS or any(
            path.startswith(p) for p in _PUBLIC_PREFIXES
        ):
            return await call_next(request)

        # Extract Bearer token
        token = _extract_token(request)
        if not token:
            return _json_response(401, "Not authenticated")

        # Verify token (signature + expiry only — revocation is per-route)
        payload = decode_access_token(token)
        if not payload:
            return _json_response(401, "Invalid or expired token")

        # Inject user context into request state
        request.state.user_id = payload.get("sub")
        request.state.username = payload.get("username")
        request.state.roles = payload.get("roles", [])
        request.state.jti = payload.get("jti")
        request.state.username = payload.get("sub", "")
        request.state.jti = payload.get("jti", "")
        # Tenant extraction (from JWT or header, default to "default-tenant")
        request.state.tenant_id = request.headers.get("X-Tenant-Id", payload.get("tenant_id", "default-tenant"))

        # In a real isolation pattern, you'd bind engine/session context here.
        response = await call_next(request)

        # Apply DLP scanning to JSON responses on protected /api/ routes
        if response.headers.get("content-type") == "application/json":
            body_chunks = []
            async for chunk in response.body_iterator:
                body_chunks.append(chunk)
            body = b"".join(body_chunks)

            if body:
                text = body.decode("utf-8")
                async with get_db_session() as session:
                    dlp_result = await check_text_with_db(text, session)
                    if dlp_result.has_violations:
                        await log_dlp_event(
                            session, 
                            dlp_result, 
                            user_id=request.state.user_id, 
                            context_path=path
                        )
                        await session.commit()
                        
                        # Re-pack response with masked body (or block)
                        if dlp_result.blocked:
                            return _json_response(403, "Content blocked by DLP policy")
                        
                        body = dlp_result.cleaned_text.encode("utf-8")
                        # Remove content-length since we changed it
                        if "content-length" in response.headers:
                            del response.headers["content-length"]

            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        return response


def _extract_token(request: Request) -> str | None:
    """Extract Bearer token from Authorization header or ?token query param."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    # WebSocket upgrade or fallback query param
    token = request.query_params.get("token")
    return token or None


# ── FastAPI dependency — get current user ─────────────────────────────────

from fastapi import HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

_security = HTTPBearer(auto_error=False)


async def get_current_user(request: Request) -> dict:
    """FastAPI dependency — returns current user dict from request state.

    Use in route functions: ``current_user: dict = Depends(get_current_user)``
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "user_id": user_id,
        "username": getattr(request.state, "username", ""),
        "roles": getattr(request.state, "roles", []),
        "jti": getattr(request.state, "jti", ""),
    }


async def require_role(*required_roles: str):
    """FastAPI dependency factory — raises 403 if user lacks one of the required roles."""
    async def _check(current_user: dict = __import__("fastapi").Depends(get_current_user)):
        user_roles: list[str] = current_user.get("roles", [])
        if not any(r in user_roles for r in required_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of roles: {list(required_roles)}",
            )
        return current_user
    return _check
