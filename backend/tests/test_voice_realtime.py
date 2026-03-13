"""Tests for the real-time voice streaming pipeline.

All tests use mocked Deepgram and OpenAI clients -- no real API calls.
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.schemas import (
    WSAgentStatus,
    WSAgentTextDelta,
    WSAudioChunk,
    WSError,
    WSListening,
    WSSessionEnd,
    WSSessionStart,
    WSSessionStarted,
    WSTranscriptFinal,
    WSTranscriptPartial,
    WSTurnDone,
)
from src.api.server import app
from src.voice.realtime import (
    DEEPGRAM_LANGUAGE_MAP,
    VOICE_MAP,
    VoiceSession,
    split_sentences,
    synthesize_sentence,
)


# --- WebSocket Message Schemas ---


class TestWebSocketSchemas:
    def test_session_start_defaults(self) -> None:
        msg = WSSessionStart()
        assert msg.type == "session_start"
        assert msg.account_id == "acc_001"
        assert msg.language == "auto"
        assert msg.session_id is None

    def test_session_start_with_session_id(self) -> None:
        msg = WSSessionStart(session_id="abc123", account_id="acc_005", language="fr")
        assert msg.session_id == "abc123"
        assert msg.account_id == "acc_005"
        assert msg.language == "fr"

    def test_session_end(self) -> None:
        msg = WSSessionEnd()
        assert msg.type == "session_end"

    def test_session_started(self) -> None:
        msg = WSSessionStarted(session_id="xyz789")
        assert msg.type == "session_started"
        assert msg.session_id == "xyz789"

    def test_listening(self) -> None:
        msg = WSListening()
        assert msg.type == "listening"

    def test_transcript_partial(self) -> None:
        msg = WSTranscriptPartial(text="What is my...")
        assert msg.type == "transcript_partial"
        assert msg.text == "What is my..."

    def test_transcript_final(self) -> None:
        msg = WSTranscriptFinal(text="What is my balance?")
        assert msg.type == "transcript_final"

    def test_agent_status(self) -> None:
        msg = WSAgentStatus(message="Checking account balance")
        assert msg.type == "agent_status"

    def test_agent_text_delta(self) -> None:
        msg = WSAgentTextDelta(chunk="Your current")
        assert msg.type == "agent_text_delta"

    def test_audio_chunk(self) -> None:
        msg = WSAudioChunk(data="base64data==")
        assert msg.type == "audio_chunk"

    def test_turn_done(self) -> None:
        msg = WSTurnDone(
            session_id="abc",
            language_detected="en",
            tools_used=[],
            latency_ms={"total_ms": 1500.0},
        )
        assert msg.type == "turn_done"
        assert msg.session_id == "abc"
        assert msg.groundedness_score is None

    def test_error(self) -> None:
        msg = WSError(message="Something went wrong")
        assert msg.type == "error"

    def test_schema_serialization_roundtrip(self) -> None:
        msg = WSSessionStart(account_id="acc_003", language="sw")
        data = msg.model_dump()
        restored = WSSessionStart(**data)
        assert restored.account_id == "acc_003"
        assert restored.language == "sw"


# --- Sentence Splitting ---


class TestSentenceSplitting:
    def test_single_sentence(self) -> None:
        assert split_sentences("Hello there.") == ["Hello there."]

    def test_two_sentences(self) -> None:
        result = split_sentences(
            "Your balance is 45,000 FCFA. Would you like to do anything else?"
        )
        assert len(result) == 2
        assert result[0] == "Your balance is 45,000 FCFA."
        assert result[1] == "Would you like to do anything else?"

    def test_question_mark_split(self) -> None:
        result = split_sentences("Is that correct? Let me check your account details again.")
        assert len(result) == 2

    def test_exclamation_split(self) -> None:
        result = split_sentences("Done! Your transfer has been processed.")
        assert len(result) == 2

    def test_short_trailing_fragment_merged(self) -> None:
        result = split_sentences("Your balance is 45,000 FCFA. Thank you.")
        assert len(result) == 1
        assert "Thank you" in result[0]

    def test_empty_string(self) -> None:
        assert split_sentences("") == []

    def test_whitespace_only(self) -> None:
        assert split_sentences("   ") == []

    def test_no_sentence_boundary(self) -> None:
        text = "your balance is 45,000 FCFA which is available for transfers"
        result = split_sentences(text)
        assert len(result) == 1

    def test_preserves_numbers_and_currency(self) -> None:
        text = "The fee is 1,500 FCFA. The total would be 46,500 FCFA."
        result = split_sentences(text)
        for part in result:
            assert "FCFA" in part

    def test_french_text(self) -> None:
        text = "Votre solde est de 45 000 FCFA. Souhaitez-vous autre chose?"
        result = split_sentences(text)
        assert len(result) == 2


# --- Voice Maps ---


class TestVoiceMaps:
    def test_voice_map_english(self) -> None:
        assert VOICE_MAP["en"] == "alloy"

    def test_voice_map_french(self) -> None:
        assert VOICE_MAP["fr"] == "nova"

    def test_voice_map_swahili(self) -> None:
        assert VOICE_MAP["sw"] == "echo"

    def test_deepgram_language_map(self) -> None:
        assert DEEPGRAM_LANGUAGE_MAP["en"] == "en"
        assert DEEPGRAM_LANGUAGE_MAP["fr"] == "fr"
        assert DEEPGRAM_LANGUAGE_MAP["sw"] == "sw"
        assert DEEPGRAM_LANGUAGE_MAP["auto"] == "en"


# --- TTS Synthesis ---


class TestSynthesizeSentence:
    @pytest.mark.asyncio
    async def test_returns_base64_audio(self) -> None:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = b"fake_mp3_audio"
        mock_client.audio.speech.create = AsyncMock(return_value=mock_response)

        result = await synthesize_sentence(mock_client, "Hello world", language="en")

        assert "audio_base64" in result
        assert len(result["audio_base64"]) > 0
        assert result["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_uses_correct_voice_for_language(self) -> None:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = b"audio"
        mock_client.audio.speech.create = AsyncMock(return_value=mock_response)

        await synthesize_sentence(mock_client, "Bonjour", language="fr")

        call_kwargs = mock_client.audio.speech.create.call_args.kwargs
        assert call_kwargs["voice"] == "nova"

    @pytest.mark.asyncio
    async def test_uses_configurable_model(self) -> None:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = b"audio"
        mock_client.audio.speech.create = AsyncMock(return_value=mock_response)

        await synthesize_sentence(mock_client, "Test", language="en", model="tts-1-hd")

        call_kwargs = mock_client.audio.speech.create.call_args.kwargs
        assert call_kwargs["model"] == "tts-1-hd"


# --- VoiceSession ---


class TestVoiceSession:
    def test_init(self) -> None:
        session = VoiceSession(account_id="acc_001", session_id="test123", language="fr")
        assert session.account_id == "acc_001"
        assert session.session_id == "test123"
        assert session.language == "fr"

    @pytest.mark.asyncio
    async def test_connect_asr_requires_api_key(self) -> None:
        session = VoiceSession(account_id="acc_001", session_id="test123")
        with patch("src.voice.realtime.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(deepgram_api_key="", voice_endpointing_ms=800)
            with pytest.raises(RuntimeError, match="DEEPGRAM_API_KEY"):
                await session.connect_asr()

    @pytest.mark.asyncio
    async def test_send_audio_noop_when_disconnected(self) -> None:
        session = VoiceSession(account_id="acc_001", session_id="test123")
        await session.send_audio(b"some_audio_bytes")

    @pytest.mark.asyncio
    async def test_get_transcript_event_returns_none_on_timeout(self) -> None:
        session = VoiceSession(account_id="acc_001", session_id="test123")
        result = await session.get_transcript_event(timeout=0.01)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_transcript_event_returns_queued_event(self) -> None:
        session = VoiceSession(account_id="acc_001", session_id="test123")
        await session._transcript_queue.put({"type": "utterance_end", "text": "Hello"})

        result = await session.get_transcript_event(timeout=0.1)
        assert result is not None
        assert result["type"] == "utterance_end"
        assert result["text"] == "Hello"

    @pytest.mark.asyncio
    async def test_close_without_connect(self) -> None:
        session = VoiceSession(account_id="acc_001", session_id="test123")
        await session.close()


# --- Session Store Integration ---


class TestVoiceSessionIntegration:
    def test_session_creation_and_lookup(self) -> None:
        from src.session import SessionStore

        store = SessionStore(ttl_minutes=30)
        sid = store.create_session("acc_001")
        assert store.get_messages(sid) == []
        assert store.get_account_id(sid) == "acc_001"

    def test_session_message_persistence(self) -> None:
        from src.session import SessionStore

        store = SessionStore(ttl_minutes=30)
        sid = store.create_session("acc_001")
        store.update_messages(sid, ["msg1", "msg2"])  # type: ignore[arg-type]
        assert store.get_messages(sid) == ["msg1", "msg2"]

    def test_session_resume_with_existing_id(self) -> None:
        from src.session import SessionStore

        store = SessionStore(ttl_minutes=30)
        sid = store.create_session("acc_001")
        store.update_messages(sid, ["turn1"])  # type: ignore[arg-type]

        messages = store.get_messages(sid)
        assert messages == ["turn1"]

    def test_invalid_session_id_returns_none(self) -> None:
        from src.session import SessionStore

        store = SessionStore(ttl_minutes=30)
        assert store.get_messages("nonexistent") is None


# --- StreamEvent Generator ---


class TestStreamAgentResponse:

    def _mock_settings(self) -> MagicMock:
        """Create a mock Settings with use_multi_agent=False to skip classification."""
        settings = MagicMock()
        settings.use_multi_agent = False
        settings.language_detection_timeout_s = 2.0
        settings.language_detection_model = "test-model"
        settings.agent_model = "test-model"
        settings.agent_max_tokens = 100
        settings.agent_max_tool_rounds = 3
        return settings

    @pytest.mark.asyncio
    async def test_yields_status_events(self) -> None:
        from pydantic_graph import End

        from src.agent.core import StreamContext, StreamEvent, stream_agent_response

        events: list[StreamEvent] = []

        with patch("src.agent.core.check_guardrails") as mock_guard, \
             patch("src.agent.core.detect_language", new_callable=AsyncMock) as mock_lang, \
             patch("src.agent.core.get_settings") as mock_get_settings, \
             patch("src.agent.core.support_agent") as mock_agent:

            mock_get_settings.return_value = self._mock_settings()
            mock_guard.return_value = MagicMock(
                safe=True, injection_detected=False, flags=[]
            )
            mock_lang.return_value = MagicMock(
                language="en", confidence=0.9,
                code_switching=False, secondary_language=None,
            )

            mock_result = MagicMock()
            mock_result.output = "Your balance is 245,000 FCFA."
            mock_result.all_messages.return_value = ["msg1", "msg2"]

            mock_run = AsyncMock()
            mock_run.next_node = End("done")
            mock_run.result = mock_result

            mock_ctx_manager = AsyncMock()
            mock_ctx_manager.__aenter__ = AsyncMock(return_value=mock_run)
            mock_ctx_manager.__aexit__ = AsyncMock(return_value=False)
            mock_agent.iter.return_value = mock_ctx_manager

            from src.agent.orchestrator import AgentType
            with patch.dict("src.agent.core.AGENTS", {AgentType.SUPPORT: mock_agent}):
                ctx = StreamContext()
                async for event in stream_agent_response(
                    message="What is my balance?",
                    stream_context=ctx,
                ):
                    events.append(event)

        event_types = [e.type for e in events]
        assert "status" in event_types
        assert "done" in event_types

    @pytest.mark.asyncio
    async def test_stream_context_populated(self) -> None:
        from pydantic_graph import End

        from src.agent.core import StreamContext, stream_agent_response

        with patch("src.agent.core.check_guardrails") as mock_guard, \
             patch("src.agent.core.detect_language", new_callable=AsyncMock) as mock_lang, \
             patch("src.agent.core.get_settings") as mock_get_settings, \
             patch("src.agent.core.support_agent") as mock_agent:

            mock_get_settings.return_value = self._mock_settings()
            mock_guard.return_value = MagicMock(
                safe=True, injection_detected=False, flags=[]
            )
            mock_lang.return_value = MagicMock(
                language="en", confidence=0.9,
                code_switching=False, secondary_language=None,
            )

            mock_result = MagicMock()
            mock_result.output = "Test response"
            mock_result.all_messages.return_value = ["history_msg1", "history_msg2"]

            mock_run = AsyncMock()
            mock_run.next_node = End("done")
            mock_run.result = mock_result

            mock_ctx_manager = AsyncMock()
            mock_ctx_manager.__aenter__ = AsyncMock(return_value=mock_run)
            mock_ctx_manager.__aexit__ = AsyncMock(return_value=False)
            mock_agent.iter.return_value = mock_ctx_manager

            from src.agent.orchestrator import AgentType
            with patch.dict("src.agent.core.AGENTS", {AgentType.SUPPORT: mock_agent}):
                ctx = StreamContext()
                async for _ in stream_agent_response(
                    message="Test",
                    stream_context=ctx,
                ):
                    pass

        assert len(ctx.all_messages) == 2

    @pytest.mark.asyncio
    async def test_error_on_exception(self) -> None:
        from src.agent.core import StreamEvent, stream_agent_response

        with patch("src.agent.core.check_guardrails", side_effect=Exception("boom")):
            events: list[StreamEvent] = []
            async for event in stream_agent_response(message="crash"):
                events.append(event)

        assert any(e.type == "error" for e in events)

    @pytest.mark.asyncio
    async def test_yields_progressive_text_deltas(self) -> None:
        """Verify that text chunks are yielded progressively, not batched."""
        from pydantic_graph import End

        from src.agent.core import StreamContext, StreamEvent, stream_agent_response

        events: list[StreamEvent] = []

        with patch("src.agent.core.check_guardrails") as mock_guard, \
             patch("src.agent.core.detect_language", new_callable=AsyncMock) as mock_lang, \
             patch("src.agent.core.get_settings") as mock_get_settings, \
             patch("src.agent.core.support_agent") as mock_agent:

            mock_get_settings.return_value = self._mock_settings()
            mock_guard.return_value = MagicMock(
                safe=True, injection_detected=False, flags=[]
            )
            mock_lang.return_value = MagicMock(
                language="en", confidence=0.9,
                code_switching=False, secondary_language=None,
            )

            # Simulate a model request node that streams 3 text chunks
            text_chunks = ["Your balance ", "is 245,000 ", "FCFA."]

            async def fake_stream_text(delta: bool = True, debounce_by: object = None):  # noqa: ANN001, ARG001
                for chunk in text_chunks:
                    yield chunk

            mock_stream = MagicMock()
            mock_stream.stream_text = fake_stream_text

            mock_stream_ctx = AsyncMock()
            mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_stream)
            mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

            # Create a model request node mock
            mock_model_node = MagicMock()
            mock_model_node.stream.return_value = mock_stream_ctx

            end_node = End("done")

            mock_result = MagicMock()
            mock_result.output = "Your balance is 245,000 FCFA."
            mock_result.all_messages.return_value = ["msg1", "msg2"]

            # next_node returns model node first, then next() returns End
            mock_run = AsyncMock()
            mock_run.next_node = mock_model_node
            mock_run.result = mock_result
            mock_run.ctx = MagicMock()
            mock_run.next = AsyncMock(return_value=end_node)

            mock_agent.is_model_request_node.return_value = True
            mock_agent.is_call_tools_node.return_value = False

            mock_ctx_manager = AsyncMock()
            mock_ctx_manager.__aenter__ = AsyncMock(return_value=mock_run)
            mock_ctx_manager.__aexit__ = AsyncMock(return_value=False)
            mock_agent.iter.return_value = mock_ctx_manager

            from src.agent.orchestrator import AgentType
            with patch.dict("src.agent.core.AGENTS", {AgentType.SUPPORT: mock_agent}):
                ctx = StreamContext()
                async for event in stream_agent_response(
                    message="What is my balance?",
                    stream_context=ctx,
                ):
                    events.append(event)

        # Should have multiple text_delta events (one per chunk)
        text_deltas = [e for e in events if e.type == "text_delta"]
        assert len(text_deltas) == 3, f"Expected 3 text_delta events, got {len(text_deltas)}"
        assert text_deltas[0].data["chunk"] == "Your balance "
        assert text_deltas[1].data["chunk"] == "is 245,000 "
        assert text_deltas[2].data["chunk"] == "FCFA."

    @pytest.mark.asyncio
    async def test_streaming_strips_emojis_per_chunk(self) -> None:
        """Verify that emoji characters are stripped from each streamed chunk."""
        from pydantic_graph import End

        from src.agent.core import StreamEvent, stream_agent_response

        events: list[StreamEvent] = []

        with patch("src.agent.core.check_guardrails") as mock_guard, \
             patch("src.agent.core.detect_language", new_callable=AsyncMock) as mock_lang, \
             patch("src.agent.core.get_settings") as mock_get_settings, \
             patch("src.agent.core.support_agent") as mock_agent:

            mock_get_settings.return_value = self._mock_settings()
            mock_guard.return_value = MagicMock(
                safe=True, injection_detected=False, flags=[]
            )
            mock_lang.return_value = MagicMock(
                language="en", confidence=0.9,
                code_switching=False, secondary_language=None,
            )

            # Chunks with emojis that should be stripped
            text_chunks = ["Hello! 😊 ", "Your balance ", "is ready 🎉"]

            async def fake_stream_text(delta: bool = True, debounce_by: object = None):  # noqa: ANN001, ARG001
                for chunk in text_chunks:
                    yield chunk

            mock_stream = MagicMock()
            mock_stream.stream_text = fake_stream_text

            mock_stream_ctx = AsyncMock()
            mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_stream)
            mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

            mock_model_node = MagicMock()
            mock_model_node.stream.return_value = mock_stream_ctx

            end_node = End("done")

            mock_result = MagicMock()
            mock_result.output = "Hello! Your balance is ready"
            mock_result.all_messages.return_value = []

            mock_run = AsyncMock()
            mock_run.next_node = mock_model_node
            mock_run.result = mock_result
            mock_run.ctx = MagicMock()
            mock_run.next = AsyncMock(return_value=end_node)

            mock_agent.is_model_request_node.return_value = True
            mock_agent.is_call_tools_node.return_value = False

            mock_ctx_manager = AsyncMock()
            mock_ctx_manager.__aenter__ = AsyncMock(return_value=mock_run)
            mock_ctx_manager.__aexit__ = AsyncMock(return_value=False)
            mock_agent.iter.return_value = mock_ctx_manager

            from src.agent.orchestrator import AgentType
            with patch.dict("src.agent.core.AGENTS", {AgentType.SUPPORT: mock_agent}):
                async for event in stream_agent_response(message="Hi"):
                    events.append(event)

        text_deltas = [e for e in events if e.type == "text_delta"]
        assert len(text_deltas) == 3
        # Emojis should be stripped
        assert "😊" not in text_deltas[0].data["chunk"]
        assert "🎉" not in text_deltas[2].data["chunk"]
        assert text_deltas[0].data["chunk"] == "Hello!  "
        assert text_deltas[1].data["chunk"] == "Your balance "
        assert text_deltas[2].data["chunk"] == "is ready "


# --- WebSocket Endpoint ---


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


async def _yielding_none(*args, **kwargs):  # type: ignore[no-untyped-def]
    """Mock get_transcript_event that actually yields to the event loop."""
    await asyncio.sleep(0.05)
    return None


class TestVoiceWebSocketEndpoint:
    def test_invalid_first_message_rejected(self, client: TestClient) -> None:
        with client.websocket_connect("/ws/voice") as ws:
            ws.send_json({"type": "not_session_start"})
            data = ws.receive_json()
            assert data["type"] == "error"
            assert "session_start" in data["message"].lower()

    def test_session_start_returns_session_started(self, client: TestClient) -> None:
        with patch("src.voice.realtime.VoiceSession.connect_asr", new_callable=AsyncMock), \
             patch("src.voice.realtime.VoiceSession.close", new_callable=AsyncMock), \
             patch("src.voice.realtime.VoiceSession.get_transcript_event", side_effect=_yielding_none):

            with client.websocket_connect("/ws/voice") as ws:
                ws.send_json({
                    "type": "session_start",
                    "account_id": "acc_001",
                    "language": "en",
                })
                data = ws.receive_json()
                assert data["type"] == "session_started"
                assert "session_id" in data
                assert len(data["session_id"]) > 0

                data2 = ws.receive_json()
                assert data2["type"] == "listening"

                ws.send_json({"type": "session_end"})

    def test_session_start_with_existing_session_id(self, client: TestClient) -> None:
        from src.session import SessionStore

        store = SessionStore(ttl_minutes=30)
        sid = store.create_session("acc_001")
        store.update_messages(sid, ["prior_msg"])  # type: ignore[arg-type]

        with patch("src.session.get_session_store", return_value=store), \
             patch("src.voice.realtime.VoiceSession.connect_asr", new_callable=AsyncMock), \
             patch("src.voice.realtime.VoiceSession.close", new_callable=AsyncMock), \
             patch("src.voice.realtime.VoiceSession.get_transcript_event", side_effect=_yielding_none):

            with client.websocket_connect("/ws/voice") as ws:
                ws.send_json({
                    "type": "session_start",
                    "account_id": "acc_001",
                    "language": "en",
                    "session_id": sid,
                })
                data = ws.receive_json()
                assert data["type"] == "session_started"
                assert data["session_id"] == sid

                ws.send_json({"type": "session_end"})

    def test_session_end_closes_cleanly(self, client: TestClient) -> None:
        with patch("src.voice.realtime.VoiceSession.connect_asr", new_callable=AsyncMock), \
             patch("src.voice.realtime.VoiceSession.close", new_callable=AsyncMock) as mock_close, \
             patch("src.voice.realtime.VoiceSession.get_transcript_event", side_effect=_yielding_none):

            with client.websocket_connect("/ws/voice") as ws:
                ws.send_json({
                    "type": "session_start",
                    "account_id": "acc_001",
                })
                ws.receive_json()
                ws.receive_json()

                ws.send_json({"type": "session_end"})

            mock_close.assert_called_once()
