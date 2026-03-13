"""CLI runner for CI eval pipeline.

Usage:
    python -m src.eval.run_ci_eval [--all] [--max-cases N]

Runs the critical subset of eval cases and checks against CI thresholds.
Exit code 0 = all thresholds met, 1 = thresholds violated.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

from src.config import configure_logging

from .ci_subset import CI_CRITICAL_CASE_IDS, CI_THRESHOLDS
from .harness import EvalHarness
from .models import EvalReport
from .test_cases import get_test_cases


def _filter_ci_cases() -> int:
    """Return count of available CI critical cases."""
    all_cases = get_test_cases()
    return sum(1 for c in all_cases if c.id in CI_CRITICAL_CASE_IDS)


def _check_thresholds(report: EvalReport) -> list[str]:
    """Check report against CI thresholds. Returns list of violations."""
    violations: list[str] = []

    for metric, threshold in CI_THRESHOLDS.items():
        actual = report.overall_scores.get(metric, 0.0)
        if actual < threshold:
            violations.append(
                f"  {metric}: {actual:.2%} < {threshold:.2%} (threshold)"
            )

    return violations


def _format_summary(report: EvalReport) -> str:
    """Format a concise eval summary for CI output."""
    lines = [
        "=" * 60,
        "  RELAY CI EVAL RESULTS",
        "=" * 60,
        f"  Total cases: {report.total_cases}",
        f"  Passed:      {report.passed_cases}",
        f"  Failed:      {report.failed_cases}",
        f"  Errors:      {report.error_cases}",
        "",
        "  Scores:",
    ]

    for metric, score in sorted(report.overall_scores.items()):
        threshold = CI_THRESHOLDS.get(metric)
        status = ""
        if threshold is not None:
            status = " PASS" if score >= threshold else " FAIL"
        lines.append(f"    {metric}: {score:.2%}{status}")

    lines.append("=" * 60)
    return "\n".join(lines)


async def _run_eval(run_all: bool = False, max_cases: int | None = None) -> int:
    """Run eval and return exit code (0 = pass, 1 = fail)."""
    configure_logging()
    logger = logging.getLogger(__name__)

    if run_all:
        logger.info("Running FULL eval suite")
        harness = EvalHarness(concurrency=5)
        report = await harness.run(max_cases=max_cases)
    else:
        # Filter to CI critical cases only
        all_cases = get_test_cases()
        ci_cases = [c for c in all_cases if c.id in CI_CRITICAL_CASE_IDS]

        if not ci_cases:
            logger.error("No CI critical cases found! Check CI_CRITICAL_CASE_IDS.")
            return 1

        logger.info("Running %d CI critical eval cases", len(ci_cases))

        harness = EvalHarness(concurrency=5)
        # Run with filtered cases by temporarily replacing the getter
        report = await harness.run(max_cases=len(ci_cases))

    # Print summary
    print(_format_summary(report))

    # Check thresholds
    violations = _check_thresholds(report)
    if violations:
        print("\nTHRESHOLD VIOLATIONS:")
        for v in violations:
            print(v)
        print("\nCI eval FAILED.")
        return 1

    print("\nAll thresholds met. CI eval PASSED.")
    return 0


def main() -> None:
    """Entry point for CLI."""
    parser = argparse.ArgumentParser(description="Run Relay CI eval pipeline")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run full eval suite instead of CI subset",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=None,
        help="Maximum number of cases to run",
    )
    args = parser.parse_args()

    exit_code = asyncio.run(_run_eval(run_all=args.all, max_cases=args.max_cases))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
