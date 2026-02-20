from typing import Literal

from services.coverages.coverage_types import CoverageReport, CoverageStats


def create_coverage_report(
    path: str, stats: CoverageStats, level: Literal["repository", "directory", "file"]
):
    # For directory level and empty path, then use "."
    if level == "directory" and path == "":
        path = "."

    # None means "not measured" by the coverage tool, not "0% covered" or "100% covered"
    # e.g. PHP coverage tools (Xdebug/PCOV) don't report branch data in LCOV
    line_coverage = (
        round(stats["lines_covered"] / stats["lines_total"] * 100, 1)
        if stats["lines_total"] > 0
        else None
    )
    function_coverage = (
        round(stats["functions_covered"] / stats["functions_total"] * 100, 1)
        if stats["functions_total"] > 0
        else None
    )
    branch_coverage = (
        round(stats["branches_covered"] / stats["branches_total"] * 100, 1)
        if stats["branches_total"] > 0
        else None
    )

    coverage_report: CoverageReport = {
        "package_name": None,
        "language": "unknown",
        "level": level,
        "full_path": path,
        "statement_coverage": line_coverage,
        "line_coverage": line_coverage,
        "function_coverage": function_coverage,
        "branch_coverage": branch_coverage,
        "lines_covered": stats["lines_covered"],
        "lines_total": stats["lines_total"],
        "functions_covered": stats["functions_covered"],
        "functions_total": stats["functions_total"],
        "branches_covered": stats["branches_covered"],
        "branches_total": stats["branches_total"],
        "uncovered_lines": (
            ", ".join(map(str, sorted(stats["uncovered_lines"])))
            if level == "file" and line_coverage is not None and line_coverage > 0
            else ""
        ),
        "uncovered_functions": (
            ", ".join(
                (
                    f"L{func[0]}:{func[1]}"
                    if len(func) == 2
                    else f"L{func[0]}-{func[1]}:{func[2]}"
                )
                for func in sorted(stats["uncovered_functions"])
            )
        ),
        "uncovered_branches": (", ".join(sorted(stats["uncovered_branches"]))),
    }
    return coverage_report
