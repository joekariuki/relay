"""Voice pipeline: Whisper ASR -> Agent -> OpenAI TTS.

Handles speech-to-text, routes through the agent, and optionally
synthesizes speech output. Tracks latency at every stage.
"""

from __future__ import annotations

import base64
import io
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# Voice selection per language
_VOICE_MAP: dict[str, str] = {
    "en": "alloy",
    "fr": "nova",
    "sw": "echo",
}


async def transcribe_audio(
    client: Any,
    audio_bytes: bytes,
    filename: str = "audio.webm",
) -> dict[str, Any]:
    """Transcribe audio bytes using OpenAI Whisper API.

    Args:
        client: OpenAI AsyncOpenAI client.
        audio_bytes: Raw audio bytes (webm/opus, mp3, wav, etc.).
        filename: Filename hint for the API.

    Returns:
        Dict with transcript, detected_language, and duration_ms.
    """
    start = time.perf_counter()

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    response = await client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",
    )

    duration_ms = (time.perf_counter() - start) * 1000

    return {
        "transcript": response.text,
        "detected_language": getattr(response, "language", "en"),
        "duration_ms": duration_ms,
    }


async def synthesize_speech(
    client: Any,
    text: str,
    language: str = "en",
) -> dict[str, Any]:
    """Synthesize speech from text using OpenAI TTS API.

    Args:
        client: OpenAI AsyncOpenAI client.
        text: Text to synthesize.
        language: Language code for voice selection.

    Returns:
        Dict with audio_bytes, audio_base64, and duration_ms.
    """
    start = time.perf_counter()

    voice = _VOICE_MAP.get(language, "alloy")

    response = await client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
        response_format="mp3",
    )

    audio_bytes = response.content
    duration_ms = (time.perf_counter() - start) * 1000

    return {
        "audio_bytes": audio_bytes,
        "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
        "duration_ms": duration_ms,
    }


async def process_voice(
    audio_bytes: bytes,
    account_id: str = "acc_001",
    enable_tts: bool = True,
) -> dict[str, Any]:
    """Full voice pipeline: ASR -> Agent -> optional TTS.

    Args:
        audio_bytes: Raw audio bytes from the client.
        account_id: DuniaWallet account ID.
        enable_tts: Whether to generate audio response.

    Returns:
        Dict with response, transcript, tools, latency breakdown, and optional audio.
    """
    from openai import AsyncOpenAI
    from src.config import get_settings

    settings = get_settings()
    latency: dict[str, float] = {}

    if not settings.openai_api_key:
        return {
            "response": "Voice service is temporarily unavailable. Please use text mode.",
            "transcript": "",
            "language_detected": "en",
            "tools_used": [],
            "latency_ms": {},
            "audio_base64": None,
        }

    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Stage 1: ASR (Whisper)
    try:
        asr_result = await transcribe_audio(openai_client, audio_bytes)
        transcript = asr_result["transcript"]
        latency["asr_ms"] = asr_result["duration_ms"]
        logger.info("ASR complete: '%s' (%.0fms)", transcript[:50], asr_result["duration_ms"])
    except Exception:
        logger.error("Whisper transcription failed", exc_info=True)
        return {
            "response": "Could not transcribe your audio. Please try again or use text mode.",
            "transcript": "",
            "language_detected": "en",
            "tools_used": [],
            "latency_ms": latency,
            "audio_base64": None,
        }

    if not transcript.strip():
        return {
            "response": "I couldn't hear anything in your audio. Please try again.",
            "transcript": "",
            "language_detected": "en",
            "tools_used": [],
            "latency_ms": latency,
            "audio_base64": None,
        }

    # Stage 2: Agent processing
    from src.agent.core import process_message

    agent_result = await process_message(
        message=transcript,
        account_id=account_id,
    )

    latency["agent_processing_ms"] = agent_result.latency_ms.get("total_ms", 0.0)
    latency["language_detection_ms"] = agent_result.latency_ms.get("language_detection_ms", 0.0)
    language = agent_result.language_detected.value

    tools_used = [
        {
            "tool_name": t.tool_name,
            "arguments": t.arguments,
            "result": t.result,
            "duration_ms": t.duration_ms,
        }
        for t in agent_result.tools_used
    ]

    # Stage 3: TTS (optional)
    audio_base64 = None
    if enable_tts:
        try:
            tts_result = await synthesize_speech(
                openai_client,
                agent_result.response_text,
                language=language,
            )
            audio_base64 = tts_result["audio_base64"]
            latency["tts_ms"] = tts_result["duration_ms"]
        except Exception:
            logger.warning("TTS synthesis failed, returning text only", exc_info=True)

    # Total E2E latency
    latency["total_e2e_ms"] = sum(latency.values())

    return {
        "response": agent_result.response_text,
        "transcript": transcript,
        "language_detected": language,
        "tools_used": tools_used,
        "latency_ms": latency,
        "audio_base64": audio_base64,
    }
