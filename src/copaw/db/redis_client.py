# -*- coding: utf-8 -*-
"""
CoPaw Enterprise — Redis async connection manager.

Uses redis-py ≥ 5.0 with hiredis for high-throughput parsing.
Provides typed helpers for common patterns: cache get/set, pub/sub,
distributed locks, and session storage.
"""
from __future__ import annotations

import logging
import os
from typing import Any, AsyncIterator, Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

logger = logging.getLogger(__name__)


class RedisManager:
    """Async Redis connection manager (singleton pattern).

    Usage (inside FastAPI lifespan)::

        redis_mgr = RedisManager()
        await redis_mgr.initialize()
        app.state.redis = redis_mgr
        ...
        await redis_mgr.close()
    """

    def __init__(self) -> None:
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
        self._key_prefix: str = "copaw:"

    # ------------------------------------------------------------------ #
    # Initialisation
    # ------------------------------------------------------------------ #

    async def initialize(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int | None = None,
        password: str | None = None,
        max_connections: int = 50,
        key_prefix: str = "copaw:",
    ) -> None:
        """Create connection pool and verify connectivity."""
        host = host or os.environ.get("COPAW_REDIS_HOST", "localhost")
        port = int(port or os.environ.get("COPAW_REDIS_PORT", "6379"))
        db = int(db if db is not None else os.environ.get("COPAW_REDIS_DB", "0"))
        password = password or os.environ.get("COPAW_REDIS_PASSWORD") or None
        self._key_prefix = key_prefix

        logger.info(
            "Connecting to Redis at %s:%s db=%s (max_conn=%s)",
            host,
            port,
            db,
            max_connections,
        )

        self._pool = aioredis.ConnectionPool.from_url(
            f"redis://{host}:{port}/{db}",
            password=password,
            max_connections=max_connections,
            decode_responses=True,
        )
        self._client = aioredis.Redis(connection_pool=self._pool)

        # Verify connectivity
        await self.health_check(raise_on_failure=True)
        logger.info("✓ Redis connected successfully")

    async def close(self) -> None:
        """Close the connection pool."""
        if self._client:
            await self._client.aclose()
        if self._pool:
            await self._pool.aclose()
        logger.info("Redis connection pool closed")

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _k(self, key: str) -> str:
        """Prepend the namespace prefix to a key."""
        if key.startswith(self._key_prefix):
            return key
        return f"{self._key_prefix}{key}"

    @property
    def client(self) -> Redis:
        if self._client is None:
            raise RuntimeError(
                "RedisManager not initialised — call initialize() first"
            )
        return self._client

    # ------------------------------------------------------------------ #
    # Cache helpers
    # ------------------------------------------------------------------ #

    async def get(self, key: str) -> Optional[str]:
        """Return a string value or ``None`` if the key doesn't exist."""
        return await self.client.get(self._k(key))

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set a value (stringified via redis-py) with optional TTL in seconds."""
        if ttl:
            await self.client.setex(self._k(key), ttl, str(value))
        else:
            await self.client.set(self._k(key), str(value))

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys, returns number of deleted keys."""
        return await self.client.delete(*[self._k(k) for k in keys])

    async def exists(self, key: str) -> bool:
        return bool(await self.client.exists(self._k(key)))

    async def expire(self, key: str, ttl: int) -> None:
        await self.client.expire(self._k(key), ttl)

    async def incr(self, key: str) -> int:
        return await self.client.incr(self._k(key))

    # ------------------------------------------------------------------ #
    # Hash helpers (used for session storage)
    # ------------------------------------------------------------------ #

    async def hset(self, key: str, mapping: dict) -> None:
        await self.client.hset(self._k(key), mapping=mapping)

    async def hgetall(self, key: str) -> dict:
        return await self.client.hgetall(self._k(key))

    async def hdel(self, key: str, *fields: str) -> None:
        await self.client.hdel(self._k(key), *fields)

    # ------------------------------------------------------------------ #
    # Pub/Sub
    # ------------------------------------------------------------------ #

    async def publish(self, channel: str, message: str) -> None:
        await self.client.publish(self._k(channel), message)

    async def subscribe(self, channel: str) -> AsyncIterator[str]:
        """Async generator that yields messages from a channel."""
        pubsub = self.client.pubsub()
        await pubsub.subscribe(self._k(channel))
        try:
            async for raw in pubsub.listen():
                if raw["type"] == "message":
                    yield raw["data"]
        finally:
            await pubsub.unsubscribe(self._k(channel))
            await pubsub.aclose()

    # ------------------------------------------------------------------ #
    # Distributed lock
    # ------------------------------------------------------------------ #

    async def acquire_lock(
        self,
        lock_name: str,
        ttl: int = 30,
    ) -> bool:
        """Try to acquire a simple Redis-based lock.

        Returns ``True`` if acquired, ``False`` otherwise.
        """
        result = await self.client.set(
            self._k(f"lock:{lock_name}"),
            "1",
            nx=True,
            ex=ttl,
        )
        return result is True

    async def release_lock(self, lock_name: str) -> None:
        await self.delete(f"lock:{lock_name}")

    # ------------------------------------------------------------------ #
    # Health check
    # ------------------------------------------------------------------ #

    async def health_check(self, raise_on_failure: bool = False) -> bool:
        try:
            result = await self.client.ping()
            return bool(result)
        except Exception as exc:
            logger.error("Redis health-check failed: %s", exc)
            if raise_on_failure:
                raise
            return False


# Module-level singleton
_redis_manager: Optional[RedisManager] = None


def get_redis_manager() -> RedisManager:
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager()
    return _redis_manager
