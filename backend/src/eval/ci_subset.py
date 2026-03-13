"""Critical eval cases for CI pipeline.

Curated subset of 20 high-priority test cases run on every PR.
Covers core functionality across all major categories to catch regressions fast.
"""

from __future__ import annotations

# 20 critical test case IDs covering all major categories:
# - 3 balance (core functionality)
# - 2 transactions
# - 2 fees
# - 1 dispute
# - 2 multilingual (French + Swahili)
# - 1 code switching
# - 3 safety (injection, out-of-scope, financial advice)
# - 1 low literacy
# - 2 international (new pan-African functionality)
# - 2 multi-currency
# - 1 pan-African
CI_CRITICAL_CASE_IDS: set[str] = {
    # Balance
    "bal_001",  # Basic balance check (English, acc_001)
    "bal_003",  # Balance check for a different account
    "bal_009",  # Balance for WAEMU country account
    # Transactions
    "txn_001",  # Recent transactions
    "txn_005",  # Transaction lookup by recipient
    # Fees
    "fee_001",  # Domestic fee calculation
    "fee_003",  # International WAEMU fee
    # Disputes
    "dis_001",  # Dispute filing
    # Multilingual
    "fr_001",   # French balance inquiry
    "sw_001",   # Swahili balance inquiry
    # Code switching
    "cs_001",   # French-English code switching
    # Safety
    "saf_001",  # Prompt injection attempt
    "saf_003",  # System prompt extraction
    "oos_001",  # Out-of-scope question
    # Low literacy
    "low_001",  # Simplified language
    # International
    "intl_001", # UK to Nigeria transfer fees
    "intl_005", # Cross-Africa corridor (Kenya to Tanzania)
    # Multi-currency
    "mcur_001", # NGN balance check
    "mcur_005", # Exchange rate query
    # Pan-African
    "pan_001",  # Pan-African agent search
}

# CI threshold gates — eval must meet these to pass
CI_THRESHOLDS = {
    "tool_correctness": 0.85,   # 85% of tools called correctly
    "must_contain_pass": 0.90,  # 90% of must-contain checks pass
    "compliance_pass": 1.0,     # 100% compliance (no violations)
}
