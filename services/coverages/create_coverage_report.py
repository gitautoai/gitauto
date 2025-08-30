from typing import Literal

from services.coverages.coverage_types import CoverageReport


def create_coverage_report(
    path: str, stats: dict, level: Literal["repository", "directory", "file"]
):
    # For directory level and empty path, then use "."
    if level == "directory" and path == "":
        path = "."

    line_coverage = round(
        (
            (stats["lines_covered"] / stats["lines_total"] * 100)
            if stats["lines_total"] > 0
            else 100
        ),
        2,
    )
    function_coverage = round(
        (
            (stats["functions_covered"] / stats["functions_total"] * 100)
            if stats["functions_total"] > 0
            else 100
        ),
        2,
    )
    branch_coverage = round(
        (
            (stats["branches_covered"] / stats["branches_total"] * 100)
            if stats["branches_total"] > 0
            else 100
        ),
        2,
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
        "path_coverage": branch_coverage,
        "uncovered_lines": (
            ", ".join(map(str, sorted(stats["uncovered_lines"])))
            if level == "file" and line_coverage > 0
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
