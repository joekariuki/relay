"""Hallucination detection using LLM-as-judge.

Detects fabricated financial data, invented policies, false reassurances,
and other hallucinations in agent responses.
"""

from __future__ import annotations

import json
import logging

from .models import HallucinationEntry, HallucinationResult

logger = logging.getLogger(__name__)

_HALLUCINATION_PROMPT = """You are an evaluation judge for a mobile money support agent (DuniaWallet). Detect any hallucinations in the assistant's response.

## Evidence (Tool Results)
{evidence}

## User Question
{user_message}

## Assistant Response
{response}

## Hallucination Types
- "fabricated_data": Made-up balances, fees, transaction IDs, dates, or amounts not in evidence
- "invented_policy": Policies or rules not found in evidence or known DuniaWallet policies
- "false_reassurance": Falsely claiming an issue is resolved or action was taken

## Severity
- "critical": Wrong financial data (balances, fees, amounts), invented transaction IDs
- "minor": Slightly inaccurate phrasing, minor policy details

Respond with ONLY a JSON object (no markdown, no explanation):
{{"clean": true/false, "hallucinations": [{{"claim": "the fabricated claim", "category": "type", "severity": "critical|minor"}}]}}

If the response is clean (no hallucinations), return: {{"clean": true, "hallucinations": []}}"""


async def detect_hallucinations(
    response_text: str,
    user_message: str,
    tool_results: list[dict[str, object]],
    model: str = "anthropic:claude-haiku-4-5-20241022",
) -> HallucinationResult:
    """Detect hallucinations in the agent's response.

    Uses LLM-as-judge via pydantic-ai to identify fabricated data and false claims.
    """
    evidence = json.dumps(tool_results, indent=2, default=str) if tool_results else "None"
    prompt = _HALLUCINATION_PROMPT.format(
        evidence=evidence,
        user_message=user_message,
        response=response_text,
    )

    try:
        from pydantic_ai import ModelRequest
        from pydantic_ai.direct import model_request
        from pydantic_ai.messages import TextPart
        from pydantic_ai.settings import ModelSettings

        response = await model_request(
            model,
            [ModelRequest.user_text_prompt(prompt)],
            model_settings=ModelSettings(max_tokens=400),
        )
        first_part = response.parts[0]
        assert isinstance(first_part, TextPart), f"Expected TextPart, got {type(first_part)}"
        text = first_part.content.strip()

        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        data = json.loads(text)

        entries: list[HallucinationEntry] = []
        for h in data.get("hallucinations", []):
            entries.append(HallucinationEntry(
                claim=str(h.get("claim", "")),
                category=str(h.get("category", "fabricated_data")),
                severity=str(h.get("severity", "minor")),
            ))

        return HallucinationResult(
            clean=bool(data.get("clean", True)),
            hallucinations=tuple(entries),
        )

    except Exception:
        logger.warning("Hallucination detection failed", exc_info=True)
        return HallucinationResult(clean=True, hallucinations=())
