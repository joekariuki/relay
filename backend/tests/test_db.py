"""Tests for PostgreSQL persistence layer.

Tests use mocked asyncpg pool — no real database required.
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from src.db.connection import _run_migrations, check_health, close_pool, init_pool
from src.db.session_store import (
    PostgresSessionStore,
    _deserialize_messages,
    _serialize_messages,
)


def _make_pool_with_conn(mock_conn: AsyncMock) -> AsyncMock:
    """Create a mock asyncpg pool whose acquire() returns a proper async context manager."""
    mock_pool = AsyncMock()

    @asynccontextmanager
    async def _acquire():
        yield mock_conn

    mock_pool.acquire = _acquire
    return mock_pool


# === Message Serialization Tests ===


class TestMessageSerialization:
    """Test pydantic-ai message serialization/deserialization for JSONB storage."""

    def test_serialize_empty_list(self) -> None:
        result = _serialize_messages([])
        assert result == "[]"

    def test_roundtrip_user_message(self) -> None:
        messages = [
            ModelRequest(parts=[UserPromptPart(content="Hello")]),
        ]
        serialized = _serialize_messages(messages)
        deserialized = _deserialize_messages(serialized)

        assert len(deserialized) == 1
        assert isinstance(deserialized[0], ModelRequest)

    def test_roundtrip_model_response(self) -> None:
        messages = [
            ModelRequest(parts=[UserPromptPart(content="Hi")]),
            ModelResponse(parts=[TextPart(content="Hello! How can I help?")]),
        ]
        serialized = _serialize_messages(messages)
        deserialized = _deserialize_messages(serialized)

        assert len(deserialized) == 2
        assert isinstance(deserialized[0], ModelRequest)
        assert isinstance(deserialized[1], ModelResponse)

    def test_deserialize_from_python_objects(self) -> None:
        """asyncpg auto-parses JSONB to Python objects, not strings."""
        messages = [
            ModelRequest(parts=[UserPromptPart(content="Test")]),
        ]
        serialized = _serialize_messages(messages)
        # Simulate asyncpg JSONB auto-parse
        python_objects = json.loads(serialized)
        deserialized = _deserialize_messages(python_objects)

        assert len(deserialized) == 1
        assert isinstance(deserialized[0], ModelRequest)

    def test_serialize_produces_valid_json(self) -> None:
        messages = [
            ModelRequest(parts=[UserPromptPart(content="Bonjour")]),
            ModelResponse(parts=[TextPart(content="Salut!")]),
        ]
        serialized = _serialize_messages(messages)
        parsed = json.loads(serialized)
        assert isinstance(parsed, list)
        assert len(parsed) == 2


# === Connection Pool Tests ===


class TestConnectionPool:
    """Test asyncpg pool management."""

    @pytest.mark.asyncio
    @patch("src.db.connection.asyncpg")
    async def test_init_pool_creates_pool(self, mock_asyncpg: MagicMock) -> None:
        import src.db.connection as conn_mod

        original_pool = conn_mod._pool
        conn_mod._pool = None

        try:
            mock_conn = AsyncMock()
            mock_pool = _make_pool_with_conn(mock_conn)
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)

            pool = await init_pool("postgresql://test:test@localhost/test")

            assert pool is mock_pool
            mock_asyncpg.create_pool.assert_awaited_once()
        finally:
            conn_mod._pool = original_pool

    @pytest.mark.asyncio
    @patch("src.db.connection.asyncpg")
    async def test_init_pool_is_idempotent(self, mock_asyncpg: MagicMock) -> None:
        import src.db.connection as conn_mod

        original_pool = conn_mod._pool
        mock_existing_pool = AsyncMock()
        conn_mod._pool = mock_existing_pool

        try:
            pool = await init_pool("postgresql://test:test@localhost/test")
            assert pool is mock_existing_pool
            mock_asyncpg.create_pool.assert_not_called()
        finally:
            conn_mod._pool = original_pool

    @pytest.mark.asyncio
    async def test_close_pool_when_none(self) -> None:
        import src.db.connection as conn_mod

        original_pool = conn_mod._pool
        conn_mod._pool = None
        try:
            await close_pool()  # Should not raise
        finally:
            conn_mod._pool = original_pool

    @pytest.mark.asyncio
    async def test_close_pool_closes_and_clears(self) -> None:
        import src.db.connection as conn_mod

        original_pool = conn_mod._pool
        mock_pool = AsyncMock()
        conn_mod._pool = mock_pool
        try:
            await close_pool()
            mock_pool.close.assert_awaited_once()
            assert conn_mod._pool is None
        finally:
            conn_mod._pool = original_pool


# === Health Check Tests ===


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_when_no_pool(self) -> None:
        import src.db.connection as conn_mod

        original_pool = conn_mod._pool
        conn_mod._pool = None
        try:
            result = await check_health()
            assert result["postgres"] == "not_configured"
        finally:
            conn_mod._pool = original_pool

    @pytest.mark.asyncio
    async def test_health_when_pool_healthy(self) -> None:
        import src.db.connection as conn_mod

        original_pool = conn_mod._pool
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        mock_pool = _make_pool_with_conn(mock_conn)
        mock_pool.get_size = MagicMock(return_value=5)
        mock_pool.get_idle_size = MagicMock(return_value=3)

        conn_mod._pool = mock_pool
        try:
            result = await check_health()
            assert result["postgres"] == "ok"
            assert result["pool_size"] == 5
            assert result["pool_free"] == 3
        finally:
            conn_mod._pool = original_pool

    @pytest.mark.asyncio
    async def test_health_when_pool_error(self) -> None:
        import src.db.connection as conn_mod

        original_pool = conn_mod._pool

        mock_pool = AsyncMock()
        # Make acquire itself raise, not return a coroutine
        mock_pool.acquire = MagicMock(side_effect=Exception("Connection refused"))

        conn_mod._pool = mock_pool
        try:
            result = await check_health()
            assert result["postgres"] == "error"
            assert "Connection refused" in str(result["detail"])
        finally:
            conn_mod._pool = original_pool


# === PostgresSessionStore Tests ===


class TestPostgresSessionStore:
    """Test PostgresSessionStore with mocked pool."""

    def _mock_pool(self) -> AsyncMock:
        pool = AsyncMock()
        return pool

    @pytest.mark.asyncio
    async def test_create_session(self) -> None:
        store = PostgresSessionStore(ttl_minutes=30)
        mock_pool = self._mock_pool()

        with patch("src.db.session_store.get_pool", return_value=mock_pool):
            session_id = await store.create_session("acc_001")

        assert len(session_id) == 16
        mock_pool.execute.assert_awaited_once()
        call_args = mock_pool.execute.call_args
        assert "INSERT INTO sessions" in call_args[0][0]
        assert call_args[0][2] == "acc_001"

    @pytest.mark.asyncio
    async def test_get_messages_returns_none_for_missing(self) -> None:
        store = PostgresSessionStore(ttl_minutes=30)
        mock_pool = self._mock_pool()
        mock_pool.fetchrow.return_value = None

        with patch("src.db.session_store.get_pool", return_value=mock_pool):
            result = await store.get_messages("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_messages_returns_none_for_expired(self) -> None:
        store = PostgresSessionStore(ttl_minutes=30)
        mock_pool = self._mock_pool()

        # Atomic UPDATE...RETURNING returns None for expired sessions
        # (WHERE clause filters them out), then DELETE cleans up
        mock_pool.fetchrow.return_value = None
        mock_pool.execute.return_value = "DELETE 1"

        with patch("src.db.session_store.get_pool", return_value=mock_pool):
            result = await store.get_messages("expired_session")

        assert result is None
        # Should have attempted cleanup of expired session
        mock_pool.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_messages_returns_messages(self) -> None:
        store = PostgresSessionStore(ttl_minutes=30)
        mock_pool = self._mock_pool()

        messages = [ModelRequest(parts=[UserPromptPart(content="Hello")])]
        serialized = json.loads(_serialize_messages(messages))

        recent_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        mock_pool.fetchrow.return_value = {
            "messages": serialized,
            "last_accessed": recent_time,
        }

        with patch("src.db.session_store.get_pool", return_value=mock_pool):
            result = await store.get_messages("valid_session")

        assert result is not None
        assert len(result) == 1
        assert isinstance(result[0], ModelRequest)

    @pytest.mark.asyncio
    async def test_update_messages_returns_true_on_success(self) -> None:
        store = PostgresSessionStore(ttl_minutes=30)
        mock_pool = self._mock_pool()
        mock_pool.execute.return_value = "UPDATE 1"

        messages = [ModelRequest(parts=[UserPromptPart(content="Hi")])]

        with patch("src.db.session_store.get_pool", return_value=mock_pool):
            result = await store.update_messages("session_id", messages)

        assert result is True

    @pytest.mark.asyncio
    async def test_update_messages_returns_false_for_missing(self) -> None:
        store = PostgresSessionStore(ttl_minutes=30)
        mock_pool = self._mock_pool()
        mock_pool.execute.return_value = "UPDATE 0"

        with patch("src.db.session_store.get_pool", return_value=mock_pool):
            result = await store.update_messages("missing", [])

        assert result is False

    @pytest.mark.asyncio
    async def test_update_messages_trims_history(self) -> None:
        store = PostgresSessionStore(ttl_minutes=30, max_history=5)
        mock_pool = self._mock_pool()
        mock_pool.execute.return_value = "UPDATE 1"

        # Create 10 messages
        messages = [
            ModelRequest(parts=[UserPromptPart(content=f"Message {i}")])
            for i in range(10)
        ]

        with patch("src.db.session_store.get_pool", return_value=mock_pool):
            await store.update_messages("session_id", messages)

        # Verify the serialized data contains only the last 5 messages
        call_args = mock_pool.execute.call_args
        serialized = call_args[0][2]
        parsed = json.loads(serialized)
        assert len(parsed) == 5

    @pytest.mark.asyncio
    async def test_delete_session_returns_true(self) -> None:
        store = PostgresSessionStore(ttl_minutes=30)
        mock_pool = self._mock_pool()
        mock_pool.execute.return_value = "DELETE 1"

        with patch("src.db.session_store.get_pool", return_value=mock_pool):
            result = await store.delete_session("session_id")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_session_returns_false_for_missing(self) -> None:
        store = PostgresSessionStore(ttl_minutes=30)
        mock_pool = self._mock_pool()
        mock_pool.execute.return_value = "DELETE 0"

        with patch("src.db.session_store.get_pool", return_value=mock_pool):
            result = await store.delete_session("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_account_id_returns_id(self) -> None:
        store = PostgresSessionStore(ttl_minutes=30)
        mock_pool = self._mock_pool()

        recent_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        mock_pool.fetchrow.return_value = {
            "account_id": "acc_001",
            "last_accessed": recent_time,
        }

        with patch("src.db.session_store.get_pool", return_value=mock_pool):
            result = await store.get_account_id("session_id")

        assert result == "acc_001"

    @pytest.mark.asyncio
    async def test_get_account_id_returns_none_for_expired(self) -> None:
        store = PostgresSessionStore(ttl_minutes=30)
        mock_pool = self._mock_pool()

        old_time = datetime.now(timezone.utc) - timedelta(minutes=60)
        mock_pool.fetchrow.return_value = {
            "account_id": "acc_001",
            "last_accessed": old_time,
        }

        with patch("src.db.session_store.get_pool", return_value=mock_pool):
            result = await store.get_account_id("expired")

        assert result is None

    @pytest.mark.asyncio
    async def test_cleanup_expired(self) -> None:
        store = PostgresSessionStore(ttl_minutes=30)
        mock_pool = self._mock_pool()
        mock_pool.execute.return_value = "DELETE 3"

        with patch("src.db.session_store.get_pool", return_value=mock_pool):
            removed = await store.cleanup_expired()

        assert removed == 3

    @pytest.mark.asyncio
    async def test_active_session_count(self) -> None:
        store = PostgresSessionStore(ttl_minutes=30)
        mock_pool = self._mock_pool()
        mock_pool.fetchval.return_value = 7

        with patch("src.db.session_store.get_pool", return_value=mock_pool):
            count = await store.active_session_count

        assert count == 7

    @pytest.mark.asyncio
    async def test_pool_not_initialized_raises(self) -> None:
        store = PostgresSessionStore(ttl_minutes=30)

        with patch("src.db.session_store.get_pool", return_value=None):
            with pytest.raises(RuntimeError, match="PostgreSQL pool not initialized"):
                await store.create_session("acc_001")


# === Config Tests ===


class TestPostgresConfig:
    def test_defaults(self) -> None:
        from src.config import Settings

        s = Settings(anthropic_api_key="test")
        assert s.use_postgres is False
        assert s.database_url is None

    def test_enabled(self) -> None:
        from src.config import Settings

        s = Settings(
            anthropic_api_key="test",
            use_postgres=True,
            database_url="postgresql://localhost/relay",
        )
        assert s.use_postgres is True
        assert s.database_url == "postgresql://localhost/relay"


# === Migration Tests ===


class TestMigrations:
    @pytest.mark.asyncio
    async def test_run_migrations_executes_sql(self) -> None:
        mock_conn = AsyncMock()
        mock_pool = _make_pool_with_conn(mock_conn)

        await _run_migrations(mock_pool)

        # Should have executed at least the 001_initial.sql
        assert mock_conn.execute.await_count >= 1
        # Verify the SQL contains CREATE TABLE
        first_call = mock_conn.execute.call_args_list[0]
        assert "CREATE TABLE" in first_call[0][0]
