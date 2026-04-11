# -*- coding: utf-8 -*-
"""
Enterprise DLP (Data Loss Prevention) Service.

Architecture:
- Built-in PII regex rules (Chinese ID, phone, bank card, email, IP)
- Admin-configurable rules stored in PostgreSQL (DLPRule)
- Events logged to DLPEvent table
- Three actions: mask | alert | block
- Stateless: inject DB session per call

Integration points:
- Called from EnterpriseAuthMiddleware response path
- Called from Agent response handler (future)
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


# ── Action types ─────────────────────────────────────────────────────────────

class DLPAction(str, Enum):
    MASK = "mask"
    ALERT = "alert"
    BLOCK = "block"


# ── Built-in PII patterns ─────────────────────────────────────────────────────

_BUILTIN_RULES: list[dict] = [
    {
        "name": "cn_id_card",
        "description": "Chinese National ID Card",
        "pattern": r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b",
        "action": DLPAction.MASK,
        "is_builtin": True,
    },
    {
        "name": "cn_phone",
        "description": "Chinese Mobile Phone Number",
        "pattern": r"\b1[3-9]\d{9}\b",
        "action": DLPAction.MASK,
        "is_builtin": True,
    },
    {
        "name": "bank_card",
        "description": "Bank Card Number (16-19 digits)",
        "pattern": r"\b(?:\d[ -]?){15,18}\d\b",
        "action": DLPAction.MASK,
        "is_builtin": True,
    },
    {
        "name": "email",
        "description": "Email Address",
        "pattern": r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
        "action": DLPAction.ALERT,
        "is_builtin": True,
    },
    {
        "name": "ipv4",
        "description": "IPv4 Address (non-private)",
        "pattern": r"\b(?:(?!10\.|172\.(?:1[6-9]|2\d|3[01])\.|192\.168\.)\d{1,3}\.){3}\d{1,3}\b",
        "action": DLPAction.ALERT,
        "is_builtin": True,
    },
    {
        "name": "api_key_like",
        "description": "API Key / Secret token pattern (sk-, pk-, Bearer)",
        "pattern": r"\b(?:sk|pk|api|secret|token|key)[-_][A-Za-z0-9]{16,}\b",
        "action": DLPAction.BLOCK,
        "is_builtin": True,
    },
]

# Pre-compiled for performance
_COMPILED_BUILTIN: list[dict] = [
    {**r, "compiled": re.compile(r["pattern"], re.IGNORECASE)}
    for r in _BUILTIN_RULES
]


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class DLPMatch:
    rule_name: str
    action: DLPAction
    matched_value: str
    start: int
    end: int


@dataclass
class DLPResult:
    original_text: str
    cleaned_text: str
    matches: list[DLPMatch] = field(default_factory=list)
    blocked: bool = False

    @property
    def has_violations(self) -> bool:
        return bool(self.matches)


# ── Core check function ───────────────────────────────────────────────────────

def check_text(
    text: str,
    extra_rules: list[dict] | None = None,
) -> DLPResult:
    """Run DLP check on plain text.

    Args:
        text: Input text to scan.
        extra_rules: Additional compiled rules from DB (same dict schema as _COMPILED_BUILTIN).

    Returns:
        DLPResult with cleaned text and match list.
    """
    all_rules = _COMPILED_BUILTIN + (extra_rules or [])
    matches: list[DLPMatch] = []
    blocked = False

    for rule in all_rules:
        action = DLPAction(rule["action"]) if isinstance(rule["action"], str) else rule["action"]
        compiled = rule.get("compiled") or re.compile(rule["pattern"], re.IGNORECASE)

        for m in compiled.finditer(text):
            matches.append(
                DLPMatch(
                    rule_name=rule["name"],
                    action=action,
                    matched_value=m.group(),
                    start=m.start(),
                    end=m.end(),
                )
            )
            if action == DLPAction.BLOCK:
                blocked = True

    # Apply masking (replace in reverse order to keep offsets stable)
    cleaned = text
    mask_matches = sorted(
        [m for m in matches if m.action == DLPAction.MASK],
        key=lambda x: x.start,
        reverse=True,
    )
    for mm in mask_matches:
        replacement = mm.matched_value[:3] + "*" * max(len(mm.matched_value) - 3, 3)
        cleaned = cleaned[: mm.start] + replacement + cleaned[mm.end :]

    return DLPResult(
        original_text=text,
        cleaned_text=cleaned,
        matches=matches,
        blocked=blocked,
    )


def mask_pii(text: str) -> str:
    """Quick helper — returns masked text, ignores blocking."""
    return check_text(text).cleaned_text


# ── DB-backed rule loader ─────────────────────────────────────────────────────

async def load_db_rules(session) -> list[dict]:
    """Load active custom rules from PostgreSQL and compile patterns."""
    from sqlalchemy import select
    from ..db.models.dlp import DLPRule

    rules = (
        await session.scalars(select(DLPRule).where(DLPRule.is_active.is_(True)))
    ).all()
    compiled = []
    for r in rules:
        try:
            compiled.append(
                {
                    "name": r.rule_name,
                    "description": r.description or "",
                    "pattern": r.pattern_regex,
                    "action": r.action,
                    "is_builtin": False,
                    "compiled": re.compile(r.pattern_regex, re.IGNORECASE),
                }
            )
        except re.error as exc:
            logger.warning("Invalid DLP rule pattern '%s': %s", r.rule_name, exc)
    return compiled


# ── Async check with DB rules ────────────────────────────────────────────────

async def check_text_with_db(text: str, session) -> DLPResult:
    """Full DLP check including DB-configured rules."""
    extra = await load_db_rules(session)
    return check_text(text, extra_rules=extra)


# ── Event logger ─────────────────────────────────────────────────────────────

async def log_dlp_event(
    session,
    result: DLPResult,
    user_id=None,
    context_path: Optional[str] = None,
) -> None:
    """Persist a DLP event for triggered violations."""
    if not result.has_violations:
        return

    from ..db.models.dlp import DLPEvent

    for match in result.matches:
        event = DLPEvent(
            rule_name=match.rule_name,
            action_taken=match.action.value,
            content_summary=f"[{match.rule_name}] ...{result.original_text[max(0, match.start-10):match.end+10]}...",
            user_id=user_id,
            context_path=context_path,
        )
        session.add(event)
