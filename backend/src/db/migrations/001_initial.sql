-- Initial schema for Relay session persistence.
--
-- Stores conversation sessions with pydantic-ai message history as JSONB.
-- Messages are stored as a single JSONB array per session rather than
-- a separate table — simpler for a demo and avoids N+1 on every chat turn.

CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT PRIMARY KEY,
    account_id      TEXT NOT NULL,
    messages        JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_accessed   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for TTL cleanup queries
CREATE INDEX IF NOT EXISTS idx_sessions_last_accessed ON sessions (last_accessed);

-- Index for account lookups
CREATE INDEX IF NOT EXISTS idx_sessions_account_id ON sessions (account_id);
