# -*- coding: utf-8 -*-
"""
Enterprise Alert Service — Redis-backed anomaly detection + multi-channel notify.

Supported channels:
- WeCom (企业微信) webhook
- DingTalk (钉钉) webhook
- SMTP email

Redis key schema:
  alert:login_fail:{user_id}:{ip}  → counter (TTL = window_seconds)
  alert:cooldown:{rule_type}:{target} → flag (TTL = cooldown_seconds, prevents spam)
"""
from __future__ import annotations

import asyncio
import logging
import os
import smtplib
import uuid
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ── Notify channel config (from env) ─────────────────────────────────────────
_WECOM_WEBHOOK = os.environ.get("COPAW_WECOM_WEBHOOK_URL", "")
_DINGTALK_WEBHOOK = os.environ.get("COPAW_DINGTALK_WEBHOOK_URL", "")
_SMTP_HOST = os.environ.get("COPAW_SMTP_HOST", "")
_SMTP_PORT = int(os.environ.get("COPAW_SMTP_PORT", "465"))
_SMTP_USER = os.environ.get("COPAW_SMTP_USER", "")
_SMTP_PASS = os.environ.get("COPAW_SMTP_PASSWORD", "")
_ALERT_EMAIL_TO = os.environ.get("COPAW_ALERT_EMAIL_TO", "")

_COOLDOWN_SECONDS = 300  # 5 min between repeat alerts for same key


# ── Low-level notifiers ───────────────────────────────────────────────────────

async def _send_wecom(message: str) -> None:
    if not _WECOM_WEBHOOK:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                _WECOM_WEBHOOK,
                json={"msgtype": "text", "text": {"content": f"[CoPaw Alert]\n{message}"}},
            )
    except Exception as exc:
        logger.warning("WeCom notify failed: %s", exc)


async def _send_dingtalk(message: str) -> None:
    if not _DINGTALK_WEBHOOK:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                _DINGTALK_WEBHOOK,
                json={
                    "msgtype": "text",
                    "text": {"content": f"[CoPaw Alert] {message}"},
                    "at": {"isAtAll": False},
                },
            )
    except Exception as exc:
        logger.warning("DingTalk notify failed: %s", exc)


def _send_email_sync(message: str) -> None:
    if not (_SMTP_HOST and _SMTP_USER and _ALERT_EMAIL_TO):
        return
    try:
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = "[CoPaw Security Alert]"
        msg["From"] = _SMTP_USER
        msg["To"] = _ALERT_EMAIL_TO
        with smtplib.SMTP_SSL(_SMTP_HOST, _SMTP_PORT) as server:
            server.login(_SMTP_USER, _SMTP_PASS)
            server.send_message(msg)
    except Exception as exc:
        logger.warning("Email notify failed: %s", exc)


async def notify(message: str) -> None:
    """Send alert to all configured channels (fire and forget)."""
    tasks = [_send_wecom(message), _send_dingtalk(message)]
    await asyncio.gather(*tasks, return_exceptions=True)
    # Email is sync — run in threadpool to avoid blocking
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _send_email_sync, message)


# ── AlertService ──────────────────────────────────────────────────────────────

class AlertService:

    @staticmethod
    async def check_login_anomaly(
        session: AsyncSession,
        username: str,
        ip: Optional[str],
        failed: bool,
        redis=None,
    ) -> None:
        """Track login failures. Load threshold from DB AlertRule, fallback to 3/5min.

        On threshold breach:
        1. Persist AlertEvent
        2. Send multi-channel notify (with cooldown to prevent spam)
        """
        if not failed:
            # Reset counter on successful login
            if redis and ip:
                await redis.delete(f"alert:login_fail:{username}:{ip}")
            return

        if not redis:
            logger.debug("No Redis — skipping login anomaly check")
            return

        counter_key = f"alert:login_fail:{username}:{ip or 'unknown'}"
        cooldown_key = f"alert:cooldown:login_fail:{username}"

        count = await redis.incr(counter_key)
        if count == 1:
            await redis.expire(counter_key, 300)  # 5-minute window

        # Load threshold from DB or use default 3
        threshold = await AlertService._get_threshold(session, "login_fail", default=3)

        if count >= threshold:
            # Cooldown check: don't spam if already alerted
            in_cooldown = await redis.get(cooldown_key)
            if not in_cooldown:
                await redis.set(cooldown_key, "1", ttl=_COOLDOWN_SECONDS)

                # Persist event
                await AlertService._persist_event(
                    session,
                    rule_type="login_fail",
                    context={
                        "username": username,
                        "ip": ip,
                        "failure_count": count,
                    },
                )

                msg = (
                    f"🚨 Login anomaly detected!\n"
                    f"User: {username}\n"
                    f"IP: {ip or 'unknown'}\n"
                    f"Consecutive failures: {count}\n"
                    f"Time: {datetime.now(timezone.utc).isoformat()}"
                )
                asyncio.create_task(notify(msg))
                logger.warning("Login anomaly: user=%s ip=%s count=%s", username, ip, count)

    @staticmethod
    async def check_permission_change(
        session: AsyncSession,
        actor_id: uuid.UUID,
        target_user_id: uuid.UUID,
        change_type: str,
        redis=None,
    ) -> None:
        """Alert on sensitive permission changes (role assign / revoke to admin roles)."""
        from ..db.models.alert import AlertEvent
        msg = (
            f"⚠️ Permission change!\n"
            f"Action: {change_type}\n"
            f"Actor: {actor_id}\n"
            f"Target user: {target_user_id}\n"
            f"Time: {datetime.now(timezone.utc).isoformat()}"
        )
        await AlertService._persist_event(
            session,
            rule_type="permission_change",
            context={
                "actor_id": str(actor_id),
                "target_user_id": str(target_user_id),
                "change_type": change_type,
            },
        )
        asyncio.create_task(notify(msg))

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    async def _get_threshold(
        session: AsyncSession, rule_type: str, default: int
    ) -> int:
        from ..db.models.alert import AlertRule
        rule = await session.scalar(
            select(AlertRule).where(
                AlertRule.rule_type == rule_type, AlertRule.is_active.is_(True)
            )
        )
        return rule.threshold if rule else default

    @staticmethod
    async def _persist_event(
        session: AsyncSession, rule_type: str, context: dict
    ) -> None:
        from ..db.models.alert import AlertEvent
        event = AlertEvent(
            rule_type=rule_type,
            triggered_at=datetime.now(timezone.utc),
            context=context,
        )
        session.add(event)
