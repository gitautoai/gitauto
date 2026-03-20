from typing import Literal

from services.coverages.calc_coverage import calc_coverage
from services.coverages.coverage_types import CoverageReport, CoverageStats


def create_coverage_report(
    path: str,
    stats: CoverageStats,
    level: Literal["repository", "directory", "file"],
):
    # For directory level and empty path, then use "."
    if level == "directory" and path == "":
        path = "."

    line_coverage = calc_coverage(stats["lines_covered"], stats["lines_total"])
    function_coverage = calc_coverage(
        stats["functions_covered"], stats["functions_total"]
    )
    branch_coverage = calc_coverage(stats["branches_covered"], stats["branches_total"])

    coverage_report: CoverageReport = {
        "package_name": None,
        "language": "unknown",
        "level": level,
        "full_path": path,
        "statement_coverage": line_coverage,
        "line_coverage": line_coverage,
        "function_coverage": function_coverage,
        "branch_coverage": branch_coverage,
        "lines_covered": stats["lines_covered"] or 0,
        "lines_total": stats["lines_total"] or 0,
        "functions_covered": stats["functions_covered"] or 0,
        "functions_total": stats["functions_total"] or 0,
        "branches_covered": stats["branches_covered"] or 0,
        "branches_total": stats["branches_total"] or 0,
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
