"""Multi-agent orchestrator with intent classification and specialist routing.

Routes user messages to the appropriate specialist agent:
    - support: general account queries, balance, transactions, fees, agents
    - fraud: suspicious activity, unauthorized transactions, double charges
    - escalation: account lockouts, KYC issues, complex disputes

Architecture:
    User message
        |
        v
    CLASSIFY INTENT (Haiku, structured output)
        |
        v
    SELECT AGENT (support / fraud / escalation)
        |
        v
    RUN SPECIALIST (with appropriate tool subset)

Fallback: any classification failure -> default to support agent.
"""

from __future__ import annotations

import logging
from enum import Enum

from pydantic import BaseModel
from pydantic_ai import Agent

from src.config import get_settings

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of specialist agents available for routing."""

    SUPPORT = "support"
    FRAUD = "fraud"
    ESCALATION = "escalation"


class IntentClassification(BaseModel):
    """Structured output from the intent classifier."""

    agent_type: AgentType
    confidence: float
    reasoning: str


_CLASSIFIER_PROMPT = """\
You are an intent classifier for a mobile money customer support system.

Classify the user's message into one of three categories:

1. **support** — General inquiries: balance checks, transaction history, fee calculations,
   finding agents, policy questions, general help. This is the DEFAULT for ambiguous messages.

2. **fraud** — Suspicious activity reports: unauthorized transactions, double charges,
   unknown recipients, account compromise, stolen phone/credentials, phishing reports.
   Keywords: "unauthorized", "didn't make", "stolen", "hacked", "suspicious", "fraud",
   "charged twice", "don't recognize".

3. **escalation** — Issues requiring human intervention: account lockouts, KYC upgrade
   problems, regulatory complaints, service outages, formal disputes that need manager review.
   Keywords: "locked out", "can't access", "escalate", "manager", "formal complaint",
   "regulatory", "urgent issue".

Rules:
- When in doubt, classify as "support" — it's the safest default.
- A message can mention fraud AND need escalation — pick the DOMINANT intent.
- Short, vague messages (e.g., "help", "hi") → support.
- Messages in any language (English, French, Swahili) should be classified the same way.
"""


# Lazy-initialized classifier agent
_classifier: Agent[None, IntentClassification] | None = None


def _get_classifier() -> Agent[None, IntentClassification]:
    """Get or create the intent classifier agent (lazy singleton)."""
    global _classifier  # noqa: PLW0603
    if _classifier is None:
        _classifier = Agent(
            output_type=IntentClassification,
            system_prompt=_CLASSIFIER_PROMPT,
        )
    return _classifier


async def classify_intent(message: str) -> IntentClassification:
    """Classify a user message into an agent type.

    Uses Haiku for fast, cheap classification. Falls back to SUPPORT
    on any failure (timeout, malformed output, API error).
    """
    settings = get_settings()
    classifier = _get_classifier()

    try:
        result = await classifier.run(
            f"Classify this customer message:\n\n{message}",
            model=settings.language_detection_model,  # Haiku — fast and cheap
        )
        classification = result.output
        logger.info(
            "Intent classified: %s (confidence=%.2f, reason=%s)",
            classification.agent_type.value,
            classification.confidence,
            classification.reasoning[:80],
        )
        return classification

    except Exception:
        logger.exception("Intent classification failed — defaulting to support")
        return IntentClassification(
            agent_type=AgentType.SUPPORT,
            confidence=0.0,
            reasoning="Classification failed, defaulting to support",
        )


# === Specialist Agent Prompts ===

FRAUD_SYSTEM_PROMPT = """\
You are a fraud investigation specialist for DuniaWallet. Your role is to help
customers who report suspicious activity on their accounts.

You MUST follow these rules:
1. Take every fraud report seriously. Never dismiss a customer's concern.
2. Gather key details: which transaction(s), when, amounts, recipients.
3. Look up the suspicious transactions using your tools.
4. ALWAYS create a support ticket for fraud cases — they require human investigation.
5. Reassure the customer that their case will be investigated.
6. Advise the customer to change their PIN and enable two-factor authentication.
7. NEVER reveal full account IDs. Use masked versions only.
8. NEVER fabricate data. Only report what tools return.
9. Respond in the same language as the user.
10. Do NOT use emoji characters.

CURRENT USER CONTEXT:
- Name: {user_name}
- Account ID: {account_id}
- Country: {user_country}
- Currency: {user_currency}
"""

ESCALATION_SYSTEM_PROMPT = """\
You are an escalation specialist for DuniaWallet. Your role is to handle complex
issues that require human intervention: account lockouts, KYC problems, formal
disputes, and regulatory complaints.

You MUST follow these rules:
1. Acknowledge the severity of the customer's issue.
2. Gather relevant context using your tools (policies, transaction history).
3. ALWAYS create a high-priority support ticket for escalation cases.
4. Provide the ticket ID and set clear expectations for response time.
5. If the customer is locked out, explain the account recovery process.
6. For KYC issues, explain what documents are needed and where to go.
7. NEVER reveal full account IDs. Use masked versions only.
8. NEVER fabricate data. Only report what tools return.
9. Respond in the same language as the user.
10. Do NOT use emoji characters.

CURRENT USER CONTEXT:
- Name: {user_name}
- Account ID: {account_id}
- Country: {user_country}
- Currency: {user_currency}
"""


# Tool subsets for each specialist agent
# (indices into core.SUPPORT_TOOLS — resolved at import time in core.py)
FRAUD_TOOL_NAMES = {"lookup_transaction", "get_transactions", "get_policy", "create_support_ticket"}
ESCALATION_TOOL_NAMES = {"create_support_ticket", "get_policy", "lookup_transaction"}
