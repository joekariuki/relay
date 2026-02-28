"""In-memory session store for conversation history with TTL expiry."""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from threading import Lock

from pydantic_ai.messages import ModelMessage

from src.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Holds conversation state for a single session."""

    account_id: str
    messages: list[ModelMessage] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)


class SessionStore:
    """Thread-safe in-memory session store with TTL-based expiry."""

    def __init__(self, ttl_minutes: int = 30, max_history: int = 20) -> None:
        self._sessions: dict[str, SessionData] = {}
        self._lock = Lock()
        self._ttl_seconds = ttl_minutes * 60
        self._max_history = max_history

    def create_session(self, account_id: str) -> str:
        """Create a new session and return its ID."""
        session_id = uuid.uuid4().hex[:16]
        with self._lock:
            self._sessions[session_id] = SessionData(account_id=account_id)
        logger.info("Session created: %s (account=%s)", session_id, account_id)
        return session_id

    def get_messages(self, session_id: str) -> list[ModelMessage] | None:
        """Return message history for a session, or None if expired/missing."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if self._is_expired(session):
                del self._sessions[session_id]
                logger.info("Session expired on access: %s", session_id)
                return None
            session.last_accessed = time.time()
            return list(session.messages)

    def update_messages(
        self, session_id: str, messages: list[ModelMessage]
    ) -> bool:
        """Replace the session's message history. Returns False if session is gone."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            if self._is_expired(session):
                del self._sessions[session_id]
                return False
            session.messages = messages
            session.last_accessed = time.time()
            return True

    def delete_session(self, session_id: str) -> bool:
        """Delete a session. Returns True if it existed."""
        with self._lock:
            removed = self._sessions.pop(session_id, None)
        if removed:
            logger.info("Session deleted: %s", session_id)
        return removed is not None

    def get_account_id(self, session_id: str) -> str | None:
        """Return the account_id for a session, or None if missing/expired."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or self._is_expired(session):
                return None
            return session.account_id

    def cleanup_expired(self) -> int:
        """Remove all expired sessions. Returns count of removed sessions."""
        now = time.time()
        removed = 0
        with self._lock:
            expired_ids = [
                sid
                for sid, data in self._sessions.items()
                if (now - data.last_accessed) > self._ttl_seconds
            ]
            for sid in expired_ids:
                del self._sessions[sid]
                removed += 1
        if removed:
            logger.info("Cleaned up %d expired sessions", removed)
        return removed

    @property
    def active_session_count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def _is_expired(self, session: SessionData) -> bool:
        return (time.time() - session.last_accessed) > self._ttl_seconds


_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    """Get the singleton session store instance."""
    global _store
    if _store is None:
        settings = get_settings()
        _store = SessionStore(
            ttl_minutes=settings.session_ttl_minutes,
            max_history=settings.session_max_history,
        )
    return _store
