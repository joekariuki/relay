"""Tests for language detection (heuristic fallback)."""

from src.agent.router import _heuristic_language_detect


class TestHeuristicLanguageDetection:
    def test_french_greeting(self) -> None:
        result = _heuristic_language_detect("Bonjour, quel est mon solde?")
        assert result.language == "fr"

    def test_french_transfer(self) -> None:
        result = _heuristic_language_detect("Je veux envoyer de l'argent")
        assert result.language == "fr"

    def test_french_fee_inquiry(self) -> None:
        result = _heuristic_language_detect("Combien sont les frais pour un transfert?")
        assert result.language == "fr"

    def test_swahili_greeting(self) -> None:
        result = _heuristic_language_detect("Habari, nataka kuona salio yangu")
        assert result.language == "sw"

    def test_swahili_help(self) -> None:
        result = _heuristic_language_detect("Tafadhali msaada nataka kutuma pesa")
        assert result.language == "sw"

    def test_english_default(self) -> None:
        result = _heuristic_language_detect("What is my balance?")
        assert result.language == "en"

    def test_english_for_ambiguous(self) -> None:
        result = _heuristic_language_detect("hello")
        assert result.language == "en"

    def test_english_for_empty(self) -> None:
        result = _heuristic_language_detect("")
        assert result.language == "en"

    def test_code_switching_fr_sw(self) -> None:
        result = _heuristic_language_detect("Bonjour habari nataka mon solde tafadhali")
        assert result.code_switching
        assert result.secondary_language is not None

    def test_confidence_not_above_one(self) -> None:
        result = _heuristic_language_detect(
            "Bonjour je veux mon solde combien frais transfert envoi argent"
        )
        assert result.confidence <= 1.0

    def test_result_structure(self) -> None:
        result = _heuristic_language_detect("Test message")
        assert hasattr(result, "language")
        assert hasattr(result, "confidence")
        assert hasattr(result, "code_switching")
        assert hasattr(result, "secondary_language")
