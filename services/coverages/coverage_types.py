from typing import Union, TypedDict, Literal


class CoverageReport(TypedDict):
    package_name: Union[str, None]
    language: str
    level: Literal["repository", "directory", "file"]
    full_path: str
    statement_coverage: float
    function_coverage: float
    branch_coverage: float
    line_coverage: float
    path_coverage: float
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
    "path_coverage": 0,
    "uncovered_lines": "",
    "uncovered_functions": "",
    "uncovered_branches": "",
}
