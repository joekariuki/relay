"""Groundedness scoring using LLM-as-judge.

Evaluates whether the agent's response is grounded in the tool results
(evidence), identifying unsupported claims and contradictions.
"""

from __future__ import annotations

import json
import logging

from .models import GroundednessResult

logger = logging.getLogger(__name__)

_GROUNDEDNESS_PROMPT = """You are an evaluation judge. Your task is to assess whether an AI assistant's response is grounded in the provided evidence (tool results).

## Evidence (Tool Results)
{evidence}

## Assistant Response
{response}

## Instructions
1. Identify every factual claim in the assistant's response (numbers, dates, names, statuses, etc.)
2. For each claim, check if it is supported by the evidence
3. Count: grounded claims (supported), ungrounded claims (not in evidence), contradictions (conflicts with evidence)
4. Calculate a score: grounded_claims / total_claims (0.0 to 1.0)

Respond with ONLY a JSON object (no markdown, no explanation):
{{"score": 0.0-1.0, "grounded_claims": N, "ungrounded_claims": N, "contradictions": N, "reasoning": "brief explanation"}}"""


async def score_groundedness(
    response_text: str,
    tool_results: list[dict[str, object]],
    model: str = "anthropic:claude-haiku-4-5-20251001",
) -> GroundednessResult:
    """Score how well the response is grounded in tool results.

    Uses LLM-as-judge via pydantic-ai to evaluate factual claims against evidence.
    """
    if not tool_results:
        return GroundednessResult(
            score=1.0,
            grounded_claims=0,
            ungrounded_claims=0,
            contradictions=0,
            reasoning="No tool results to ground against (informational response)",
        )

    evidence = json.dumps(tool_results, indent=2, default=str)
    prompt = _GROUNDEDNESS_PROMPT.format(evidence=evidence, response=response_text)

    try:
        # Lazy import: pydantic-ai direct API deferred to avoid heavy eval imports at startup
        from pydantic_ai import ModelRequest
        from pydantic_ai.direct import model_request
        from pydantic_ai.messages import TextPart
        from pydantic_ai.settings import ModelSettings

        response = await model_request(
            model,
            [ModelRequest.user_text_prompt(prompt)],
            model_settings=ModelSettings(max_tokens=300),
        )
        first_part = response.parts[0]
        assert isinstance(first_part, TextPart), f"Expected TextPart, got {type(first_part)}"
        text = first_part.content.strip()

        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        data = json.loads(text)

        return GroundednessResult(
            score=max(0.0, min(1.0, float(data.get("score", 0.0)))),
            grounded_claims=int(data.get("grounded_claims", 0)),
            ungrounded_claims=int(data.get("ungrounded_claims", 0)),
            contradictions=int(data.get("contradictions", 0)),
            reasoning=str(data.get("reasoning", "")),
        )

    except Exception:
        logger.warning("Groundedness scoring failed", exc_info=True)
        return _default_result("Scoring failed due to error")


def _default_result(reason: str) -> GroundednessResult:
    """Return a default result when scoring is not possible."""
    return GroundednessResult(
        score=0.0,
        grounded_claims=0,
        ungrounded_claims=0,
        contradictions=0,
        reasoning=reason,
    )
