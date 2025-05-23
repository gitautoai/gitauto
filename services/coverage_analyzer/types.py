from typing import TypedDict, Literal


class CoverageReport(TypedDict):
    package_name: str | None
    level: Literal["repository", "directory", "file"]
    full_path: str
    statement_coverage: float
    function_coverage: float
    branch_coverage: float
    line_coverage: float
    uncovered_lines: str


DEFAULT_COVERAGES: CoverageReport = {
    "package_name": None,
    "level": "repository",
    "full_path": "",
    "statement_coverage": 0,
    "function_coverage": 0,
    "branch_coverage": 0,
    "line_coverage": 0,
    "uncovered_lines": "",
}
