"""Real-time voice streaming pipeline: Deepgram ASR -> Agent -> OpenAI TTS.

Uses WebSocket-based streaming for low-latency voice-to-voice interaction.
Deepgram handles speech-to-text with built-in VAD (endpointing), and
OpenAI TTS synthesizes the agent response sentence-by-sentence for
perceived streaming playback.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

from deepgram import AsyncDeepgramClient
from deepgram.listen.v1.types.listen_v1results import ListenV1Results
from deepgram.listen.v1.types.listen_v1utterance_end import ListenV1UtteranceEnd

from src.config import get_settings

logger = logging.getLogger(__name__)

VOICE_MAP: dict[str, str] = {
    "en": "alloy",
    "fr": "nova",
    "sw": "echo",
}

DEEPGRAM_LANGUAGE_MAP: dict[str, str] = {
    "en": "en",
    "fr": "fr",
    "sw": "sw",
    "auto": "en",
}

_SENTENCE_SPLIT_RE = re.compile(
    r"(?<=[.!?])\s+(?=[A-Z\u00C0-\u024F])"
)


def split_sentences(text: str) -> list[str]:
    """Split text into sentences for incremental TTS synthesis.

    Splits on sentence-ending punctuation followed by whitespace and an
    uppercase letter. Keeps short trailing fragments attached to the
    previous sentence to avoid synthesizing tiny audio clips.
    """
    parts = _SENTENCE_SPLIT_RE.split(text)
    if not parts:
        return [text] if text.strip() else []

    result: list[str] = []
    for part in parts:
        stripped = part.strip()
        if not stripped:
            continue
        if result and len(stripped) < 20:
            result[-1] = result[-1] + " " + stripped
        else:
            result.append(stripped)
    return result


async def synthesize_sentence(
    openai_client: Any,
    text: str,
    language: str,
    model: str = "tts-1",
) -> dict[str, Any]:
    """Synthesize a single sentence to MP3 audio via OpenAI TTS."""
    start = time.perf_counter()
    voice = VOICE_MAP.get(language, "alloy")

    response = await openai_client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        response_format="mp3",
    )

    audio_bytes = response.content
    duration_ms = (time.perf_counter() - start) * 1000

    return {
        "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
        "duration_ms": duration_ms,
    }


@dataclass
class VoiceSession:
    """Manages a single real-time voice mode session.

    Coordinates Deepgram streaming ASR, the pydantic-ai agent,
    and OpenAI TTS for a bidirectional voice conversation.
    """

    account_id: str
    session_id: str
    language: str = "en"
    _deepgram_client: AsyncDeepgramClient | None = field(default=None, repr=False)
    _deepgram_ws: Any = field(default=None, repr=False)
    _transcript_buffer: str = field(default="", repr=False)
    _is_connected: bool = field(default=False, repr=False)
    _receive_task: asyncio.Task[None] | None = field(default=None, repr=False)
    _transcript_queue: asyncio.Queue[dict[str, Any]] = field(
        default_factory=asyncio.Queue, repr=False
    )

    async def connect_asr(self) -> None:
        """Open a streaming connection to Deepgram for live transcription."""
        settings = get_settings()
        if not settings.deepgram_api_key:
            raise RuntimeError("DEEPGRAM_API_KEY is not configured")

        self._deepgram_client = AsyncDeepgramClient(api_key=settings.deepgram_api_key)

        dg_language = DEEPGRAM_LANGUAGE_MAP.get(self.language, "en")

        self._deepgram_ws_ctx = self._deepgram_client.listen.v1.connect(
            model="nova-2",
            language=dg_language,
            encoding="linear16",
            sample_rate="16000",
            channels="1",
            interim_results="true",
            utterance_end_ms=str(settings.voice_endpointing_ms),
            vad_events="true",
            punctuate="true",
            smart_format="true",
        )
        self._deepgram_ws = await self._deepgram_ws_ctx.__aenter__()
        self._is_connected = True

        self._receive_task = asyncio.create_task(self._receive_loop())
        logger.info("Deepgram ASR connected (session=%s, lang=%s)", self.session_id, dg_language)

    async def _receive_loop(self) -> None:
        """Read messages from Deepgram and push them onto the transcript queue."""
        try:
            async for msg in self._deepgram_ws:
                if isinstance(msg, ListenV1Results):
                    transcript = ""
                    if msg.channel and msg.channel.alternatives:
                        transcript = msg.channel.alternatives[0].transcript or ""

                    if not transcript.strip():
                        continue

                    is_final = bool(msg.is_final)
                    if is_final:
                        self._transcript_buffer += (" " + transcript).lstrip()

                    await self._transcript_queue.put({
                        "type": "transcript_partial" if not is_final else "transcript_interim_final",
                        "text": transcript if not is_final else self._transcript_buffer.strip(),
                        "is_final": is_final,
                    })

                elif isinstance(msg, ListenV1UtteranceEnd):
                    final_text = self._transcript_buffer.strip()
                    self._transcript_buffer = ""
                    if final_text:
                        await self._transcript_queue.put({
                            "type": "utterance_end",
                            "text": final_text,
                        })
        except Exception:
            if self._is_connected:
                logger.error("Deepgram receive loop error", exc_info=True)
                await self._transcript_queue.put({
                    "type": "error",
                    "text": "ASR connection error",
                })

    async def send_audio(self, audio_bytes: bytes) -> None:
        """Forward raw PCM audio bytes to the Deepgram connection."""
        if self._deepgram_ws and self._is_connected:
            await self._deepgram_ws.send_media(audio_bytes)

    async def get_transcript_event(self, timeout: float = 0.1) -> dict[str, Any] | None:
        """Get the next transcript event from the queue, or None on timeout."""
        try:
            return await asyncio.wait_for(self._transcript_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def close(self) -> None:
        """Cleanly close the Deepgram connection."""
        self._is_connected = False
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self._deepgram_ws:
            try:
                await self._deepgram_ws.send_close_stream()
            except Exception:
                pass

        if hasattr(self, "_deepgram_ws_ctx"):
            try:
                await self._deepgram_ws_ctx.__aexit__(None, None, None)
            except Exception:
                pass

        self._deepgram_ws = None
        logger.info("Deepgram ASR disconnected (session=%s)", self.session_id)
