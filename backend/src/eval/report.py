"""Evaluation report formatting and output."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .models import EvalReport


def format_report(report: EvalReport) -> str:
    """Format an evaluation report as a human-readable string."""
    lines: list[str] = []

    lines.append("=" * 60)
    lines.append("  RELAY EVALUATION REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Summary
    total = report.total_cases
    if total == 0:
        lines.append("No test cases were run.")
        return "\n".join(lines)

    pass_rate = report.passed_cases / total * 100
    lines.append(f"Total Cases:  {total}")
    lines.append(f"Passed:       {report.passed_cases} ({pass_rate:.1f}%)")
    lines.append(f"Failed:       {report.failed_cases}")
    lines.append(f"Errors:       {report.error_cases}")
    lines.append("")

    # Overall scores
    if report.overall_scores:
        lines.append("-" * 40)
        lines.append("  OVERALL SCORES")
        lines.append("-" * 40)
        for key, value in report.overall_scores.items():
            label = key.replace("_", " ").title()
            if "rate" in key or key == "groundedness":
                lines.append(f"  {label}: {value:.1%}")
            else:
                lines.append(f"  {label}: {value:.2f}")
        lines.append("")

    # Category breakdown
    if report.by_category:
        lines.append("-" * 40)
        lines.append("  BY CATEGORY")
        lines.append("-" * 40)
        for cat_name, scores in sorted(report.by_category.items()):
            total_cat = int(scores.get("total", 0))
            passed_cat = int(scores.get("passed", 0))
            rate = scores.get("pass_rate", 0.0)
            lines.append(f"  {cat_name:30s}  {passed_cat}/{total_cat} ({rate:.0%})")
        lines.append("")

    # Latency
    avg_latency = report.metadata.get("avg_latency_ms", 0.0)
    if isinstance(avg_latency, (int, float)) and avg_latency > 0:
        lines.append(f"  Avg Latency: {avg_latency:.0f}ms")
        lines.append("")

    # Failures detail
    failures = [r for r in report.case_results if r.error is None and (
        r.tool_correctness < 0.5 or not r.must_contain_pass or not r.must_not_contain_pass
    )]
    if failures:
        lines.append("-" * 40)
        lines.append("  FAILURES")
        lines.append("-" * 40)
        for r in failures[:20]:  # Show first 20
            lines.append(f"  [{r.test_case_id}] {r.category.value}")
            if r.tool_correctness < 0.5:
                lines.append(f"    Tool correctness: {r.tool_correctness:.2f}")
            if not r.must_contain_pass:
                lines.append("    Missing required content")
            if not r.must_not_contain_pass:
                lines.append("    Contains prohibited content")
            lines.append("")

    # Errors detail
    errors = [r for r in report.case_results if r.error is not None]
    if errors:
        lines.append("-" * 40)
        lines.append("  ERRORS")
        lines.append("-" * 40)
        for r in errors[:10]:
            lines.append(f"  [{r.test_case_id}] {r.error}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def save_report(report: EvalReport, output_dir: str = "eval_results") -> str:
    """Save an evaluation report as JSON.

    Returns the path to the saved file.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Build JSON-serializable data
    data = {
        "summary": {
            "total_cases": report.total_cases,
            "passed_cases": report.passed_cases,
            "failed_cases": report.failed_cases,
            "error_cases": report.error_cases,
        },
        "overall_scores": report.overall_scores,
        "by_category": report.by_category,
        "metadata": {str(k): v for k, v in report.metadata.items()},
        "case_results": [
            {
                "test_case_id": r.test_case_id,
                "category": r.category.value,
                "tools_used": list(r.tools_used),
                "tool_correctness": r.tool_correctness,
                "must_contain_pass": r.must_contain_pass,
                "must_not_contain_pass": r.must_not_contain_pass,
                "refusal_correct": r.refusal_correct,
                "groundedness_score": r.groundedness.score if r.groundedness else None,
                "hallucination_clean": r.hallucination.clean if r.hallucination else None,
                "compliance_compliant": r.compliance.compliant if r.compliance else None,
                "language_correct": (
                    r.language_quality.correct_language if r.language_quality else None
                ),
                "latency_ms": r.latency_ms,
                "error": r.error,
            }
            for r in report.case_results
        ],
    }

    # Use timestamp in filename
    # Lazy import: datetime only needed when persisting report to disk
    import datetime

    timestamp = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"eval_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)

    return filepath
