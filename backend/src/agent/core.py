"""Core agent orchestration loop.

Pipeline: guardrails -> language detection -> prompt selection -> pydantic-ai agent -> response.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from pydantic_ai import Agent, RunContext, UsageLimits
from pydantic_ai.settings import ModelSettings

from src.config import get_settings
from src.knowledge.accounts import get_account
from src.knowledge.models import AgentResponse, Language, ToolCallRecord

from .formatting import clean_response_text
from .guardrails import check_guardrails
from .prompts import get_system_prompt
from .router import LanguageDetectionResult, detect_language
from .tools import execute_tool

logger = logging.getLogger(__name__)


@dataclass
class AgentDeps:
    """Runtime dependencies injected into the agent via RunContext."""

    account_id: str
    language: str
    tool_records: list[ToolCallRecord] = field(default_factory=list)


# Module-level agent instance — model provided at run time via agent.run(model=...)
support_agent = Agent(
    deps_type=AgentDeps,
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
) -> AgentResponse:
    """Process a user message through the full agent pipeline.

    Args:
        message: The user's message text.
        account_id: The DuniaWallet account ID for context.
        language_hint: Optional language hint ("en", "fr", "sw").

    Returns:
        An AgentResponse with the response text, tools used, and metadata.
    """
    settings = get_settings()
    latency: dict[str, float] = {}
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
        )
        response_text = result.output

    except Exception:
        logger.error("Agent processing failed", exc_info=True)
        response_text = (
            "I'm sorry, I encountered an error processing your request. "
            "Please try again or contact support."
        )

    latency["agent_processing_ms"] = (time.perf_counter() - t2) * 1000
    latency["total_ms"] = (time.perf_counter() - t0) * 1000

    response_text = clean_response_text(response_text)

    return AgentResponse(
        response_text=response_text,
        language_detected=_language_code_to_enum(lang_result.language),
        tools_used=deps.tool_records,
        groundedness_score=None,
        latency_ms=latency,
        metadata=metadata,
    )
