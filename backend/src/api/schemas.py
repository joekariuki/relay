"""Pydantic request/response schemas for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for the /chat and /chat/stream endpoints."""

    message: str = Field(..., min_length=1, max_length=2000, description="User message text")
    account_id: str = Field(default="acc_001", description="DuniaWallet account ID")
    language: str | None = Field(
        default=None,
        pattern=r"^(en|fr|sw)$",
        description="Language hint (en, fr, sw). Auto-detected if not provided.",
    )
    session_id: str | None = Field(
        default=None,
        description="Session ID for conversation continuity. Auto-created if not provided.",
    )


class ToolCallInfo(BaseModel):
    """Information about a tool call made during processing."""

    tool_name: str
    arguments: dict[str, object]
    result: dict[str, object]
    duration_ms: float


class ChatResponse(BaseModel):
    """Response body for the /chat endpoint."""

    response: str
    session_id: str
    language_detected: str
    tools_used: list[ToolCallInfo]
    groundedness_score: float | None = None
    latency_ms: dict[str, float]
    metadata: dict[str, object] = Field(default_factory=dict)


class VoiceResponse(BaseModel):
    """Response body for the /voice endpoint."""

    response: str
    transcript: str
    language_detected: str
    tools_used: list[ToolCallInfo]
    latency_ms: dict[str, float]
    audio_base64: str | None = None


class EvalRequest(BaseModel):
    """Request body for the /eval endpoint."""

    category: str | None = Field(default=None, description="Filter by eval category")
    max_cases: int | None = Field(default=None, ge=1, le=200, description="Max test cases to run")


class EvalScores(BaseModel):
    """Overall evaluation scores."""

    tool_correctness: float | None = None
    groundedness: float | None = None
    compliance_rate: float | None = None
    hallucination_free_rate: float | None = None
    language_correctness: float | None = None


class EvalResponse(BaseModel):
    """Response body for the /eval endpoint."""

    total_cases: int
    passed_cases: int
    failed_cases: int
    error_cases: int
    overall_scores: dict[str, float]
    by_category: dict[str, dict[str, float]]


class HealthResponse(BaseModel):
    """Response body for the /health endpoint."""

    status: str
    version: str
    environment: str
