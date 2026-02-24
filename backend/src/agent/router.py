"""Language detection for incoming user messages.

Uses an LLM via pydantic-ai for fast, accurate detection with a keyword-based heuristic fallback.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Keyword sets for heuristic fallback
_FR_MARKERS = frozenset({
    "bonjour", "salut", "merci", "combien", "solde", "compte", "envoi",
    "envoyer", "frais", "paiement", "retrait", "depot", "transfert",
    "aide", "probleme", "quel", "quelle", "comment", "pourquoi",
    "oui", "non", "s'il", "svp", "je", "mon", "mes", "une", "des",
    "facture", "argent", "agent", "numero", "recevoir", "dernier",
    "derniere", "transactions", "montant",
})

_SW_MARKERS = frozenset({
    "habari", "mambo", "sawa", "asante", "nataka", "salio", "akaunti",
    "tuma", "pesa", "malipo", "ada", "msaada", "tatizo", "kiasi",
    "ndiyo", "hapana", "tafadhali", "shukrani", "nini", "vipi",
    "wapi", "lini", "kwa", "yangu", "yako", "muamala", "kutuma",
    "kupokea", "salio", "wakala", "nambari", "simu",
})


@dataclass(frozen=True)
class LanguageDetectionResult:
    """Result of language detection."""

    language: str  # "en", "fr", "sw"
    confidence: float  # 0.0 - 1.0
    code_switching: bool
    secondary_language: str | None


def _heuristic_language_detect(message: str) -> LanguageDetectionResult:
    """Keyword-based language detection as a fast fallback.

    Counts marker word matches for each language and picks the best.
    """
    words = set(message.lower().split())

    fr_hits = len(words & _FR_MARKERS)
    sw_hits = len(words & _SW_MARKERS)

    total_words = max(len(words), 1)
    fr_ratio = fr_hits / total_words
    sw_ratio = sw_hits / total_words

    # Detect code-switching: significant presence of two languages
    code_switching = False
    secondary: str | None = None

    if fr_hits >= 2 and sw_hits >= 1:
        code_switching = True
        if fr_ratio > sw_ratio:
            secondary = "sw"
        else:
            secondary = "fr"
    elif fr_hits >= 1 and sw_hits >= 2:
        code_switching = True
        secondary = "fr" if sw_ratio > fr_ratio else "sw"

    if sw_hits > fr_hits and sw_hits >= 2:
        return LanguageDetectionResult(
            language="sw",
            confidence=min(sw_ratio * 3, 0.9),
            code_switching=code_switching,
            secondary_language=secondary,
        )
    elif fr_hits > sw_hits and fr_hits >= 1:
        return LanguageDetectionResult(
            language="fr",
            confidence=min(fr_ratio * 3, 0.9),
            code_switching=code_switching,
            secondary_language=secondary,
        )
    elif code_switching and fr_hits > 0 and sw_hits > 0:
        # Equal presence of both languages — pick dominant or default to French
        dominant = "fr" if fr_hits >= sw_hits else "sw"
        other = "sw" if dominant == "fr" else "fr"
        return LanguageDetectionResult(
            language=dominant,
            confidence=min(max(fr_ratio, sw_ratio) * 2, 0.7),
            code_switching=True,
            secondary_language=other,
        )
    else:
        # Default to English
        return LanguageDetectionResult(
            language="en",
            confidence=0.5,
            code_switching=False,
            secondary_language=None,
        )


async def detect_language(
    message: str,
    timeout_s: float = 2.0,
    model: str = "anthropic:claude-haiku-4-5-20241022",
) -> LanguageDetectionResult:
    """Detect the language of a user message using an LLM via pydantic-ai.

    Falls back to heuristic detection if the API call fails or times out.

    Args:
        message: The user message to analyze.
        timeout_s: Timeout in seconds for the API call.
        model: Model to use for language detection (provider:model format).
    """
    import asyncio

    try:
        from pydantic_ai import ModelRequest
        from pydantic_ai.direct import model_request
        from pydantic_ai.settings import ModelSettings

        prompt = (
            "Detect the language of this message. Respond with ONLY a JSON object "
            "(no markdown, no explanation):\n"
            '{"language": "en"|"fr"|"sw", "confidence": 0.0-1.0, '
            '"code_switching": true|false, "secondary_language": "en"|"fr"|"sw"|null}\n\n'
            f"Message: {message}"
        )

        response = await asyncio.wait_for(
            model_request(
                model,
                [ModelRequest.user_text_prompt(prompt)],
                model_settings=ModelSettings(max_tokens=100),
            ),
            timeout=timeout_s,
        )

        import json

        text = str(response.parts[0].content).strip()
        # Handle potential markdown code blocks
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        data = json.loads(text)

        lang = str(data.get("language", "en")).lower()
        if lang not in ("en", "fr", "sw"):
            lang = "en"

        return LanguageDetectionResult(
            language=lang,
            confidence=float(data.get("confidence", 0.8)),
            code_switching=bool(data.get("code_switching", False)),
            secondary_language=data.get("secondary_language"),
        )

    except asyncio.TimeoutError:
        logger.warning("Language detection timed out, using heuristic fallback")
        return _heuristic_language_detect(message)
    except Exception:
        logger.warning("Language detection failed, using heuristic fallback", exc_info=True)
        return _heuristic_language_detect(message)
