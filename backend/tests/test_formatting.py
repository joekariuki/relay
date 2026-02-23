"""Tests for response text cleaning and formatting."""

from src.agent.formatting import clean_response_text


class TestEmojiRemoval:
    def test_removes_simple_emoji(self) -> None:
        assert clean_response_text("Hello! \U0001f600") == "Hello!"

    def test_removes_multiple_emojis(self) -> None:
        result = clean_response_text("Great \U0001f44d news \U0001f389 today!")
        assert "\U0001f44d" not in result
        assert "\U0001f389" not in result
        assert "Great  news  today!" == result

    def test_preserves_text_without_emojis(self) -> None:
        text = "Your balance is 245,000 FCFA."
        assert clean_response_text(text) == text

    def test_removes_flag_emojis(self) -> None:
        result = clean_response_text("Senegal \U0001f1f8\U0001f1f3")
        assert "Senegal" in result
        assert "\U0001f1f8" not in result

    def test_removes_wave_emoji(self) -> None:
        assert clean_response_text("\U0001f44b Bonjour!") == "Bonjour!"


class TestNewlineNormalization:
    def test_collapses_triple_newlines(self) -> None:
        assert clean_response_text("a\n\n\nb") == "a\n\nb"

    def test_collapses_many_newlines(self) -> None:
        assert clean_response_text("a\n\n\n\n\n\nb") == "a\n\nb"

    def test_preserves_double_newlines(self) -> None:
        assert clean_response_text("a\n\nb") == "a\n\nb"

    def test_preserves_single_newlines(self) -> None:
        assert clean_response_text("a\nb") == "a\nb"


class TestWhitespaceStripping:
    def test_strips_trailing_whitespace_per_line(self) -> None:
        assert clean_response_text("hello   \nworld  ") == "hello\nworld"

    def test_strips_leading_trailing_whitespace(self) -> None:
        assert clean_response_text("  hello  ") == "hello"

    def test_empty_string(self) -> None:
        assert clean_response_text("") == ""

    def test_whitespace_only(self) -> None:
        assert clean_response_text("   \n\n   ") == ""


class TestCombinedCleaning:
    def test_emoji_and_newlines(self) -> None:
        text = "\U0001f600 Hello!\n\n\n\nHow can I help?  "
        result = clean_response_text(text)
        assert result == "Hello!\n\nHow can I help?"

    def test_realistic_claude_response(self) -> None:
        text = (
            "\U0001f44b Bonjour Amadou!\n\n\n"
            "Your account balance is **245,000 FCFA**.  \n\n"
            "Is there anything else I can help with? \U0001f60a"
        )
        result = clean_response_text(text)
        assert "\U0001f44b" not in result
        assert "\U0001f60a" not in result
        assert "245,000 FCFA" in result
        assert "\n\n\n" not in result
