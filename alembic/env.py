# -*- coding: utf-8 -*-
"""
Alembic migration environment for CoPaw Enterprise.

Builds the PostgreSQL URL from COPAW_DB_* environment variables so that
the same alembic.ini works identically in Docker Compose and local dev.

Run migrations::

    # inside the container or venv
    alembic upgrade head

    # generate a new migration
    alembic revision --autogenerate -m "describe_your_change"
"""
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Make sure the CoPaw package is importable ──────────────────────────────
# When alembic runs from the project root, src/ must be on the path.
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
for candidate in [PROJECT_ROOT / "src", PROJECT_ROOT]:
    p = str(candidate)
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Import all ORM models so Alembic detects them ─────────────────────────
from copaw.db.models import Base  # noqa: E402 — after sys.path manipulation

# ── Alembic Config ─────────────────────────────────────────────────────────
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ── Build DSN from env vars ────────────────────────────────────────────────

def _get_dsn() -> str:
    host = os.environ.get("COPAW_DB_HOST", "localhost")
    port = os.environ.get("COPAW_DB_PORT", "5432")
    name = os.environ.get("COPAW_DB_NAME", "copaw_enterprise")
    user = os.environ.get("COPAW_DB_USER", "copaw")
    pw = os.environ.get("COPAW_DB_PASSWORD", "")
    # Use psycopg2 for sync alembic migrations (asyncpg is async-only)
    return f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{name}"


def run_migrations_offline() -> None:
    """Generate SQL without a live DB connection (useful for review)."""
    url = _get_dsn()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations against a live DB connection."""
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = _get_dsn()

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
