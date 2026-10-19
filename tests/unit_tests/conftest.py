import os
import pytest

from collections import defaultdict

FRAMEWORK_NAME_MAPPING = {
    "langgraph": "LangGraph",
    "crewai": "CrewAI",
    "n8n": "n8n",
    "openai-agents": "OpenAI Agents"
}

test_metadata = {}
all_results = defaultdict(list)

def pytest_runtest_protocol(item, nextitem):
    test_metadata[item.nodeid] = {
        "docstring": item.obj.__doc__,
        "markers": [m.name for m in item.iter_markers()],
        "lineno": item.obj.__code__.co_firstlineno + 1
    }
    return None

def pytest_runtest_logreport(report):
    if report.when == "call":
        try:
            meta = test_metadata.get(report.nodeid, {})

            markers = meta.get("markers", [])
            docstring = meta.get("docstring", "")
            lineno = meta.get("lineno", 0)

            # Only process reports that match the expected unit_tests/<framework>/<category>/ depth.
            relative_parts = report.nodeid.split("unit_tests/")
            if len(relative_parts) < 2:
                return
            inner_parts = relative_parts[-1].split("/")
            if len(inner_parts) < 2:
                return

            framework_key = inner_parts[0]
            category = inner_parts[1]
            framework = FRAMEWORK_NAME_MAPPING.get(
                framework_key,
                "Unknown (error while mapping name)",
            )
            # Safely handle None docstrings (e.g. class-based test methods without a docstring)
            docstring = (docstring or "").replace("\n", "")
            outcome = "Unknown"
            url = report.nodeid.split("::")[0] + f"#L{lineno}"

            if "supported" in markers:
                if report.outcome == "passed":
                    outcome = "Passed✅"
                elif report.outcome == "failed":
                    outcome = "Failed❌"
            elif "not_supported" in markers:
                outcome = "Unsupported⬜"

            result = {
                "docstring": docstring,
                "outcome": outcome,
                "url": url,
                "category": category
            }

            all_results[framework].append(result)
        except Exception:
            # Silently skip reports that don't match the expected structure.
            pass


def pytest_sessionfinish(session, exitstatus):
    with open("test-report.md", "w", encoding="utf-8") as f:
        for framework, results in all_results.items():
            f.write(f"# {framework} Tests\n")
            f.write("| Category | Test Description | Status | Link |\n")
            f.write("|----------|------------------|--------|------|\n")

            results_by_category = defaultdict(list)
            for result in results:
                results_by_category[result["category"]].append(result)

            for category in sorted(results_by_category.keys()):
                category_results = results_by_category[category]
                first = True
                for result in category_results:
                    cat_cell = category if first else ""
                    f.write(f"| {cat_cell} | {result['docstring']} | {result['outcome']} | [link]({result['url']}) |\n")
                    first = False