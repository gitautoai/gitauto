from constants.messages import SETTINGS_LINKS
from constants.urls import GH_BASE_URL

SCHEDULE_PREFIX = "Schedule:"
SCHEDULE_PREFIX_ADD = f"{SCHEDULE_PREFIX} Add unit and integration tests to"
SCHEDULE_PREFIX_INCREASE = f"{SCHEDULE_PREFIX} Achieve 100% test coverage for"
SCHEDULE_PREFIX_QUALITY = f"{SCHEDULE_PREFIX} Strengthen tests for"


MAX_CATEGORIES_IN_TITLE = 3


def get_pr_title(
    file_path: str,
    has_existing_tests: bool = False,
    quality_only: bool = False,
    failed_categories: list[str] | None = None,
):
    if quality_only:
        if failed_categories:
            shown = failed_categories[:MAX_CATEGORIES_IN_TITLE]
            cat_str = ", ".join(shown)
            if len(failed_categories) > MAX_CATEGORIES_IN_TITLE:
                cat_str += f" +{len(failed_categories) - MAX_CATEGORIES_IN_TITLE}"
            return f"{SCHEDULE_PREFIX_QUALITY} `{file_path}` ({cat_str})"
        return f"{SCHEDULE_PREFIX_QUALITY} `{file_path}`"
    prefix = SCHEDULE_PREFIX_INCREASE if has_existing_tests else SCHEDULE_PREFIX_ADD
    return f"{prefix} `{file_path}`"


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
    quality_checks: dict[str, dict[str, dict[str, str]]] | None,
):
    file_url = f"{GH_BASE_URL}/{owner}/{repo}/blob/{branch}/{file_path}"
    sections: list[str] = []

    # Coverage section (only for <100% files)
    has_coverage = not all(
        x is None
        for x in [statement_coverage, function_coverage, branch_coverage, line_coverage]
    )
    if has_coverage:
        cov_header = f"## Current Coverage for [{file_path}]({file_url})"
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
        sections.append(f"{cov_header}\n" + "\n".join(cov_lines))

    # Quality check failures section
    if quality_checks:
        quality_lines: list[str] = []
        for category, checks in quality_checks.items():
            failures = [
                (check_name, check_data)
                for check_name, check_data in checks.items()
                if check_data.get("status") == "fail"
            ]
            if not failures:
                continue

            quality_lines.append(f"\n### {category}")
            for check_name, check_data in failures:
                reason = check_data.get("reason", "")
                quality_lines.append(f"- **{check_name}**: {reason}")

        if quality_lines:
            header = f"## Quality Check Failures for [{file_path}]({file_url})"
            sections.append(header + "\n".join(quality_lines))

    # Instructions section
    instructions_header = "## Instructions"
    if has_coverage and quality_checks:
        instructions_body = "Focus on covering the uncovered areas and addressing the quality gaps listed above."
    elif has_coverage:
        instructions_body = "Focus on covering the uncovered areas."
    elif quality_checks:
        instructions_body = (
            "Add or strengthen tests to address the quality gaps listed above."
        )
    else:
        instructions_body = (
            "Create tests for happy paths, error cases, edge cases, and corner cases."
        )
    sections.append(f"{instructions_header}\n{instructions_body}")

    return "\n\n".join(sections) + f"\n\n{SETTINGS_LINKS}"
