"""FastAPI server exposing the agent, voice, and eval endpoints."""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import configure_logging, get_settings

from .schemas import (
    ChatRequest,
    ChatResponse,
    EvalRequest,
    EvalResponse,
    HealthResponse,
    ToolCallInfo,
    VoiceResponse,
)

logger = logging.getLogger(__name__)

VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: validate config on startup."""
    configure_logging()
    settings = get_settings()
    logger.info(
        "Starting Relay backend v%s (env=%s)",
        VERSION,
        settings.environment,
    )
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY not set - agent may fail if using Anthropic models")
    yield
    logger.info("Shutting down Relay backend")


app = FastAPI(
    title="Relay - Mobile Money Support Agent",
    version=VERSION,
    lifespan=lifespan,
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        settings.frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Add a unique request ID to each request for tracing."""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=VERSION,
        environment=settings.environment,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a text message through the agent pipeline."""
    from src.agent.core import process_message

    try:
        result = await process_message(
            message=request.message,
            account_id=request.account_id,
            language_hint=request.language,
        )

        tools_info = [
            ToolCallInfo(
                tool_name=t.tool_name,
                arguments=t.arguments,
                result=t.result,
                duration_ms=t.duration_ms,
            )
            for t in result.tools_used
        ]

        return ChatResponse(
            response=result.response_text,
            language_detected=result.language_detected.value,
            tools_used=tools_info,
            groundedness_score=result.groundedness_score,
            latency_ms=result.latency_ms,
            metadata=result.metadata,
        )

    except Exception:
        logger.error("Chat endpoint failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/voice", response_model=VoiceResponse)
async def voice(
    audio: UploadFile = File(...),
    account_id: str = Form(default="acc_001"),
    enable_tts: bool = Form(default=True),
) -> VoiceResponse:
    """Process a voice message: ASR -> Agent -> optional TTS."""
    try:
        from src.voice.pipeline import process_voice

        audio_bytes = await audio.read()
        result = await process_voice(
            audio_bytes=audio_bytes,
            account_id=account_id,
            enable_tts=enable_tts,
        )

        tools_info = [
            ToolCallInfo(
                tool_name=t["tool_name"],
                arguments=t["arguments"],
                result=t["result"],
                duration_ms=t["duration_ms"],
            )
            for t in result.get("tools_used", [])
        ]

        return VoiceResponse(
            response=result["response"],
            transcript=result["transcript"],
            language_detected=result["language_detected"],
            tools_used=tools_info,
            latency_ms=result["latency_ms"],
            audio_base64=result.get("audio_base64"),
        )

    except ImportError:
        raise HTTPException(status_code=501, detail="Voice pipeline not available")
    except Exception:
        logger.error("Voice endpoint failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/eval", response_model=EvalResponse)
async def run_eval(request: EvalRequest) -> EvalResponse:
    """Run the evaluation suite. Warning: this can take several minutes."""
    try:
        from src.eval.harness import EvalHarness
        from src.eval.models import EvalCategory

        category = None
        if request.category:
            try:
                category = EvalCategory(request.category)
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid category: {request.category}",
                )

        harness = EvalHarness(concurrency=5)
        report = await harness.run(
            category=category,
            max_cases=request.max_cases,
        )

        return EvalResponse(
            total_cases=report.total_cases,
            passed_cases=report.passed_cases,
            failed_cases=report.failed_cases,
            error_cases=report.error_cases,
            overall_scores=report.overall_scores,
            by_category=report.by_category,
        )

    except HTTPException:
        raise
    except Exception:
        logger.error("Eval endpoint failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
