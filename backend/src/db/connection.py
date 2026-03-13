"""Asyncpg connection pool management and health checks."""

from __future__ import annotations

import logging
from pathlib import Path

import asyncpg

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def init_pool(database_url: str, *, min_size: int = 2, max_size: int = 10) -> asyncpg.Pool:
    """Create and cache the asyncpg connection pool.

    Also runs any pending SQL migrations on first init.
    """
    global _pool  # noqa: PLW0603
    if _pool is not None:
        return _pool

    _pool = await asyncpg.create_pool(
        database_url,
        min_size=min_size,
        max_size=max_size,
    )
    logger.info("PostgreSQL connection pool created (min=%d, max=%d)", min_size, max_size)

    await _run_migrations(_pool)
    return _pool


async def get_pool() -> asyncpg.Pool | None:
    """Return the cached connection pool, or None if not initialized."""
    return _pool


async def close_pool() -> None:
    """Close the connection pool gracefully."""
    global _pool  # noqa: PLW0603
    if _pool is not None:
        await _pool.close()
        logger.info("PostgreSQL connection pool closed")
        _pool = None


async def check_health() -> dict[str, object]:
    """Return PostgreSQL health status."""
    if _pool is None:
        return {"postgres": "not_configured"}

    try:
        async with _pool.acquire() as conn:
            row = await conn.fetchval("SELECT 1")
            return {
                "postgres": "ok",
                "pool_size": _pool.get_size(),
                "pool_free": _pool.get_idle_size(),
            }
    except Exception as e:
        logger.warning("PostgreSQL health check failed: %s", e)
        return {"postgres": "error", "detail": str(e)}


async def _run_migrations(pool: asyncpg.Pool) -> None:
    """Run SQL migration files in order."""
    migration_files = sorted(_MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        return

    async with pool.acquire() as conn:
        for migration_file in migration_files:
            sql = migration_file.read_text()
            try:
                await conn.execute(sql)
                logger.info("Applied migration: %s", migration_file.name)
            except Exception:
                logger.exception("Migration failed: %s", migration_file.name)
                raise
