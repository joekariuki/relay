"""Tests for the in-memory session store."""

from __future__ import annotations

import time

from src.session import SessionData, SessionStore


class TestSessionStore:
    def test_create_session_returns_id(self) -> None:
        store = SessionStore(ttl_minutes=30)
        sid = store.create_session("acc_001")
        assert isinstance(sid, str)
        assert len(sid) == 16

    def test_get_messages_returns_empty_list_for_new_session(self) -> None:
        store = SessionStore(ttl_minutes=30)
        sid = store.create_session("acc_001")
        msgs = store.get_messages(sid)
        assert msgs == []

    def test_get_messages_returns_none_for_unknown_session(self) -> None:
        store = SessionStore(ttl_minutes=30)
        assert store.get_messages("nonexistent") is None

    def test_update_messages_persists(self) -> None:
        store = SessionStore(ttl_minutes=30)
        sid = store.create_session("acc_001")
        store.update_messages(sid, ["msg1", "msg2"])  # type: ignore[arg-type]
        msgs = store.get_messages(sid)
        assert msgs == ["msg1", "msg2"]

    def test_update_messages_returns_false_for_unknown(self) -> None:
        store = SessionStore(ttl_minutes=30)
        assert store.update_messages("nonexistent", []) is False

    def test_delete_session_removes_it(self) -> None:
        store = SessionStore(ttl_minutes=30)
        sid = store.create_session("acc_001")
        assert store.delete_session(sid) is True
        assert store.get_messages(sid) is None

    def test_delete_session_returns_false_for_unknown(self) -> None:
        store = SessionStore(ttl_minutes=30)
        assert store.delete_session("nonexistent") is False

    def test_get_account_id(self) -> None:
        store = SessionStore(ttl_minutes=30)
        sid = store.create_session("acc_002")
        assert store.get_account_id(sid) == "acc_002"

    def test_get_account_id_returns_none_for_unknown(self) -> None:
        store = SessionStore(ttl_minutes=30)
        assert store.get_account_id("nonexistent") is None

    def test_active_session_count(self) -> None:
        store = SessionStore(ttl_minutes=30)
        assert store.active_session_count == 0
        store.create_session("acc_001")
        store.create_session("acc_002")
        assert store.active_session_count == 2

    def test_get_messages_returns_copy(self) -> None:
        """Verify that get_messages returns a copy, not a reference."""
        store = SessionStore(ttl_minutes=30)
        sid = store.create_session("acc_001")
        store.update_messages(sid, ["msg1"])  # type: ignore[arg-type]
        msgs = store.get_messages(sid)
        assert msgs is not None
        msgs.append("msg2")  # type: ignore[arg-type]
        assert store.get_messages(sid) == ["msg1"]


class TestSessionExpiry:
    def test_expired_session_returns_none(self) -> None:
        store = SessionStore(ttl_minutes=0)
        sid = store.create_session("acc_001")
        # TTL is 0 minutes = 0 seconds, so it's immediately expired
        time.sleep(0.01)
        assert store.get_messages(sid) is None

    def test_cleanup_removes_expired(self) -> None:
        store = SessionStore(ttl_minutes=0)
        store.create_session("acc_001")
        store.create_session("acc_002")
        time.sleep(0.01)
        removed = store.cleanup_expired()
        assert removed == 2
        assert store.active_session_count == 0

    def test_cleanup_keeps_active(self) -> None:
        store = SessionStore(ttl_minutes=30)
        store.create_session("acc_001")
        removed = store.cleanup_expired()
        assert removed == 0
        assert store.active_session_count == 1

    def test_update_refreshes_last_accessed(self) -> None:
        store = SessionStore(ttl_minutes=30)
        sid = store.create_session("acc_001")
        original_data = store._sessions[sid]
        original_time = original_data.last_accessed
        time.sleep(0.01)
        store.update_messages(sid, [])
        assert store._sessions[sid].last_accessed > original_time

    def test_get_refreshes_last_accessed(self) -> None:
        store = SessionStore(ttl_minutes=30)
        sid = store.create_session("acc_001")
        original_time = store._sessions[sid].last_accessed
        time.sleep(0.01)
        store.get_messages(sid)
        assert store._sessions[sid].last_accessed > original_time
