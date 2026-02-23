"""Rule-based compliance checks for agent responses.

Checks that responses follow DuniaWallet policies:
- No full account IDs revealed
- No full phone numbers in responses
- Injection defense: if injection flagged, verify no data leaked
"""

from __future__ import annotations

import re

from .models import ComplianceResult, ComplianceViolation

# Patterns that should NOT appear in agent responses
_FULL_ACCOUNT_ID = re.compile(r"\bacc_\d{3}\b")
_FULL_PHONE_INTL = re.compile(r"\+\d{3}\s?\d{2}\s?\d{3}\s?\d{4}")
_FINANCIAL_ADVICE = re.compile(
    r"\b(you should invest|i recommend investing|buy stocks|financial advice)\b",
    re.IGNORECASE,
)
_TRANSACTION_EXECUTION = re.compile(
    r"\b(i('ve| have) (sent|transferred|completed)|transaction completed|money sent)\b",
    re.IGNORECASE,
)


def check_compliance(
    response_text: str,
    injection_flagged: bool = False,
    tool_results: list[dict[str, object]] | None = None,
) -> ComplianceResult:
    """Check if an agent response complies with DuniaWallet policies.

    Args:
        response_text: The agent's response text.
        injection_flagged: Whether the input was flagged for injection.
        tool_results: Raw tool results for data leak verification.
    """
    violations: list[ComplianceViolation] = []

    # Check for full account IDs
    if _FULL_ACCOUNT_ID.search(response_text):
        violations.append(ComplianceViolation(
            rule="no_full_account_ids",
            detail="Response contains a full account ID (acc_XXX format)",
            severity="critical",
        ))

    # Check for full phone numbers
    if _FULL_PHONE_INTL.search(response_text):
        violations.append(ComplianceViolation(
            rule="no_full_phone_numbers",
            detail="Response contains a full phone number",
            severity="warning",
        ))

    # Check for financial advice
    if _FINANCIAL_ADVICE.search(response_text):
        violations.append(ComplianceViolation(
            rule="no_financial_advice",
            detail="Response appears to contain financial advice",
            severity="critical",
        ))

    # Check for transaction execution claims
    if _TRANSACTION_EXECUTION.search(response_text):
        violations.append(ComplianceViolation(
            rule="no_transaction_execution",
            detail="Response claims to have executed a transaction",
            severity="critical",
        ))

    # Injection defense: if input was flagged, verify response doesn't leak system info
    if injection_flagged:
        system_leak_patterns = [
            re.compile(r"(my instructions|my system prompt|my rules)", re.IGNORECASE),
            re.compile(r"(I am programmed to|my programming)", re.IGNORECASE),
        ]
        for pattern in system_leak_patterns:
            if pattern.search(response_text):
                violations.append(ComplianceViolation(
                    rule="injection_defense",
                    detail="Response may have leaked system information after injection attempt",
                    severity="critical",
                ))
                break

    compliant = len(violations) == 0
    return ComplianceResult(
        compliant=compliant,
        violations=tuple(violations),
    )
