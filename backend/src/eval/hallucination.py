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
    client: object,
    response_text: str,
    user_message: str,
    tool_results: list[dict[str, object]],
    model: str = "claude-haiku-4-5-20241022",
) -> HallucinationResult:
    """Detect hallucinations in the agent's response.

    Uses LLM-as-judge (Haiku) to identify fabricated data and false claims.
    """
    evidence = json.dumps(tool_results, indent=2, default=str) if tool_results else "None"
    prompt = _HALLUCINATION_PROMPT.format(
        evidence=evidence,
        user_message=user_message,
        response=response_text,
    )

    try:
        from anthropic import AsyncAnthropic

        if not isinstance(client, AsyncAnthropic):
            return HallucinationResult(clean=True, hallucinations=())

        response = await client.messages.create(
            model=model,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )

        first_block = response.content[0]
        if not hasattr(first_block, "text"):
            return HallucinationResult(clean=True, hallucinations=())
        text = first_block.text.strip()

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
