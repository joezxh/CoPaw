# -*- coding: utf-8 -*-
"""
Enterprise Single Sign-On (SSO) Client via Authlib.
Supports Mock OIDC providers for development.
"""
from __future__ import annotations

import logging
from authlib.integrations.starlette_client import OAuth
from fastapi import Request
from starlette.config import Config

logger = logging.getLogger(__name__)

# Usually configurations come from a DB or env. 
# We use a mock dict here for the 'mock' provider as requested.
OIDC_PROVIDERS = {
    "mock": {
        "client_id": "mock-client-id",
        "client_secret": "mock-client-secret",
        "server_metadata_url": "https://mock-oidc.local/.well-known/openid-configuration",
        "client_kwargs": {"scope": "openid email profile"},
    }
}

oauth = OAuth()

def register_mock_providers():
    """Register the mock OIDC provider for testing."""
    oauth.register(
        name='mock',
        client_id=OIDC_PROVIDERS["mock"]["client_id"],
        client_secret=OIDC_PROVIDERS["mock"]["client_secret"],
        server_metadata_url=OIDC_PROVIDERS["mock"]["server_metadata_url"],
        client_kwargs=OIDC_PROVIDERS["mock"]["client_kwargs"],
    )
    logger.info("Registered mock OIDC provider for Phase C Enterprise SSO.")

# Initialize registries
register_mock_providers()

async def get_sso_client(name: str):
    """Retrieve the Authlib remote app dynamically."""
    return oauth.create_client(name)
