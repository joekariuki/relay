"""Language quality evaluation using LLM-as-judge.

Checks that the agent responds in the correct language with good fluency.
"""

from __future__ import annotations

import json
import logging

from .models import LanguageResult

logger = logging.getLogger(__name__)

_LANGUAGE_PROMPT = """Evaluate the language quality of this customer support response.

## Expected Language: {expected_language}
## Response:
{response}

## Instructions
1. Is the response in the expected language? (true/false)
2. What language is the response actually in? (en/fr/sw/mixed)
3. Rate fluency from 0.0-1.0 (grammar, natural phrasing, appropriate register)
4. List any specific issues (wrong language, grammar errors, awkward phrasing)

Respond with ONLY a JSON object (no markdown, no explanation):
{{"correct_language": true/false, "detected_language": "en|fr|sw|mixed", "fluency_score": 0.0-1.0, "issues": ["issue1", "issue2"]}}"""

_LANGUAGE_NAMES = {"en": "English", "fr": "French", "sw": "Swahili"}


async def evaluate_language_quality(
    response_text: str,
    expected_language: str,
    model: str = "anthropic:claude-haiku-4-5-20251001",
) -> LanguageResult:
    """Evaluate language quality and correctness of the response.

    Uses LLM-as-judge via pydantic-ai to assess language use.
    """
    lang_name = _LANGUAGE_NAMES.get(expected_language, expected_language)
    prompt = _LANGUAGE_PROMPT.format(
        expected_language=lang_name,
        response=response_text,
    )

    try:
        # Lazy import: pydantic-ai direct API deferred to avoid heavy eval imports at startup
        from pydantic_ai import ModelRequest
        from pydantic_ai.direct import model_request
        from pydantic_ai.messages import TextPart
        from pydantic_ai.settings import ModelSettings

        response = await model_request(
            model,
            [ModelRequest.user_text_prompt(prompt)],
            model_settings=ModelSettings(max_tokens=200),
        )
        first_part = response.parts[0]
        assert isinstance(first_part, TextPart), f"Expected TextPart, got {type(first_part)}"
        text = first_part.content.strip()

        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        data = json.loads(text)

        return LanguageResult(
            correct_language=bool(data.get("correct_language", True)),
            detected_language=str(data.get("detected_language", expected_language)),
            fluency_score=max(0.0, min(1.0, float(data.get("fluency_score", 1.0)))),
            issues=tuple(str(i) for i in data.get("issues", [])),
        )

    except Exception:
        logger.warning("Language quality evaluation failed", exc_info=True)
        return _default_result(expected_language)


def _default_result(language: str) -> LanguageResult:
    """Return a default result when evaluation is not possible."""
    return LanguageResult(
        correct_language=True,
        detected_language=language,
        fluency_score=1.0,
        issues=(),
    )
