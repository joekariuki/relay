"""Data models for the evaluation framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EvalCategory(str, Enum):
    """Categories for evaluation test cases."""

    BALANCE = "balance_inquiry"
    TRANSACTIONS = "transaction_history"
    FEES = "fee_calculation"
    DISPUTES = "disputes"
    MULTILINGUAL_FR = "multilingual_fr"
    MULTILINGUAL_SW = "multilingual_sw"
    CODE_SWITCHING = "code_switching"
    SAFETY = "safety_injection"
    OUT_OF_SCOPE = "out_of_scope"
    LOW_LITERACY = "low_literacy"


@dataclass(frozen=True)
class TestCase:
    """A single evaluation test case."""

    id: str
    category: EvalCategory
    message: str
    account_id: str
    language: str  # Expected response language: "en", "fr", "sw"
    expected_tools: tuple[str, ...]  # Tools that should be called
    must_contain: tuple[str, ...]  # Strings that must appear in response
    must_not_contain: tuple[str, ...]  # Strings that must NOT appear in response
    expect_refusal: bool  # Whether the agent should refuse/redirect
    ground_truth: str  # Brief expected factual content
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroundednessResult:
    """Result of groundedness evaluation."""

    score: float  # 0.0 - 1.0
    grounded_claims: int
    ungrounded_claims: int
    contradictions: int
    reasoning: str


@dataclass(frozen=True)
class HallucinationEntry:
    """A single detected hallucination."""

    claim: str
    category: str  # "fabricated_data", "invented_policy", "false_reassurance"
    severity: str  # "critical", "minor"


@dataclass(frozen=True)
class HallucinationResult:
    """Result of hallucination detection."""

    clean: bool
    hallucinations: tuple[HallucinationEntry, ...]


@dataclass(frozen=True)
class ComplianceViolation:
    """A single compliance violation."""

    rule: str
    detail: str
    severity: str  # "critical", "warning"


@dataclass(frozen=True)
class ComplianceResult:
    """Result of compliance check."""

    compliant: bool
    violations: tuple[ComplianceViolation, ...]


@dataclass(frozen=True)
class LanguageResult:
    """Result of language quality evaluation."""

    correct_language: bool
    detected_language: str
    fluency_score: float  # 0.0 - 1.0
    issues: tuple[str, ...]


@dataclass(frozen=True)
class CaseResult:
    """Full evaluation result for a single test case."""

    test_case_id: str
    category: EvalCategory
    response_text: str
    tools_used: tuple[str, ...]
    tool_correctness: float  # 0.0 - 1.0
    must_contain_pass: bool
    must_not_contain_pass: bool
    refusal_correct: bool
    groundedness: GroundednessResult | None
    hallucination: HallucinationResult | None
    compliance: ComplianceResult | None
    language_quality: LanguageResult | None
    latency_ms: float
    error: str | None = None


@dataclass
class EvalReport:
    """Full evaluation report across all test cases."""

    total_cases: int
    passed_cases: int
    failed_cases: int
    error_cases: int
    overall_scores: dict[str, float]
    by_category: dict[str, dict[str, float]]
    case_results: list[CaseResult]
    metadata: dict[str, object] = field(default_factory=dict)
