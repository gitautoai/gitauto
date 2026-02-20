from typing import Union, TypedDict, Literal


class CoverageStats(TypedDict):
    lines_covered: int
    lines_total: int
    functions_covered: int
    functions_total: int
    branches_covered: int
    branches_total: int
    uncovered_lines: set[int]
    uncovered_functions: set[tuple[int, str] | tuple[int, int, str]]
    uncovered_branches: set[str]


class CoverageReport(TypedDict):
    package_name: Union[str, None]
    language: str
    level: Literal["repository", "directory", "file"]
    full_path: str
    statement_coverage: float | None
    function_coverage: float | None
    branch_coverage: float | None
    line_coverage: float | None
    lines_covered: int
    lines_total: int
    functions_covered: int
    functions_total: int
    branches_covered: int
    branches_total: int
    uncovered_lines: str
    uncovered_functions: str
    uncovered_branches: str


DEFAULT_COVERAGES: CoverageReport = {
    "package_name": None,
    "language": "unknown",
    "level": "repository",
    "full_path": "",
    "statement_coverage": 0,
    "function_coverage": 0,
    "branch_coverage": 0,
    "line_coverage": 0,
    "lines_covered": 0,
    "lines_total": 0,
    "functions_covered": 0,
    "functions_total": 0,
    "branches_covered": 0,
    "branches_total": 0,
    "uncovered_lines": "",
    "uncovered_functions": "",
    "uncovered_branches": "",
}
