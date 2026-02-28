"""FastAPI server exposing the agent, voice, and eval endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

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
    # Export API keys to os.environ so pydantic-ai providers can find them.
    # pydantic-settings reads .env into Settings but doesn't set os.environ.
    if settings.anthropic_api_key:
        os.environ.setdefault("ANTHROPIC_API_KEY", settings.anthropic_api_key)
    else:
        logger.warning("ANTHROPIC_API_KEY not set - agent may fail if using Anthropic models")
    if settings.openai_api_key:
        os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
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
    from src.session import get_session_store

    store = get_session_store()

    try:
        session_id = request.session_id
        message_history = None

        if session_id:
            message_history = store.get_messages(session_id)
            if message_history is None:
                session_id = store.create_session(request.account_id)
        else:
            session_id = store.create_session(request.account_id)

        result, all_messages = await process_message(
            message=request.message,
            account_id=request.account_id,
            language_hint=request.language,
            message_history=message_history,
        )

        store.update_messages(session_id, all_messages)

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
            session_id=session_id,
            language_detected=result.language_detected.value,
            tools_used=tools_info,
            groundedness_score=result.groundedness_score,
            latency_ms=result.latency_ms,
            metadata=result.metadata,
        )

    except Exception:
        logger.error("Chat endpoint failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Stream a chat response as Server-Sent Events."""
    from src.agent.core import StreamContext, process_message_stream
    from src.session import get_session_store

    store = get_session_store()

    session_id = request.session_id
    message_history = None

    if session_id:
        message_history = store.get_messages(session_id)
        if message_history is None:
            session_id = store.create_session(request.account_id)
    else:
        session_id = store.create_session(request.account_id)

    ctx = StreamContext()

    async def event_generator() -> AsyncIterator[str]:
        async for event in process_message_stream(
            message=request.message,
            account_id=request.account_id,
            language_hint=request.language,
            message_history=message_history,
            stream_context=ctx,
        ):
            # Inject session_id into the done event before yielding
            if event.startswith("event: done"):
                import json
                lines = event.strip().split("\n")
                data_line = lines[1]
                payload = json.loads(data_line.removeprefix("data: "))
                payload["session_id"] = session_id
                event = f"event: done\ndata: {json.dumps(payload)}\n\n"
            yield event
        if ctx.all_messages:
            store.update_messages(session_id, ctx.all_messages)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> JSONResponse:
    """Delete a conversation session."""
    from src.session import get_session_store

    store = get_session_store()
    deleted = store.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return JSONResponse({"status": "deleted", "session_id": session_id})


@app.post("/voice", response_model=VoiceResponse)
async def voice(
    audio: UploadFile = File(...),
    account_id: str = Form(default="acc_001"),
    enable_tts: bool = Form(default=True),
) -> VoiceResponse:
    """Process a voice message: ASR -> Agent -> optional TTS."""
    try:
        # Lazy import: voice pipeline is an optional dependency
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


@app.websocket("/ws/voice")
async def voice_stream(websocket: WebSocket) -> None:
    """Real-time voice mode over WebSocket.

    Protocol: client sends session_start JSON, then binary PCM audio frames.
    Server streams back transcript events, agent responses, and TTS audio.
    """
    from openai import AsyncOpenAI
    from src.agent.core import StreamContext, stream_agent_response
    from src.session import get_session_store
    from src.voice.realtime import VoiceSession, split_sentences, synthesize_sentence

    await websocket.accept()
    settings = get_settings()
    store = get_session_store()
    voice_session: VoiceSession | None = None

    try:
        init_data = await websocket.receive_json()
        if init_data.get("type") != "session_start":
            await websocket.send_json({"type": "error", "message": "Expected session_start message"})
            await websocket.close()
            return

        account_id = init_data.get("account_id", "acc_001")
        language = init_data.get("language", "auto")
        session_id = init_data.get("session_id")

        message_history = None
        if session_id:
            message_history = store.get_messages(session_id)
            if message_history is None:
                session_id = store.create_session(account_id)
        else:
            session_id = store.create_session(account_id)

        await websocket.send_json({"type": "session_started", "session_id": session_id})

        voice_session = VoiceSession(
            account_id=account_id,
            session_id=session_id,
            language=language if language != "auto" else "en",
        )
        await voice_session.connect_asr()
        await websocket.send_json({"type": "listening"})

        async def inbound_loop() -> None:
            """Read frames from the client: binary=audio, text=JSON control."""
            while True:
                msg = await websocket.receive()
                if msg.get("type") == "websocket.disconnect":
                    break
                if "bytes" in msg and msg["bytes"]:
                    await voice_session.send_audio(msg["bytes"])
                elif "text" in msg and msg["text"]:
                    data = json.loads(msg["text"])
                    if data.get("type") == "session_end":
                        break

        async def outbound_loop() -> None:
            """Poll Deepgram transcripts and drive the agent + TTS pipeline."""
            nonlocal message_history
            while True:
                event = await voice_session.get_transcript_event(timeout=0.1)
                if event is None:
                    continue

                if event["type"] == "transcript_partial":
                    await websocket.send_json({
                        "type": "transcript_partial",
                        "text": event["text"],
                    })

                elif event["type"] == "transcript_interim_final":
                    await websocket.send_json({
                        "type": "transcript_partial",
                        "text": event["text"],
                    })

                elif event["type"] == "utterance_end":
                    final_text = event["text"]
                    await websocket.send_json({
                        "type": "transcript_final",
                        "text": final_text,
                    })

                    t_start = time.perf_counter()
                    latency: dict[str, float] = {}

                    message_history = store.get_messages(session_id) or []
                    ctx = StreamContext()

                    accumulated_text = ""
                    tools_used: list[dict[str, object]] = []
                    language_detected = "en"

                    async for stream_event in stream_agent_response(
                        message=final_text,
                        account_id=account_id,
                        language_hint=language if language != "auto" else None,
                        message_history=message_history,
                        stream_context=ctx,
                    ):
                        if stream_event.type == "status":
                            await websocket.send_json({
                                "type": "agent_status",
                                "message": stream_event.data.get("message", ""),
                            })
                        elif stream_event.type == "text_delta":
                            chunk = str(stream_event.data.get("chunk", ""))
                            accumulated_text += chunk
                            await websocket.send_json({
                                "type": "agent_text_delta",
                                "chunk": chunk,
                            })
                        elif stream_event.type == "done":
                            language_detected = str(stream_event.data.get("language_detected", "en"))
                            tools_used = list(stream_event.data.get("tools_used", []))  # type: ignore[arg-type]
                            latency.update(stream_event.data.get("latency_ms", {}))  # type: ignore[arg-type]
                        elif stream_event.type == "error":
                            await websocket.send_json({
                                "type": "error",
                                "message": str(stream_event.data.get("message", "Agent error")),
                            })

                    if ctx.all_messages:
                        store.update_messages(session_id, ctx.all_messages)

                    latency["agent_processing_ms"] = (time.perf_counter() - t_start) * 1000

                    if accumulated_text and settings.openai_api_key:
                        t_tts = time.perf_counter()
                        openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
                        sentences = split_sentences(accumulated_text)
                        tts_first_chunk_sent = False

                        for sentence in sentences:
                            try:
                                tts_result = await synthesize_sentence(
                                    openai_client,
                                    sentence,
                                    language=language_detected,
                                    model=settings.voice_tts_model,
                                )
                                await websocket.send_json({
                                    "type": "audio_chunk",
                                    "data": tts_result["audio_base64"],
                                })
                                if not tts_first_chunk_sent:
                                    latency["tts_first_chunk_ms"] = (time.perf_counter() - t_tts) * 1000
                                    tts_first_chunk_sent = True
                            except Exception:
                                logger.warning("TTS synthesis failed for sentence", exc_info=True)

                        latency["tts_total_ms"] = (time.perf_counter() - t_tts) * 1000

                    latency["total_e2e_ms"] = (time.perf_counter() - t_start) * 1000

                    await websocket.send_json({
                        "type": "turn_done",
                        "session_id": session_id,
                        "language_detected": language_detected,
                        "tools_used": tools_used,
                        "groundedness_score": None,
                        "latency_ms": latency,
                    })
                    await websocket.send_json({"type": "listening"})

                elif event["type"] == "error":
                    await websocket.send_json({
                        "type": "error",
                        "message": event.get("text", "ASR error"),
                    })

        inbound_task = asyncio.create_task(inbound_loop())
        outbound_task = asyncio.create_task(outbound_loop())

        done, pending = await asyncio.wait(
            [inbound_task, outbound_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except WebSocketDisconnect:
        logger.info("Voice WebSocket disconnected (session=%s)", voice_session.session_id if voice_session else "unknown")
    except Exception:
        logger.error("Voice WebSocket error", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": "Internal server error"})
        except Exception:
            pass
    finally:
        if voice_session:
            await voice_session.close()


@app.post("/eval", response_model=EvalResponse)
async def run_eval(request: EvalRequest) -> EvalResponse:
    """Run the evaluation suite. Warning: this can take several minutes."""
    try:
        # Lazy import: eval harness is heavy and rarely called
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
