import json
import os
from dataclasses import dataclass

from services.jest.coverage_types import _Location
from services.jest.validate_istanbul_file_data import validate_istanbul_file_data
from utils.logging.logging_config import logger

# The `json` reporter in both jest and vitest always outputs this filename
COVERAGE_JSON_FILENAME = "coverage-final.json"


@dataclass
class Coverage:  # pylint: disable=too-many-instance-attributes
    # Field order matches jest/vitest coverage table: Stmts, Branch, Funcs, Lines
    statement_pct: float = 100.0
    branch_pct: float = 100.0
    function_pct: float = 100.0
    line_pct: float = 100.0
    uncovered_statements: str = ""
    uncovered_branches: str = ""
    uncovered_functions: str = ""
    uncovered_lines: str = ""
    error: str = ""


def _pct(covered: int, total: int):
    # Istanbul always reports all metrics; total=0 means the file has no such constructs (e.g. no branches), which is vacuously 100% covered. This differs from LCOV where total=0 means the tool doesn't support the metric (e.g. PHP branch coverage).
    if total == 0:
        return 100.0
    return round(covered / total * 100, 1)


def _format_lines(lines: set[int]):
    if not lines:
        return ""
    return ", ".join(f"line {ln}" for ln in sorted(lines))


def _format_names(names: set[str]):
    if not names:
        return ""
    return ", ".join(sorted(names))


def _get_line(loc: _Location):
    return loc["start"]["line"]


def parse_coverage_json(coverage_dir: str, impl_file: str):
    """Parse coverage-final.json and return Coverage for the impl file."""
    coverage_path = os.path.join(coverage_dir, COVERAGE_JSON_FILENAME)
    if not os.path.exists(coverage_path):
        msg = f"{coverage_path} not found"
        logger.warning("coverage: %s", msg)
        return Coverage(error=msg)

    with open(coverage_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not data:
        msg = f"{coverage_path} is empty or invalid"
        logger.warning("coverage: %s", msg)
        return Coverage(error=msg)

    # coverage-final.json keys are absolute paths; find the entry matching impl_file
    raw_file_data = None
    for key, value in data.items():
        if not isinstance(key, str):
            continue
        if key.endswith(impl_file) or key.endswith(f"/{impl_file}"):
            raw_file_data = value
            break

    if not raw_file_data or not isinstance(raw_file_data, dict):
        msg = f"No entry matching {impl_file} in {coverage_path}, file_data={raw_file_data}"
        logger.warning("coverage: %s", msg)
        return Coverage(error=msg)

    file_data = validate_istanbul_file_data(raw_file_data)
    if not file_data:
        msg = f"Invalid coverage structure for {impl_file} in {coverage_path}"
        logger.warning("coverage: %s", msg)
        return Coverage(error=msg)

    s_map = file_data["s"]
    statement_map = file_data["statementMap"]
    f_map = file_data["f"]
    fn_map = file_data["fnMap"]
    b_map = file_data["b"]
    branch_map = file_data["branchMap"]

    # Statements
    statements_covered = 0
    uncovered_statement_lines = set[int]()
    for key, count in s_map.items():
        if count > 0:
            statements_covered += 1
        else:
            stmt_info = statement_map.get(key)
            if stmt_info:
                uncovered_statement_lines.add(_get_line(stmt_info))

    # Functions
    functions_covered = 0
    uncovered_function_names = set[str]()
    for key, count in f_map.items():
        if count > 0:
            functions_covered += 1
        else:
            fn_info = fn_map.get(key)
            if fn_info:
                name = fn_info.get(
                    "name", f"anonymous@line {_get_line(fn_info['loc'])}"
                )
                uncovered_function_names.add(name)

    # Branches
    branches_total = 0
    branches_covered = 0
    uncovered_branch_lines = set[int]()
    for key, counts in b_map.items():
        branches_total += len(counts)
        for i, count in enumerate(counts):
            if count > 0:
                branches_covered += 1
            else:
                branch_info = branch_map.get(key)
                if not branch_info:
                    continue
                locations = branch_info.get("locations", [])
                if i < len(locations):
                    uncovered_branch_lines.add(_get_line(locations[i]))
                else:
                    # Fallback to branch-level loc
                    uncovered_branch_lines.add(_get_line(branch_info["loc"]))

    # Lines: derived from statementMap - each unique line with a statement
    # A line is covered if at least one statement on that line is covered
    line_to_covered = dict[int, bool]()
    for key, count in s_map.items():
        stmt_info = statement_map.get(key)
        if not stmt_info:
            continue
        line = _get_line(stmt_info)
        if count > 0:
            line_to_covered[line] = True
        elif line not in line_to_covered:
            line_to_covered[line] = False

    lines_covered = 0
    uncovered_line_numbers = set[int]()
    for line, covered in line_to_covered.items():
        if covered:
            lines_covered += 1
        else:
            uncovered_line_numbers.add(line)

    return Coverage(
        statement_pct=_pct(statements_covered, len(s_map)),
        branch_pct=_pct(branches_covered, branches_total),
        function_pct=_pct(functions_covered, len(f_map)),
        line_pct=_pct(lines_covered, len(line_to_covered)),
        uncovered_statements=_format_lines(uncovered_statement_lines),
        uncovered_branches=_format_lines(uncovered_branch_lines),
        uncovered_functions=_format_names(uncovered_function_names),
        uncovered_lines=_format_lines(uncovered_line_numbers),
    )
