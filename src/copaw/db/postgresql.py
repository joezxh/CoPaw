# -*- coding: utf-8 -*-
"""
CoPaw Enterprise — PostgreSQL async connection manager.

Uses SQLAlchemy 2.0 async engine backed by asyncpg.
Alembic migrations are driven from this module's engine.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

logger = logging.getLogger(__name__)


def _build_dsn(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    ssl_mode: str = "prefer",
) -> str:
    """Construct an asyncpg DSN from explicit parts."""
    return (
        f"postgresql+asyncpg://{username}:{password}"
        f"@{host}:{port}/{database}"
    )


class DatabaseManager:
    """Singleton-style async PostgreSQL connection manager.

    Usage (inside FastAPI lifespan)::

        db = DatabaseManager()
        await db.initialize()
        app.state.db = db
        ...
        await db.close()
    """

    def __init__(self) -> None:
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    # ------------------------------------------------------------------ #
    # Initialisation / teardown
    # ------------------------------------------------------------------ #

    async def initialize(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
        username: str | None = None,
        password: str | None = None,
        pool_size: int = 20,
        max_overflow: int = 10,
        ssl_mode: str = "prefer",
    ) -> None:
        """Create the async engine and session factory.

        All parameters fall back to ``COPAW_DB_*`` environment variables so
        the manager works both from code and from docker-compose env vars.
        """
        host = host or os.environ.get("COPAW_DB_HOST", "localhost")
        port = int(port or os.environ.get("COPAW_DB_PORT", "5432"))
        database = database or os.environ.get(
            "COPAW_DB_NAME", "copaw_enterprise"
        )
        username = username or os.environ.get("COPAW_DB_USER", "copaw")
        password = password or os.environ.get("COPAW_DB_PASSWORD", "")

        dsn = _build_dsn(host, port, database, username, password, ssl_mode)

        logger.info(
            "Connecting to PostgreSQL at %s:%s/%s (pool=%s+%s)",
            host,
            port,
            database,
            pool_size,
            max_overflow,
        )

        self._engine = create_async_engine(
            dsn,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            echo=False,
        )

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        # Verify connectivity immediately so startup fails fast on bad config.
        await self.health_check(raise_on_failure=True)
        logger.info("✓ PostgreSQL connected successfully")

    async def close(self) -> None:
        """Dispose of the connection pool."""
        if self._engine:
            await self._engine.dispose()
            logger.info("PostgreSQL connection pool closed")

    # ------------------------------------------------------------------ #
    # Session factory
    # ------------------------------------------------------------------ #

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield a managed ``AsyncSession`` with automatic commit/rollback."""
        if self._session_factory is None:
            raise RuntimeError(
                "DatabaseManager not initialised — call initialize() first"
            )
        async with self._session_factory() as sess:
            try:
                yield sess
                await sess.commit()
            except Exception:
                await sess.rollback()
                raise

    # ------------------------------------------------------------------ #
    # Health check
    # ------------------------------------------------------------------ #

    async def health_check(self, raise_on_failure: bool = False) -> bool:
        """Execute a trivial SQL to verify DB connectivity."""
        if self._engine is None:
            return False
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.error("PostgreSQL health-check failed: %s", exc)
            if raise_on_failure:
                raise
            return False

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("DatabaseManager not initialised")
        return self._engine


# Module-level singleton — FastAPI lifespan will call initialize().
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Return the module-level singleton, creating it if needed."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an ``AsyncSession`` from the singleton."""
    manager = get_database_manager()
    async with manager.session() as sess:
        yield sess
