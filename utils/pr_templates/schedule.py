from constants.messages import SETTINGS_LINKS
from constants.urls import GH_BASE_URL

SCHEDULE_PREFIX = "Schedule:"
SCHEDULE_PREFIX_ADD = f"{SCHEDULE_PREFIX} Add unit tests to "
SCHEDULE_PREFIX_INCREASE = f"{SCHEDULE_PREFIX} Achieve 100% test coverage for "


def get_pr_title(file_path: str, has_existing_tests: bool = False):
    prefix = SCHEDULE_PREFIX_INCREASE if has_existing_tests else SCHEDULE_PREFIX_ADD
    return f"{prefix}{file_path}"


def get_pr_body(
    owner: str,
    repo: str,
    branch: str,
    file_path: str,
    statement_coverage: float | None,
    function_coverage: float | None,
    branch_coverage: float | None,
    line_coverage: float | None,
    uncovered_lines: str | None,
    uncovered_functions: str | None,
    uncovered_branches: str | None,
):
    file_url = f"{GH_BASE_URL}/{owner}/{repo}/blob/{branch}/{file_path}"

    # Coverage section
    cov_header = f"## Current Coverage for [{file_path}]({file_url})"
    has_coverage = not all(
        x is None
        for x in [statement_coverage, function_coverage, branch_coverage, line_coverage]
    )
    if has_coverage:
        cov_lines: list[str] = []
        if line_coverage is not None:
            uncovered = f" (Uncovered: {uncovered_lines})" if uncovered_lines else ""
            cov_lines.append(f"- Line Coverage: {int(line_coverage)}%{uncovered}")
        if statement_coverage is not None:
            cov_lines.append(f"- Statement Coverage: {int(statement_coverage)}%")
        if function_coverage is not None:
            uncovered = (
                f" (Uncovered: {uncovered_functions})" if uncovered_functions else ""
            )
            cov_lines.append(
                f"- Function Coverage: {int(function_coverage)}%{uncovered}"
            )
        if branch_coverage is not None:
            uncovered = (
                f" (Uncovered: {uncovered_branches})" if uncovered_branches else ""
            )
            cov_lines.append(f"- Branch Coverage: {int(branch_coverage)}%{uncovered}")
        cov_body = "\n".join(cov_lines)
    else:
        cov_body = "No coverage data available."
    coverage = f"{cov_header}\n{cov_body}"

    # Instructions section
    instructions_header = "## Instructions"
    if has_coverage:
        instructions_body = "Focus on covering the uncovered areas."
    else:
        instructions_body = (
            "Create tests for happy paths, error cases, edge cases, and corner cases."
        )
    instructions = f"{instructions_header}\n{instructions_body}"

    return f"{coverage}\n\n{instructions}\n\n{SETTINGS_LINKS}"
