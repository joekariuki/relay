"""Core agent orchestration loop.

Pipeline: guardrails -> language detection -> prompt selection -> pydantic-ai agent -> response.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from pydantic_ai import Agent, RunContext, UsageLimits
from pydantic_ai.messages import ModelMessage
from pydantic_ai.settings import ModelSettings
from pydantic_graph import End

from src.config import get_settings
from src.knowledge.accounts import get_account
from src.knowledge.models import AgentResponse, Language, ToolCallRecord

from .formatting import clean_response_text
from .guardrails import check_guardrails
from .prompts import get_system_prompt
from .router import LanguageDetectionResult, detect_language
from .tools import execute_tool

logger = logging.getLogger(__name__)

# User-friendly status messages emitted via SSE while tools execute (per language)
_TOOL_STATUS_MESSAGES: dict[str, dict[str, str]] = {
    "check_balance": {
        "en": "Checking account balance",
        "fr": "Vérification du solde",
        "sw": "Kuangalia salio la akaunti",
    },
    "get_transactions": {
        "en": "Fetching recent transactions",
        "fr": "Récupération des transactions récentes",
        "sw": "Kupata miamala ya hivi karibuni",
    },
    "lookup_transaction": {
        "en": "Searching transactions",
        "fr": "Recherche de transactions",
        "sw": "Kutafuta miamala",
    },
    "calculate_fees": {
        "en": "Calculating transfer fees",
        "fr": "Calcul des frais de transfert",
        "sw": "Kukokotoa ada za uhamisho",
    },
    "find_agent": {
        "en": "Finding nearby agents",
        "fr": "Recherche d'agents à proximité",
        "sw": "Kutafuta mawakala wa karibu",
    },
    "get_policy": {
        "en": "Looking up service policies",
        "fr": "Consultation des politiques du service",
        "sw": "Kutafuta sera za huduma",
    },
    "create_support_ticket": {
        "en": "Creating support ticket",
        "fr": "Création d'un ticket d'assistance",
        "sw": "Kuunda tiketi ya msaada",
    },
}

_STAGE_STATUS_MESSAGES: dict[str, dict[str, str]] = {
    "analyzing": {
        "en": "Analyzing your request",
        "fr": "Analyse de votre demande",
        "sw": "Kuchambua ombi lako",
    },
    "preparing": {
        "en": "Preparing your response",
        "fr": "Préparation de votre réponse",
        "sw": "Kuandaa jibu lako",
    },
    "processing": {
        "en": "Processing",
        "fr": "Traitement en cours",
        "sw": "Inashughulikiwa",
    },
}


def _get_status(messages: dict[str, str], lang: str) -> str:
    return messages.get(lang, messages["en"])


@dataclass
class AgentDeps:
    """Runtime dependencies injected into the agent via RunContext."""

    account_id: str
    language: str
    tool_records: list[ToolCallRecord] = field(default_factory=list)


@dataclass
class StreamContext:
    """Mutable container populated by process_message_stream with the final message history."""

    all_messages: list[ModelMessage] = field(default_factory=list)


def _cap_message_history(messages: list[ModelMessage]) -> list[ModelMessage]:
    """Keep only the most recent message pairs to bound token usage.

    Preserves the first message (which contains the system prompt context)
    and the most recent N messages to avoid unbounded context growth.
    """
    settings = get_settings()
    max_messages = settings.session_max_history * 2
    if len(messages) <= max_messages:
        return messages
    return messages[:1] + messages[-(max_messages - 1):]


# Module-level agent instance — model provided at run time via agent.run(model=...)
support_agent = Agent(
    deps_type=AgentDeps,
    history_processors=[_cap_message_history],
)


@support_agent.system_prompt
def build_system_prompt(ctx: RunContext[AgentDeps]) -> str:
    """Build the system prompt with user context and language."""
    account = get_account(ctx.deps.account_id)
    return get_system_prompt(
        ctx.deps.language,
        user_name=account.name if account else "Unknown",
        account_id=ctx.deps.account_id,
        user_country=account.country if account else "Unknown",
    )


# === Tool Definitions (registered via @agent.tool) ===


@support_agent.tool
async def check_balance(ctx: RunContext[AgentDeps]) -> dict[str, object]:
    """Check the current balance of the user's DuniaWallet account.
    Returns balance in CFA Francs, account holder name, and KYC tier.
    The account ID is partially masked for security."""
    record = execute_tool("check_balance", {"account_id": ctx.deps.account_id})
    ctx.deps.tool_records.append(record)
    return record.result


@support_agent.tool
async def get_transactions(ctx: RunContext[AgentDeps], limit: int = 5) -> dict[str, object]:
    """Get recent transactions for the user's account, sorted by most recent first.

    Args:
        limit: Maximum number of transactions to return (1-20, default 5).
    """
    record = execute_tool("get_transactions", {
        "account_id": ctx.deps.account_id,
        "limit": limit,
    })
    ctx.deps.tool_records.append(record)
    return record.result


@support_agent.tool
async def lookup_transaction(ctx: RunContext[AgentDeps], query: str) -> dict[str, object]:
    """Search for specific transactions by transaction ID, recipient name, or description.

    Args:
        query: Search query - transaction ID, recipient name, or keyword.
    """
    record = execute_tool("lookup_transaction", {
        "account_id": ctx.deps.account_id,
        "query": query,
    })
    ctx.deps.tool_records.append(record)
    return record.result


@support_agent.tool
async def calculate_fees(
    ctx: RunContext[AgentDeps],
    amount: int,
    destination_country: str,
    currency: str = "XOF",
) -> dict[str, object]:
    """Calculate the transfer fee for a given amount and destination.

    Args:
        amount: Transfer amount in CFA Francs.
        destination_country: Destination - 'domestic' for local, or country name.
        currency: Currency code (default 'XOF').
    """
    record = execute_tool("calculate_fees", {
        "amount": amount,
        "currency": currency,
        "destination_country": destination_country,
    })
    ctx.deps.tool_records.append(record)
    return record.result


@support_agent.tool
async def find_agent(ctx: RunContext[AgentDeps], location: str) -> dict[str, object]:
    """Find DuniaWallet cash-in/cash-out agents near a given location.

    Args:
        location: City, neighborhood, or area name to search.
    """
    record = execute_tool("find_agent", {"location": location})
    ctx.deps.tool_records.append(record)
    return record.result


@support_agent.tool
async def get_policy(ctx: RunContext[AgentDeps], topic: str) -> dict[str, object]:
    """Retrieve a DuniaWallet service policy by topic.

    Args:
        topic: Policy topic key (e.g., transaction_limits, fees, kyc_verification).
    """
    record = execute_tool("get_policy", {"topic": topic})
    ctx.deps.tool_records.append(record)
    return record.result


@support_agent.tool
async def create_support_ticket(
    ctx: RunContext[AgentDeps],
    category: str,
    summary: str,
    priority: str = "medium",
) -> dict[str, object]:
    """Create a support ticket for issues requiring human intervention.

    Args:
        category: Ticket category (dispute, account_issue, transaction_problem, kyc_upgrade, other).
        summary: Brief description of the issue.
        priority: Ticket priority level (low, medium, high, urgent).
    """
    record = execute_tool("create_support_ticket", {
        "account_id": ctx.deps.account_id,
        "category": category,
        "summary": summary,
        "priority": priority,
    })
    ctx.deps.tool_records.append(record)
    return record.result


def _language_code_to_enum(code: str) -> Language:
    """Convert a language code string to the Language enum."""
    mapping = {"en": Language.EN, "fr": Language.FR, "sw": Language.SW}
    return mapping.get(code.lower(), Language.EN)


async def process_message(
    message: str,
    account_id: str = "acc_001",
    language_hint: str | None = None,
    message_history: list[ModelMessage] | None = None,
) -> tuple[AgentResponse, list[ModelMessage]]:
    """Process a user message through the full agent pipeline.

    Args:
        message: The user's message text.
        account_id: The DuniaWallet account ID for context.
        language_hint: Optional language hint ("en", "fr", "sw").
        message_history: Prior conversation messages for multi-turn context.

    Returns:
        A tuple of (AgentResponse, updated message history).
    """
    settings = get_settings()
    latency: dict[str, float] = {}
    metadata: dict[str, object] = {}
    all_messages: list[ModelMessage] = []

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
    else:
        lang_result = await detect_language(
            message,
            timeout_s=settings.language_detection_timeout_s,
            model=settings.language_detection_model,
        )

    latency["language_detection_ms"] = (time.perf_counter() - t1) * 1000
    metadata["language_detected"] = lang_result.language
    metadata["language_confidence"] = lang_result.confidence
    metadata["code_switching"] = lang_result.code_switching

    # === Stage 3: Run Agent ===
    t2 = time.perf_counter()
    deps = AgentDeps(account_id=account_id, language=lang_result.language)

    try:
        result = await support_agent.run(
            message,
            deps=deps,
            model=settings.agent_model,
            model_settings=ModelSettings(max_tokens=settings.agent_max_tokens),
            usage_limits=UsageLimits(
                request_limit=settings.agent_max_tool_rounds + 1,
            ),
            message_history=message_history or [],
        )
        response_text = result.output
        all_messages = result.all_messages()

    except Exception:
        logger.error("Agent processing failed", exc_info=True)
        response_text = (
            "I'm sorry, I encountered an error processing your request. "
            "Please try again or contact support."
        )

    latency["agent_processing_ms"] = (time.perf_counter() - t2) * 1000
    latency["total_ms"] = (time.perf_counter() - t0) * 1000

    response_text = clean_response_text(response_text)

    return (
        AgentResponse(
            response_text=response_text,
            language_detected=_language_code_to_enum(lang_result.language),
            tools_used=deps.tool_records,
            groundedness_score=None,
            latency_ms=latency,
            metadata=metadata,
        ),
        all_messages,
    )


def _sse_event(event: str, data: dict[str, object]) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def process_message_stream(
    message: str,
    account_id: str = "acc_001",
    language_hint: str | None = None,
    message_history: list[ModelMessage] | None = None,
    stream_context: StreamContext | None = None,
) -> AsyncIterator[str]:
    """Process a user message and stream the response as SSE events.

    Yields SSE-formatted strings:
        - event: text_delta — incremental text chunks
        - event: done — final metadata (language, tools, latency)
        - event: error — on failure

    Args:
        message: The user's message text.
        account_id: The DuniaWallet account ID for context.
        language_hint: Optional language hint ("en", "fr", "sw").
        message_history: Prior conversation messages for multi-turn context.
        stream_context: If provided, populated with the final message history
            after streaming completes (for the caller to persist).
    """
    settings = get_settings()
    latency: dict[str, float] = {}
    metadata: dict[str, object] = {}

    try:
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
        else:
            lang_result = await detect_language(
                message,
                timeout_s=settings.language_detection_timeout_s,
                model=settings.language_detection_model,
            )

        latency["language_detection_ms"] = (time.perf_counter() - t1) * 1000

        # === Stage 3: Stream Agent Response ===
        t2 = time.perf_counter()
        deps = AgentDeps(account_id=account_id, language=lang_result.language)

        lang = lang_result.language
        yield _sse_event("status", {"message": _get_status(_STAGE_STATUS_MESSAGES["analyzing"], lang)})

        accumulated_text = ""
        pending_chunks: list[str] = []
        async with support_agent.iter(
            message,
            deps=deps,
            model=settings.agent_model,
            model_settings=ModelSettings(max_tokens=settings.agent_max_tokens),
            usage_limits=UsageLimits(
                request_limit=settings.agent_max_tool_rounds + 1,
            ),
            message_history=message_history or [],
        ) as agent_run:
            node = agent_run.next_node
            while not isinstance(node, End):
                if support_agent.is_model_request_node(node):
                    pending_chunks = []
                    async with node.stream(agent_run.ctx) as stream:
                        async for chunk in stream.stream_text(delta=True, debounce_by=None):
                            pending_chunks.append(chunk)
                elif support_agent.is_call_tools_node(node):
                    for tc in node.model_response.tool_calls:
                        tool_msgs = _TOOL_STATUS_MESSAGES.get(tc.tool_name)
                        msg = _get_status(tool_msgs, lang) if tool_msgs else _get_status(_STAGE_STATUS_MESSAGES["processing"], lang)
                        yield _sse_event("status", {"message": msg})
                node = await agent_run.next(node)

            if stream_context is not None:
                stream_context.all_messages = agent_run.result.all_messages()

        yield _sse_event("status", {"message": _get_status(_STAGE_STATUS_MESSAGES["preparing"], lang)})
        accumulated_text = clean_response_text("".join(pending_chunks))
        if accumulated_text:
            yield _sse_event("text_delta", {"chunk": accumulated_text})

        latency["agent_processing_ms"] = (time.perf_counter() - t2) * 1000
        latency["total_ms"] = (time.perf_counter() - t0) * 1000

        tools_info = [
            {
                "tool_name": t.tool_name,
                "arguments": t.arguments,
                "result": t.result,
                "duration_ms": t.duration_ms,
            }
            for t in deps.tool_records
        ]

        yield _sse_event("done", {
            "language_detected": lang_result.language,
            "tools_used": tools_info,
            "groundedness_score": None,
            "latency_ms": latency,
        })

    except Exception:
        logger.error("Streaming agent processing failed", exc_info=True)
        yield _sse_event("error", {
            "message": "I'm sorry, I encountered an error processing your request. "
            "Please try again or contact support.",
        })
