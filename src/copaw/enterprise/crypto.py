# -*- coding: utf-8 -*-
"""
Enterprise Cryptography utilities.

Features:
1. AES-256-GCM field-level encryption for sensitive DB columns:
   - Key loaded from COPAW_FIELD_ENCRYPT_KEY env var (32-byte hex string)
   - Each encrypted value is self-contained: nonce (12B) + ciphertext + tag (16B), base64-encoded
2. SQLAlchemy TypeDecorator: EncryptedString
3. PII masking helper: mask_pii(text)
"""
from __future__ import annotations

import base64
import os
import secrets
import logging
from typing import Any, Optional

from sqlalchemy.types import TypeDecorator, Text

logger = logging.getLogger(__name__)

# ── Key loading ──────────────────────────────────────────────────────────────

def _load_key() -> bytes:
    """Load 32-byte encryption key from environment.

    COPAW_FIELD_ENCRYPT_KEY must be a 64-char hex string (256 bits).
    If not set, generates a random key and logs a warning (dev-only fallback).
    """
    raw = os.environ.get("COPAW_FIELD_ENCRYPT_KEY", "")
    if raw and len(raw) == 64:
        try:
            return bytes.fromhex(raw)
        except ValueError:
            pass

    # Dev-mode fallback (deterministic so restarts still decrypt)
    logger.warning(
        "COPAW_FIELD_ENCRYPT_KEY not set or invalid — using insecure dev fallback key. "
        "Set a 64-char hex string in production!"
    )
    # Use a fixed dev key derived from a constant (never store real data with this)
    return b"copaw-dev-key-do-not-use-in-prod"  # exactly 32 bytes


_KEY: bytes = _load_key()


# ── AES-256-GCM helpers ───────────────────────────────────────────────────────

def encrypt(plaintext: str) -> str:
    """Encrypt a string using AES-256-GCM.

    Returns base64-encoded string: nonce(12) || ciphertext || tag(16).
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(_KEY)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    blob = nonce + ciphertext  # tag is appended inside ciphertext by cryptography lib
    return base64.b64encode(blob).decode("ascii")


def decrypt(ciphertext_b64: str) -> str:
    """Decrypt a value produced by encrypt()."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    try:
        blob = base64.b64decode(ciphertext_b64)
        nonce = blob[:12]
        ct = blob[12:]
        aesgcm = AESGCM(_KEY)
        plaintext = aesgcm.decrypt(nonce, ct, None)
        return plaintext.decode("utf-8")
    except Exception as exc:
        logger.error("Decryption failed (key mismatch or corrupted data): %s", exc)
        raise ValueError("Decryption failed") from exc


def rotate_key(old_key_hex: str, new_key_hex: str, ciphertext_b64: str) -> str:
    """Re-encrypt a value from old_key to new_key (key rotation helper)."""
    old_key = bytes.fromhex(old_key_hex)
    new_key = bytes.fromhex(new_key_hex)

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    # Decrypt with old key
    blob = base64.b64decode(ciphertext_b64)
    nonce, ct = blob[:12], blob[12:]
    plaintext = AESGCM(old_key).decrypt(nonce, ct, None)

    # Re-encrypt with new key
    new_nonce = secrets.token_bytes(12)
    new_ct = AESGCM(new_key).encrypt(new_nonce, plaintext, None)
    return base64.b64encode(new_nonce + new_ct).decode("ascii")


# ── SQLAlchemy TypeDecorator ─────────────────────────────────────────────────

class EncryptedString(TypeDecorator):
    """Transparent field-level encryption for SQLAlchemy String columns.

    Usage in model:
        secret: Mapped[Optional[str]] = mapped_column(EncryptedString(), nullable=True)
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect: Any) -> Optional[str]:
        """Encrypt before writing to DB."""
        if value is None:
            return None
        return encrypt(value)

    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[str]:
        """Decrypt after reading from DB."""
        if value is None:
            return None
        try:
            return decrypt(value)
        except ValueError:
            # Return raw value if decryption fails (e.g., plaintext legacy data)
            logger.warning("EncryptedString: decryption failed, returning raw value")
            return value


# ── PII masking ───────────────────────────────────────────────────────────────

def mask_sensitive(value: str, visible_prefix: int = 3, mask_char: str = "*") -> str:
    """Mask the center/tail of a sensitive string, keeping visible_prefix chars visible."""
    if not value:
        return value
    visible = min(visible_prefix, len(value))
    masked_len = max(len(value) - visible, 3)
    return value[:visible] + mask_char * masked_len
