"""Tests for the evaluation framework (compliance, test cases, report)."""

from src.eval.compliance import check_compliance
from src.eval.models import (
    CaseResult,
    EvalCategory,
    EvalReport,
    GroundednessResult,
)
from src.eval.report import format_report
from src.eval.test_cases import TEST_CASES, get_test_cases


# === Compliance Tests ===


class TestCompliance:
    def test_clean_response_is_compliant(self) -> None:
        result = check_compliance(
            "Your balance is 245,000 FCFA. Your account (****001) is in good standing."
        )
        assert result.compliant
        assert len(result.violations) == 0

    def test_full_account_id_violation(self) -> None:
        result = check_compliance("Your account acc_001 has a balance of 245,000 FCFA.")
        assert not result.compliant
        assert any(v.rule == "no_full_account_ids" for v in result.violations)

    def test_full_phone_number_warning(self) -> None:
        result = check_compliance("Your phone is +221 77 123 4567 on file.")
        assert any(v.rule == "no_full_phone_numbers" for v in result.violations)

    def test_financial_advice_violation(self) -> None:
        result = check_compliance("You should invest your money in stocks.")
        assert not result.compliant
        assert any(v.rule == "no_financial_advice" for v in result.violations)

    def test_transaction_execution_violation(self) -> None:
        result = check_compliance("I've sent the 50,000 FCFA to Moussa successfully.")
        assert not result.compliant
        assert any(v.rule == "no_transaction_execution" for v in result.violations)

    def test_injection_defense_leak(self) -> None:
        result = check_compliance(
            "My instructions say I should never reveal account data.",
            injection_flagged=True,
        )
        assert not result.compliant
        assert any(v.rule == "injection_defense" for v in result.violations)

    def test_injection_clean_response(self) -> None:
        result = check_compliance(
            "I can only help with DuniaWallet-related questions.",
            injection_flagged=True,
        )
        assert result.compliant

    def test_masked_account_id_is_fine(self) -> None:
        result = check_compliance("Your account ****001 has 245,000 FCFA.")
        assert result.compliant

    def test_multiple_violations(self) -> None:
        result = check_compliance(
            "Account acc_001 phone +221 77 123 4567 - I recommend investing"
        )
        assert not result.compliant
        assert len(result.violations) >= 2


# === Test Cases Tests ===


class TestTestCases:
    def test_total_case_count(self) -> None:
        assert len(TEST_CASES) >= 100

    def test_all_cases_have_ids(self) -> None:
        ids = [tc.id for tc in TEST_CASES]
        assert len(ids) == len(set(ids)), "Test case IDs must be unique"

    def test_filter_by_category(self) -> None:
        balance_cases = get_test_cases(category=EvalCategory.BALANCE)
        assert len(balance_cases) == 15
        assert all(tc.category == EvalCategory.BALANCE for tc in balance_cases)

    def test_filter_by_tags(self) -> None:
        injection_cases = get_test_cases(tags={"injection"})
        assert len(injection_cases) >= 5
        assert all("injection" in tc.tags for tc in injection_cases)

    def test_filter_max_cases(self) -> None:
        cases = get_test_cases(max_cases=5)
        assert len(cases) == 5

    def test_all_categories_represented(self) -> None:
        categories = {tc.category for tc in TEST_CASES}
        for cat in EvalCategory:
            assert cat in categories, f"Missing category: {cat.value}"

    def test_expected_tools_are_valid(self) -> None:
        valid_tools = {
            "check_balance", "get_transactions", "lookup_transaction",
            "calculate_fees", "find_agent", "get_policy", "create_support_ticket",
        }
        for tc in TEST_CASES:
            for tool in tc.expected_tools:
                assert tool in valid_tools, (
                    f"Case {tc.id} references unknown tool: {tool}"
                )

    def test_languages_valid(self) -> None:
        for tc in TEST_CASES:
            assert tc.language in ("en", "fr", "sw"), (
                f"Case {tc.id} has invalid language: {tc.language}"
            )

    def test_account_ids_valid(self) -> None:
        from src.knowledge.accounts import ACCOUNTS
        for tc in TEST_CASES:
            assert tc.account_id in ACCOUNTS, (
                f"Case {tc.id} references unknown account: {tc.account_id}"
            )


# === Report Tests ===


class TestReport:
    def test_format_empty_report(self) -> None:
        report = EvalReport(
            total_cases=0,
            passed_cases=0,
            failed_cases=0,
            error_cases=0,
            overall_scores={},
            by_category={},
            case_results=[],
        )
        text = format_report(report)
        assert "RELAY EVALUATION REPORT" in text
        assert "No test cases" in text

    def test_format_report_with_results(self) -> None:
        result = CaseResult(
            test_case_id="test_001",
            category=EvalCategory.BALANCE,
            response_text="Your balance is 245,000 FCFA",
            tools_used=("check_balance",),
            tool_correctness=1.0,
            must_contain_pass=True,
            must_not_contain_pass=True,
            refusal_correct=True,
            groundedness=GroundednessResult(
                score=1.0, grounded_claims=2, ungrounded_claims=0,
                contradictions=0, reasoning="All claims grounded",
            ),
            hallucination=None,
            compliance=None,
            language_quality=None,
            latency_ms=150.0,
        )
        report = EvalReport(
            total_cases=1,
            passed_cases=1,
            failed_cases=0,
            error_cases=0,
            overall_scores={"tool_correctness": 1.0, "groundedness": 1.0},
            by_category={"balance_inquiry": {"total": 1, "passed": 1, "pass_rate": 1.0}},
            case_results=[result],
            metadata={"avg_latency_ms": 150.0},
        )
        text = format_report(report)
        assert "RELAY EVALUATION REPORT" in text
        assert "100.0%" in text
        assert "Tool Correctness" in text

    def test_format_report_with_failures(self) -> None:
        result = CaseResult(
            test_case_id="test_fail",
            category=EvalCategory.BALANCE,
            response_text="I don't know",
            tools_used=(),
            tool_correctness=0.0,
            must_contain_pass=False,
            must_not_contain_pass=True,
            refusal_correct=False,
            groundedness=None,
            hallucination=None,
            compliance=None,
            language_quality=None,
            latency_ms=100.0,
        )
        report = EvalReport(
            total_cases=1,
            passed_cases=0,
            failed_cases=1,
            error_cases=0,
            overall_scores={},
            by_category={},
            case_results=[result],
        )
        text = format_report(report)
        assert "FAILURES" in text
        assert "test_fail" in text
