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


class AccountInfo(BaseModel):
    """A single account in the /accounts response."""

    id: str
    name: str
    country: str
    currency: str
    region: str


class AccountsResponse(BaseModel):
    """Response body for the /accounts endpoint."""

    accounts: list[AccountInfo]
    count: int


class HealthResponse(BaseModel):
    """Response body for the /health endpoint."""

    status: str
    version: str
    environment: str
    postgres: str | None = None


# --- WebSocket Voice Mode Schemas ---


class WSSessionStart(BaseModel):
    """Client->Server: initialize a voice mode session."""

    type: str = "session_start"
    account_id: str = "acc_001"
    language: str = "auto"
    session_id: str | None = None


class WSSessionEnd(BaseModel):
    """Client->Server: close a voice mode session."""

    type: str = "session_end"


class WSSessionStarted(BaseModel):
    """Server->Client: acknowledge voice mode session."""

    type: str = "session_started"
    session_id: str


class WSListening(BaseModel):
    """Server->Client: ready for speech input."""

    type: str = "listening"


class WSTranscriptPartial(BaseModel):
    """Server->Client: interim ASR transcript."""

    type: str = "transcript_partial"
    text: str


class WSTranscriptFinal(BaseModel):
    """Server->Client: final ASR transcript (utterance complete)."""

    type: str = "transcript_final"
    text: str


class WSAgentStatus(BaseModel):
    """Server->Client: agent tool execution status."""

    type: str = "agent_status"
    message: str


class WSAgentTextDelta(BaseModel):
    """Server->Client: streaming agent text chunk."""

    type: str = "agent_text_delta"
    chunk: str


class WSAudioChunk(BaseModel):
    """Server->Client: TTS audio chunk."""

    type: str = "audio_chunk"
    data: str


class WSTurnDone(BaseModel):
    """Server->Client: voice turn complete with metadata."""

    type: str = "turn_done"
    session_id: str
    language_detected: str
    tools_used: list[ToolCallInfo]
    groundedness_score: float | None = None
    latency_ms: dict[str, float]


class WSError(BaseModel):
    """Server->Client: error message."""

    type: str = "error"
    message: str
