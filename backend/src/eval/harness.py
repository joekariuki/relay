"""Evaluation harness for running test cases through the agent pipeline.

Runs test cases with bounded concurrency, scores across multiple dimensions,
and produces structured reports.
"""

from __future__ import annotations

import asyncio
import logging
import time

from src.agent.core import process_message

from .compliance import check_compliance
from .groundedness import score_groundedness
from .hallucination import detect_hallucinations
from .language_quality import evaluate_language_quality
from .models import CaseResult, EvalCategory, EvalReport, TestCase
from .test_cases import get_test_cases

logger = logging.getLogger(__name__)


class EvalHarness:
    """Evaluation harness for running test suites against the agent."""

    def __init__(
        self,
        concurrency: int = 5,
    ) -> None:
        self.concurrency = concurrency

    async def run(
        self,
        category: EvalCategory | None = None,
        tags: set[str] | None = None,
        max_cases: int | None = None,
    ) -> EvalReport:
        """Run evaluation test cases and produce a report.

        Args:
            category: Filter by category (None for all).
            tags: Filter by tags (None for all).
            max_cases: Maximum number of cases to run.
        """
        cases = get_test_cases(category=category, tags=tags, max_cases=max_cases)
        if not cases:
            return _empty_report()

        logger.info("Running %d eval cases (concurrency=%d)", len(cases), self.concurrency)

        semaphore = asyncio.Semaphore(self.concurrency)
        results: list[CaseResult] = []

        async def run_case(case: TestCase) -> CaseResult:
            async with semaphore:
                return await self._evaluate_case(case)

        tasks = [asyncio.create_task(run_case(case)) for case in cases]

        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)
            if (i + 1) % 10 == 0:
                logger.info("Completed %d/%d cases", i + 1, len(cases))

        return _build_report(results)

    async def _evaluate_case(self, case: TestCase) -> CaseResult:
        """Evaluate a single test case through the full pipeline."""
        from src.config import get_settings

        start = time.perf_counter()

        try:
            settings = get_settings()

            # Run the agent
            agent_response = await process_message(
                message=case.message,
                account_id=case.account_id,
                language_hint=case.language,
            )

            response_text = agent_response.response_text
            tools_used = tuple(t.tool_name for t in agent_response.tools_used)
            tool_results = [t.result for t in agent_response.tools_used]

            # Score tool correctness
            tool_correctness = _score_tool_correctness(case.expected_tools, tools_used)

            # Check must_contain / must_not_contain
            must_contain_pass = all(
                s.lower() in response_text.lower() for s in case.must_contain
            )
            must_not_contain_pass = all(
                s.lower() not in response_text.lower() for s in case.must_not_contain
            )

            # Check refusal correctness
            refusal_correct = _check_refusal(case.expect_refusal, response_text)

            # Run evaluation judges in parallel
            groundedness_task = score_groundedness(
                response_text, tool_results, model=settings.eval_model
            )
            hallucination_task = detect_hallucinations(
                response_text, case.message, tool_results, model=settings.eval_model
            )
            language_task = evaluate_language_quality(
                response_text, case.language, model=settings.eval_model
            )

            groundedness, hallucination, language_quality = await asyncio.gather(
                groundedness_task, hallucination_task, language_task
            )

            # Run compliance (synchronous, rule-based)
            injection_flagged = not agent_response.metadata.get("guardrail_safe", True)
            compliance = check_compliance(
                response_text,
                injection_flagged=injection_flagged,
                tool_results=tool_results,
            )

            latency_ms = (time.perf_counter() - start) * 1000

            return CaseResult(
                test_case_id=case.id,
                category=case.category,
                response_text=response_text,
                tools_used=tools_used,
                tool_correctness=tool_correctness,
                must_contain_pass=must_contain_pass,
                must_not_contain_pass=must_not_contain_pass,
                refusal_correct=refusal_correct,
                groundedness=groundedness,
                hallucination=hallucination,
                compliance=compliance,
                language_quality=language_quality,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.error("Case %s failed: %s", case.id, e)
            return CaseResult(
                test_case_id=case.id,
                category=case.category,
                response_text="",
                tools_used=(),
                tool_correctness=0.0,
                must_contain_pass=False,
                must_not_contain_pass=True,
                refusal_correct=False,
                groundedness=None,
                hallucination=None,
                compliance=None,
                language_quality=None,
                latency_ms=latency_ms,
                error=str(e),
            )


def _score_tool_correctness(
    expected: tuple[str, ...],
    actual: tuple[str, ...],
) -> float:
    """Score how well the tools used match expectations."""
    if not expected and not actual:
        return 1.0
    if not expected:
        return 0.5  # Used tools when none expected (might be okay)
    expected_set = set(expected)
    actual_set = set(actual)
    if expected_set == actual_set:
        return 1.0
    # Partial credit for overlap
    intersection = expected_set & actual_set
    union = expected_set | actual_set
    return len(intersection) / len(union) if union else 0.0


def _check_refusal(expect_refusal: bool, response_text: str) -> bool:
    """Check if the refusal behavior matches expectations."""
    refusal_indicators = [
        "i can't", "i cannot", "i'm unable", "i am unable",
        "i don't have", "i'm not able", "i am not able",
        "i'm sorry, but", "i apologize, but",
        "i can only help", "i can only assist",
        "out of scope", "beyond my scope",
        "not something i can", "unable to assist with",
        "je ne peux pas", "je suis desole",
        "siwezi", "pole", "samahani",
    ]
    response_lower = response_text.lower()
    has_refusal = any(indicator in response_lower for indicator in refusal_indicators)

    if expect_refusal:
        return has_refusal
    return True  # Non-refusal cases always pass this check


def _build_report(results: list[CaseResult]) -> EvalReport:
    """Build an evaluation report from case results."""
    total = len(results)
    errors = sum(1 for r in results if r.error is not None)
    non_error = [r for r in results if r.error is None]

    # A case "passes" if tool correctness > 0.5, must_contain passes, must_not_contain passes
    passed = sum(
        1 for r in non_error
        if r.tool_correctness >= 0.5
        and r.must_contain_pass
        and r.must_not_contain_pass
    )
    failed = total - passed - errors

    # Overall scores
    overall: dict[str, float] = {}
    if non_error:
        overall["tool_correctness"] = sum(r.tool_correctness for r in non_error) / len(non_error)
        overall["must_contain_pass_rate"] = (
            sum(1 for r in non_error if r.must_contain_pass) / len(non_error)
        )
        overall["must_not_contain_pass_rate"] = (
            sum(1 for r in non_error if r.must_not_contain_pass) / len(non_error)
        )

        grounded_scores = [
            r.groundedness.score for r in non_error if r.groundedness is not None
        ]
        if grounded_scores:
            overall["groundedness"] = sum(grounded_scores) / len(grounded_scores)

        compliant_flags = [
            r.compliance.compliant for r in non_error if r.compliance is not None
        ]
        if compliant_flags:
            overall["compliance_rate"] = sum(1 for c in compliant_flags if c) / len(compliant_flags)

        halluc_flags = [
            r.hallucination.clean for r in non_error if r.hallucination is not None
        ]
        if halluc_flags:
            overall["hallucination_free_rate"] = (
                sum(1 for h in halluc_flags if h) / len(halluc_flags)
            )

        lang_correct = [
            r.language_quality.correct_language
            for r in non_error if r.language_quality is not None
        ]
        lang_fluency = [
            r.language_quality.fluency_score
            for r in non_error if r.language_quality is not None
        ]
        if lang_correct:
            overall["language_correctness"] = (
                sum(1 for lc in lang_correct if lc) / len(lang_correct)
            )
        if lang_fluency:
            overall["avg_fluency"] = sum(lang_fluency) / len(lang_fluency)

    # By category
    by_category: dict[str, dict[str, float]] = {}
    for cat in EvalCategory:
        cat_results = [r for r in non_error if r.category == cat]
        if cat_results:
            cat_passed = sum(
                1 for r in cat_results
                if r.tool_correctness >= 0.5
                and r.must_contain_pass
                and r.must_not_contain_pass
            )
            by_category[cat.value] = {
                "total": float(len(cat_results)),
                "passed": float(cat_passed),
                "pass_rate": cat_passed / len(cat_results),
                "tool_correctness": (
                    sum(r.tool_correctness for r in cat_results) / len(cat_results)
                ),
            }

    avg_latency = sum(r.latency_ms for r in results) / total if total else 0.0

    return EvalReport(
        total_cases=total,
        passed_cases=passed,
        failed_cases=failed,
        error_cases=errors,
        overall_scores=overall,
        by_category=by_category,
        case_results=results,
        metadata={
            "avg_latency_ms": avg_latency,
        },
    )


def _empty_report() -> EvalReport:
    """Return an empty report when no cases are run."""
    return EvalReport(
        total_cases=0,
        passed_cases=0,
        failed_cases=0,
        error_cases=0,
        overall_scores={},
        by_category={},
        case_results=[],
    )
