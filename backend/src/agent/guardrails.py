"""Input guardrails for prompt injection and PII detection.

These guardrails FLAG suspicious input rather than hard-blocking.
The agent (via system prompt) handles refusal gracefully.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GuardrailResult:
    """Result of running guardrail checks on user input."""

    safe: bool
    injection_detected: bool
    pii_detected: bool
    flags: tuple[str, ...]


# Compiled regex patterns for prompt injection detection
_INJECTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"ignore\s+(your|all|previous)\s+(instructions|rules|prompt)", re.IGNORECASE),
     "instruction_override"),
    (re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
     "role_reassignment"),
    (re.compile(r"(reveal|show|print|output)\s+(your|the)\s+(system\s+)?(prompt|instructions|rules)",
                re.IGNORECASE),
     "prompt_extraction"),
    (re.compile(r"forget\s+(everything|all|your)\s*(you|instructions|rules)?", re.IGNORECASE),
     "memory_wipe"),
    (re.compile(r"(pretend|act\s+as\s+if|imagine)\s+(you\s+are|that)", re.IGNORECASE),
     "role_play_attack"),
    (re.compile(r"(jailbreak|bypass|override)\s*(the|your|safety|filter)?", re.IGNORECASE),
     "jailbreak_attempt"),
    (re.compile(r"system\s*:\s*", re.IGNORECASE),
     "system_prompt_injection"),
    (re.compile(r"<\s*(system|admin|root)\s*>", re.IGNORECASE),
     "xml_injection"),
    (re.compile(r"do\s+not\s+follow\s+(your|the|any)\s+(rules|guidelines|instructions)",
                re.IGNORECASE),
     "rule_bypass"),
]

# PII detection patterns
_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Credit card numbers (basic pattern)
    (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
     "credit_card_number"),
    # National ID numbers (various formats)
    (re.compile(r"\b\d{10,13}\b"),
     "potential_id_number"),
    # Email addresses
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
     "email_address"),
    # Passwords or secrets being shared
    (re.compile(r"(my\s+)?(password|pin|secret|code)\s+(is|=|:)\s+\S+", re.IGNORECASE),
     "shared_credential"),
]


def check_guardrails(message: str) -> GuardrailResult:
    """Run guardrail checks on a user message.

    Returns a GuardrailResult indicating whether the message is safe
    and what flags were triggered.
    """
    flags: list[str] = []

    # Check injection patterns
    injection_detected = False
    for pattern, flag_name in _INJECTION_PATTERNS:
        if pattern.search(message):
            flags.append(f"injection:{flag_name}")
            injection_detected = True

    # Check PII patterns
    pii_detected = False
    for pattern, flag_name in _PII_PATTERNS:
        if pattern.search(message):
            flags.append(f"pii:{flag_name}")
            pii_detected = True

    safe = not injection_detected
    return GuardrailResult(
        safe=safe,
        injection_detected=injection_detected,
        pii_detected=pii_detected,
        flags=tuple(flags),
    )
