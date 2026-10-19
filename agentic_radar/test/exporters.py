"""
Exporters for dynamic test results.

Provides functions to serialize a list of :class:`~agentic_radar.test.test.TestResult`
objects into JSON or Markdown so that CI/CD pipelines can consume them without
requiring manual terminal redirection.
"""

import json
from pathlib import Path
from typing import Optional

from .test import TestResult


def to_json(results: list[TestResult]) -> str:
    """Serialize test results to a JSON string (pretty-printed with 2-space indent).

    Args:
        results: List of :class:`TestResult` instances produced by the test harness.

    Returns:
        A formatted JSON string representing the results array.
    """
    payload = [r.model_dump() for r in results]
    return json.dumps(payload, indent=2, ensure_ascii=False)


def to_markdown(results: list[TestResult]) -> str:
    """Serialize test results to a Markdown report string.

    The report contains:
    - A top-level heading and run summary.
    - A summary statistics table (total / passed / failed).
    - A quick-reference results table.
    - A full per-test detail section with the prompt, agent response,
      oracle verdict, and explanation.

    Args:
        results: List of :class:`TestResult` instances produced by the test harness.

    Returns:
        A Markdown string suitable for writing to a ``.md`` file.
    """
    total = len(results)
    passed = sum(1 for r in results if r.test_passed)
    failed = total - passed

    lines: list[str] = [
        "# Agentic Radar – Dynamic Test Results",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Tests | {total} |",
        f"| Passed | {passed} |",
        f"| Failed | {failed} |",
        "",
        "## Results Overview",
        "",
        "| # | Agent Name | Test Name | Result | Oracle Explanation |",
        "|---|------------|-----------|--------|--------------------|",
    ]

    for i, r in enumerate(results, 1):
        result_cell = "✅ PASSED" if r.test_passed else "❌ FAILED"
        explanation = r.explanation.replace("|", "\\|").replace("\n", " ")
        agent_name = r.agent_name.replace("|", "\\|")
        test_name = r.test_name.replace("|", "\\|")
        lines.append(
            f"| {i} | {agent_name} | {test_name} | {result_cell} | {explanation} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Detailed Test Results")

    for i, r in enumerate(results, 1):
        verdict = "✅ PASSED" if r.test_passed else "❌ FAILED"
        lines += [
            "",
            f"### Test {i}: {r.test_name} — {r.agent_name} {verdict}",
            "",
            "#### 📨 Prompt (Input)",
            "",
            "> " + r.input.replace("\n", "\n> "),
            "",
            "#### 🤖 Agent Response",
            "",
            "> " + r.output.replace("\n", "\n> "),
            "",
            "#### 🔍 Oracle Evaluation",
            "",
            f"**Verdict:** {verdict}  ",
            f"**Explanation:** {r.explanation}",
            "",
            "---",
        ]

    lines.append("")
    return "\n".join(lines)



def write_results(
    results: list[TestResult],
    output_format: str,
    output_path: Path,
) -> None:
    """Format *results* according to *output_format* and write to *output_path*.

    Args:
        results: List of :class:`TestResult` instances.
        output_format: One of ``"json"`` or ``"markdown"``.
        output_path: Destination file path.

    Raises:
        ValueError: If *output_format* is not a supported value.
    """
    if output_format == "json":
        content = to_json(results)
    elif output_format == "markdown":
        content = to_markdown(results)
    else:
        raise ValueError(
            f"Unsupported output format: '{output_format}'. "
            "Choose one of: json, markdown."
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"[Exporter] Results written to {output_path} (format: {output_format})")
