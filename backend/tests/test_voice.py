"""Tests for the voice pipeline with mocked OpenAI clients."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.voice.pipeline import _VOICE_MAP, process_voice, transcribe_audio, synthesize_speech


class TestVoiceMap:
    def test_english_voice(self) -> None:
        assert _VOICE_MAP["en"] == "alloy"

    def test_french_voice(self) -> None:
        assert _VOICE_MAP["fr"] == "nova"

    def test_swahili_voice(self) -> None:
        assert _VOICE_MAP["sw"] == "echo"


class TestTranscribeAudio:
    @pytest.mark.asyncio
    async def test_transcribe_returns_transcript(self) -> None:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.text = "What is my balance?"
        mock_response.language = "en"
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        result = await transcribe_audio(mock_client, b"fake_audio_bytes")

        assert result["transcript"] == "What is my balance?"
        assert result["detected_language"] == "en"
        assert result["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_transcribe_with_custom_filename(self) -> None:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.text = "Quel est mon solde?"
        mock_response.language = "fr"
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        result = await transcribe_audio(mock_client, b"audio", filename="recording.mp3")

        assert result["transcript"] == "Quel est mon solde?"
        assert result["detected_language"] == "fr"


class TestSynthesizeSpeech:
    @pytest.mark.asyncio
    async def test_synthesize_returns_audio(self) -> None:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = b"fake_mp3_bytes"
        mock_client.audio.speech.create = AsyncMock(return_value=mock_response)

        result = await synthesize_speech(mock_client, "Hello world", language="en")

        assert result["audio_bytes"] == b"fake_mp3_bytes"
        assert len(result["audio_base64"]) > 0
        assert result["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_synthesize_french_uses_nova(self) -> None:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = b"audio"
        mock_client.audio.speech.create = AsyncMock(return_value=mock_response)

        await synthesize_speech(mock_client, "Bonjour", language="fr")

        call_kwargs = mock_client.audio.speech.create.call_args.kwargs
        assert call_kwargs["voice"] == "nova"


class TestProcessVoice:
    @pytest.mark.asyncio
    @patch("src.voice.pipeline.synthesize_speech", new_callable=AsyncMock)
    @patch("src.voice.pipeline.transcribe_audio", new_callable=AsyncMock)
    @patch("src.agent.core.process_message", new_callable=AsyncMock)
    async def test_full_pipeline(
        self,
        mock_agent: AsyncMock,
        mock_asr: AsyncMock,
        mock_tts: AsyncMock,
    ) -> None:
        from src.knowledge.models import AgentResponse, Language

        mock_asr.return_value = {
            "transcript": "What is my balance?",
            "detected_language": "en",
            "duration_ms": 500.0,
        }
        mock_agent.return_value = (
            AgentResponse(
                response_text="Your balance is 245,000 FCFA.",
                language_detected=Language.EN,
                tools_used=[],
                groundedness_score=None,
                latency_ms={"total_ms": 200.0, "language_detection_ms": 50.0},
            ),
            [],
        )
        mock_tts.return_value = {
            "audio_bytes": b"audio",
            "audio_base64": "YXVkaW8=",
            "duration_ms": 300.0,
        }

        # Patch openai and settings
        with patch("openai.AsyncOpenAI"):
            with patch("src.config.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(openai_api_key="test-key")
                result = await process_voice(b"fake_audio")

        assert result["response"] == "Your balance is 245,000 FCFA."
        assert result["transcript"] == "What is my balance?"
        assert result["language_detected"] == "en"
        assert "asr_ms" in result["latency_ms"]
        assert "agent_processing_ms" in result["latency_ms"]

    @pytest.mark.asyncio
    async def test_no_api_key_returns_error(self) -> None:
        with patch("src.config.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key="")
            result = await process_voice(b"fake_audio")

        assert "unavailable" in result["response"].lower()
        assert result["transcript"] == ""

    @pytest.mark.asyncio
    @patch("src.voice.pipeline.transcribe_audio", new_callable=AsyncMock)
    async def test_asr_failure_returns_error(self, mock_asr: AsyncMock) -> None:
        mock_asr.side_effect = Exception("Whisper failed")

        with patch("openai.AsyncOpenAI"):
            with patch("src.config.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(openai_api_key="test-key")
                result = await process_voice(b"bad_audio")

        assert "could not transcribe" in result["response"].lower()

    @pytest.mark.asyncio
    @patch("src.voice.pipeline.transcribe_audio", new_callable=AsyncMock)
    async def test_empty_transcript_returns_error(self, mock_asr: AsyncMock) -> None:
        mock_asr.return_value = {
            "transcript": "",
            "detected_language": "en",
            "duration_ms": 100.0,
        }

        with patch("openai.AsyncOpenAI"):
            with patch("src.config.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(openai_api_key="test-key")
                result = await process_voice(b"silence")

        assert "couldn't hear" in result["response"].lower()
