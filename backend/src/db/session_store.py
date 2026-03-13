"""PostgreSQL-backed session store with the same interface as the in-memory store."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

import asyncpg
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from .connection import get_pool

logger = logging.getLogger(__name__)


class PostgresSessionStore:
    """Async session store backed by PostgreSQL.

    Mirrors the SessionStore interface but uses async methods and asyncpg.
    Messages are serialized to JSONB via pydantic-ai's ModelMessagesTypeAdapter.
    """

    def __init__(self, ttl_minutes: int = 30, max_history: int = 20) -> None:
        self._ttl_minutes = ttl_minutes
        self._max_history = max_history

    async def _get_pool(self) -> asyncpg.Pool:
        pool = await get_pool()
        if pool is None:
            raise RuntimeError("PostgreSQL pool not initialized")
        return pool

    async def create_session(self, account_id: str) -> str:
        """Create a new session and return its ID."""
        pool = await self._get_pool()
        session_id = uuid.uuid4().hex[:16]
        now = datetime.now(timezone.utc)

        await pool.execute(
            """
            INSERT INTO sessions (id, account_id, messages, created_at, last_accessed)
            VALUES ($1, $2, '[]'::jsonb, $3, $3)
            """,
            session_id,
            account_id,
            now,
        )
        logger.info("Session created: %s (account=%s)", session_id, account_id)
        return session_id

    async def get_messages(self, session_id: str) -> list[ModelMessage] | None:
        """Return message history for a session, or None if expired/missing."""
        pool = await self._get_pool()
        row = await pool.fetchrow(
            "SELECT messages, last_accessed FROM sessions WHERE id = $1",
            session_id,
        )

        if row is None:
            return None

        if self._is_expired(row["last_accessed"]):
            await pool.execute("DELETE FROM sessions WHERE id = $1", session_id)
            logger.info("Session expired on access: %s", session_id)
            return None

        # Touch last_accessed
        await pool.execute(
            "UPDATE sessions SET last_accessed = now() WHERE id = $1",
            session_id,
        )

        return _deserialize_messages(row["messages"])

    async def update_messages(
        self, session_id: str, messages: list[ModelMessage]
    ) -> bool:
        """Replace the session's message history. Returns False if session is gone."""
        pool = await self._get_pool()

        # Trim to max history
        trimmed = messages[-self._max_history :] if len(messages) > self._max_history else messages
        serialized = _serialize_messages(trimmed)

        result = await pool.execute(
            """
            UPDATE sessions
            SET messages = $2::jsonb, last_accessed = now()
            WHERE id = $1
              AND last_accessed > now() - make_interval(mins => $3)
            """,
            session_id,
            serialized,
            self._ttl_minutes,
        )

        # asyncpg returns "UPDATE N" where N is rows affected
        return result == "UPDATE 1"

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session. Returns True if it existed."""
        pool = await self._get_pool()
        result = await pool.execute(
            "DELETE FROM sessions WHERE id = $1",
            session_id,
        )
        deleted = result == "DELETE 1"
        if deleted:
            logger.info("Session deleted: %s", session_id)
        return deleted

    async def get_account_id(self, session_id: str) -> str | None:
        """Return the account_id for a session, or None if missing/expired."""
        pool = await self._get_pool()
        row = await pool.fetchrow(
            "SELECT account_id, last_accessed FROM sessions WHERE id = $1",
            session_id,
        )

        if row is None:
            return None

        if self._is_expired(row["last_accessed"]):
            return None

        return row["account_id"]

    async def cleanup_expired(self) -> int:
        """Remove all expired sessions. Returns count of removed sessions."""
        pool = await self._get_pool()
        result = await pool.execute(
            "DELETE FROM sessions WHERE last_accessed < now() - make_interval(mins => $1)",
            self._ttl_minutes,
        )
        # Parse "DELETE N"
        removed = int(result.split()[-1])
        if removed:
            logger.info("Cleaned up %d expired sessions", removed)
        return removed

    @property
    async def active_session_count(self) -> int:
        """Count non-expired sessions."""
        pool = await self._get_pool()
        count = await pool.fetchval(
            "SELECT COUNT(*) FROM sessions WHERE last_accessed > now() - make_interval(mins => $1)",
            self._ttl_minutes,
        )
        return count or 0

    def _is_expired(self, last_accessed: datetime) -> bool:
        now = datetime.now(timezone.utc)
        if last_accessed.tzinfo is None:
            last_accessed = last_accessed.replace(tzinfo=timezone.utc)
        elapsed_minutes = (now - last_accessed).total_seconds() / 60
        return elapsed_minutes > self._ttl_minutes


def _serialize_messages(messages: list[ModelMessage]) -> str:
    """Serialize pydantic-ai messages to JSON string for JSONB storage."""
    return ModelMessagesTypeAdapter.dump_json(messages).decode()


def _deserialize_messages(data: str | list | dict) -> list[ModelMessage]:
    """Deserialize messages from JSONB (asyncpg returns parsed JSON)."""
    if isinstance(data, str):
        return list(ModelMessagesTypeAdapter.validate_json(data))
    # asyncpg auto-parses JSONB to Python objects
    json_str = json.dumps(data)
    return list(ModelMessagesTypeAdapter.validate_json(json_str))
