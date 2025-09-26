from constants.messages import SETTINGS_LINKS
from constants.urls import GH_BASE_URL


def get_issue_title(file_path: str):
    return f"Schedule: Add unit tests to {file_path}"


def get_issue_body(
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

    # Early return if no coverage data available
    if all(
        x is None
        for x in [statement_coverage, function_coverage, branch_coverage, line_coverage]
    ):
        return f"Add unit tests for [{file_path}]({file_url}).\n\n{SETTINGS_LINKS}"

    # Build coverage details
    coverage_details: list[str] = []
    if line_coverage is not None:
        uncovered_lines_text = (
            f" (Uncovered Lines: {uncovered_lines})" if uncovered_lines else ""
        )
        coverage_details.append(
            f"- Line Coverage: {int(line_coverage)}%{uncovered_lines_text}"
        )

    if statement_coverage is not None:
        coverage_details.append(f"- Statement Coverage: {int(statement_coverage)}%")

    if function_coverage is not None:
        uncovered_functions_text = (
            f" (Uncovered Functions: {uncovered_functions})"
            if uncovered_functions
            else ""
        )
        coverage_details.append(
            f"- Function Coverage: {int(function_coverage)}%{uncovered_functions_text}"
        )

    if branch_coverage is not None:
        uncovered_branches_text = (
            f" (Uncovered Branches: {uncovered_branches})" if uncovered_branches else ""
        )
        coverage_details.append(
            f"- Branch Coverage: {int(branch_coverage)}%{uncovered_branches_text}"
        )

    coverage_section = "\n".join(coverage_details)

    return (
        f"Add unit tests for [{file_path}]({file_url})\n\n"
        f"{coverage_section}\n\n"
        f"Focus on covering the uncovered areas, including both happy paths, error cases, edge cases, and corner cases.\n\n"
        f"{SETTINGS_LINKS}"
    )
