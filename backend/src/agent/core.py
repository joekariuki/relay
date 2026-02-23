"""Core agent orchestration loop.

Pipeline: guardrails -> language detection -> prompt selection -> Claude tool-use loop -> response.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from src.knowledge.models import AgentResponse, Language, ToolCallRecord

from .guardrails import check_guardrails
from .prompts import get_system_prompt
from .router import LanguageDetectionResult, detect_language, _heuristic_language_detect
from .tools import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger(__name__)


def _language_code_to_enum(code: str) -> Language:
    """Convert a language code string to the Language enum."""
    mapping = {"en": Language.EN, "fr": Language.FR, "sw": Language.SW}
    return mapping.get(code.lower(), Language.EN)


async def process_message(
    message: str,
    account_id: str = "acc_001",
    language_hint: str | None = None,
    client: object | None = None,
) -> AgentResponse:
    """Process a user message through the full agent pipeline.

    Args:
        message: The user's message text.
        account_id: The DuniaWallet account ID for context.
        language_hint: Optional language hint ("en", "fr", "sw").
        client: Optional Anthropic AsyncAnthropic client. Created if not provided.

    Returns:
        An AgentResponse with the response text, tools used, and metadata.
    """
    latency: dict[str, float] = {}
    tools_used: list[ToolCallRecord] = []
    metadata: dict[str, object] = {}

    # === Stage 1: Guardrails ===
    t0 = time.perf_counter()
    guardrail_result = check_guardrails(message)
    latency["guardrails_ms"] = (time.perf_counter() - t0) * 1000

    metadata["guardrail_flags"] = guardrail_result.flags
    metadata["guardrail_safe"] = guardrail_result.safe

    if guardrail_result.injection_detected:
        logger.warning(
            "Injection detected in message",
            extra={"flags": guardrail_result.flags},
        )

    # === Stage 2: Language Detection ===
    t1 = time.perf_counter()
    if language_hint and language_hint in ("en", "fr", "sw"):
        lang_result = LanguageDetectionResult(
            language=language_hint,
            confidence=1.0,
            code_switching=False,
            secondary_language=None,
        )
    elif client is not None:
        from src.config import get_settings

        settings = get_settings()
        lang_result = await detect_language(
            client,
            message,
            timeout_s=settings.language_detection_timeout_s,
            model=settings.language_detection_model,
        )
    else:
        lang_result = _heuristic_language_detect(message)

    latency["language_detection_ms"] = (time.perf_counter() - t1) * 1000
    metadata["language_detected"] = lang_result.language
    metadata["language_confidence"] = lang_result.confidence
    metadata["code_switching"] = lang_result.code_switching

    # === Stage 3: Build Messages ===
    system_prompt = get_system_prompt(lang_result.language)
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": message},
    ]

    # === Stage 4: Agent Loop ===
    t2 = time.perf_counter()

    try:
        from anthropic import AsyncAnthropic
        from src.config import get_settings

        settings = get_settings()

        if client is None:
            if not settings.anthropic_api_key:
                return AgentResponse(
                    response_text=(
                        "I'm sorry, the service is temporarily unavailable. "
                        "Please try again later."
                    ),
                    language_detected=_language_code_to_enum(lang_result.language),
                    tools_used=tools_used,
                    groundedness_score=None,
                    latency_ms=latency,
                    metadata=metadata,
                )
            client = AsyncAnthropic(api_key=settings.anthropic_api_key)

        response_text = await _run_tool_loop(
            client=client,
            system_prompt=system_prompt,
            messages=messages,
            tools_used=tools_used,
            account_id=account_id,
            model=settings.agent_model,
            max_tokens=settings.agent_max_tokens,
            max_rounds=settings.agent_max_tool_rounds,
        )

    except ImportError:
        logger.error("anthropic package not available")
        response_text = (
            "I'm sorry, the service is temporarily unavailable. Please try again later."
        )
    except Exception:
        logger.error("Agent processing failed", exc_info=True)
        response_text = (
            "I'm sorry, I encountered an error processing your request. "
            "Please try again or contact support."
        )

    latency["agent_processing_ms"] = (time.perf_counter() - t2) * 1000
    latency["total_ms"] = (time.perf_counter() - t0) * 1000

    return AgentResponse(
        response_text=response_text,
        language_detected=_language_code_to_enum(lang_result.language),
        tools_used=tools_used,
        groundedness_score=None,
        latency_ms=latency,
        metadata=metadata,
    )


async def _run_tool_loop(
    client: Any,
    system_prompt: str,
    messages: list[dict[str, Any]],
    tools_used: list[ToolCallRecord],
    account_id: str,
    model: str,
    max_tokens: int,
    max_rounds: int,
) -> str:
    """Run the Claude tool-use loop for up to max_rounds iterations.

    Returns the final text response from the assistant.
    """
    for round_num in range(max_rounds):
        logger.debug("Tool-use round %d/%d", round_num + 1, max_rounds)

        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        # Check if we got tool use or just text
        if response.stop_reason == "end_turn" or response.stop_reason != "tool_use":
            # Extract text from response
            return _extract_text(response)

        # Process tool calls
        tool_results: list[dict[str, Any]] = []
        for block in response.content:
            if block.type == "tool_use":
                # Inject account_id if the tool expects it but LLM didn't provide
                tool_args = dict(block.input) if isinstance(block.input, dict) else {}
                if "account_id" in _get_tool_required_params(block.name):
                    tool_args.setdefault("account_id", account_id)

                record = execute_tool(block.name, tool_args)
                tools_used.append(record)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(record.result),
                })

        # Add assistant's response and tool results to conversation
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    # If we exhausted all rounds, get a final response without tools
    logger.warning("Exhausted %d tool-use rounds", max_rounds)
    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
    )
    return _extract_text(response)


def _extract_text(response: Any) -> str:
    """Extract text content from a Claude API response."""
    parts: list[str] = []
    for block in response.content:
        if hasattr(block, "text"):
            parts.append(block.text)
    return "\n".join(parts) if parts else "I'm sorry, I couldn't generate a response."


def _get_tool_required_params(tool_name: str) -> set[str]:
    """Get required parameters for a tool by name."""
    for tool in TOOL_DEFINITIONS:
        if tool["name"] == tool_name:
            return set(tool["input_schema"].get("required", []))
    return set()
