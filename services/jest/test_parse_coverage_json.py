import json
import os
import shutil

from services.jest.parse_coverage_json import (
    COVERAGE_JSON_FILENAME,
    Coverage,
    parse_coverage_json,
)

REAL_COVERAGE_PAYLOAD = os.path.join(
    os.path.dirname(__file__), "fixtures", "coverage-final.json"
)


def test_parse_coverage_json_full_coverage(tmp_path):
    """All statements, functions, branches covered -> 100% everywhere."""
    coverage_data = {
        "/tmp/clone/src/index.ts": {
            "s": {"0": 5, "1": 3},
            "f": {"0": 2},
            "b": {"0": [1, 1]},
            "branchMap": {
                "0": {
                    "type": "if",
                    "locations": [
                        {"start": {"line": 10, "column": 0}},
                        {"start": {"line": 12, "column": 0}},
                    ],
                }
            },
            "statementMap": {
                "0": {"start": {"line": 10, "column": 0}},
                "1": {"start": {"line": 12, "column": 0}},
            },
            "fnMap": {
                "0": {"name": "doStuff", "loc": {"start": {"line": 9, "column": 0}}}
            },
        }
    }
    with open(
        os.path.join(str(tmp_path), COVERAGE_JSON_FILENAME), "w", encoding="utf-8"
    ) as f:
        json.dump(coverage_data, f)

    result = parse_coverage_json(str(tmp_path), "src/index.ts")
    assert result.statement_pct == 100.0
    assert result.branch_pct == 100.0
    assert result.function_pct == 100.0
    assert result.line_pct == 100.0
    assert result.uncovered_branches == ""
    assert result.uncovered_lines == ""
    assert result.uncovered_functions == ""
    assert result.error == ""


def test_parse_coverage_json_partial_branch_coverage(tmp_path):
    """One branch alternative not covered -> uncovered_branches populated."""
    coverage_data = {
        "/tmp/clone/src/auth.ts": {
            "s": {"0": 5, "1": 0},
            "f": {"0": 2},
            "b": {"0": [3, 0], "1": [1, 1]},
            "branchMap": {
                "0": {
                    "type": "if",
                    "locations": [
                        {"start": {"line": 23, "column": 4}},
                        {"start": {"line": 25, "column": 4}},
                    ],
                },
                "1": {
                    "type": "cond-expr",
                    "locations": [
                        {"start": {"line": 30, "column": 10}},
                        {"start": {"line": 30, "column": 20}},
                    ],
                },
            },
            "statementMap": {
                "0": {"start": {"line": 23, "column": 0}},
                "1": {"start": {"line": 25, "column": 0}},
            },
            "fnMap": {
                "0": {"name": "auth", "loc": {"start": {"line": 20, "column": 0}}}
            },
        }
    }
    with open(
        os.path.join(str(tmp_path), COVERAGE_JSON_FILENAME), "w", encoding="utf-8"
    ) as f:
        json.dump(coverage_data, f)

    result = parse_coverage_json(str(tmp_path), "src/auth.ts")
    assert result.branch_pct == 75.0
    assert "line 25" in result.uncovered_branches
    assert result.statement_pct == 50.0
    assert "line 25" in result.uncovered_statements
    assert result.error == ""


def test_parse_coverage_json_uncovered_function(tmp_path):
    """Function with 0 calls -> uncovered_functions populated."""
    coverage_data = {
        "/tmp/clone/src/utils.ts": {
            "s": {"0": 1},
            "f": {"0": 1, "1": 0},
            "b": {},
            "branchMap": {},
            "statementMap": {"0": {"start": {"line": 1, "column": 0}}},
            "fnMap": {
                "0": {"name": "usedFn", "loc": {"start": {"line": 1, "column": 0}}},
                "1": {"name": "unusedFn", "loc": {"start": {"line": 10, "column": 0}}},
            },
        }
    }
    with open(
        os.path.join(str(tmp_path), COVERAGE_JSON_FILENAME), "w", encoding="utf-8"
    ) as f:
        json.dump(coverage_data, f)

    result = parse_coverage_json(str(tmp_path), "src/utils.ts")
    assert result.function_pct == 50.0
    assert "unusedFn" in result.uncovered_functions
    assert result.error == ""


def test_parse_coverage_json_missing_file(tmp_path):
    """coverage-final.json doesn't exist -> returns error."""
    result = parse_coverage_json(str(tmp_path), "src/index.ts")
    assert result.error != ""


def test_parse_coverage_json_no_matching_file(tmp_path):
    """coverage-final.json exists but doesn't contain the impl file."""
    coverage_data = {
        "/tmp/clone/src/other.ts": {
            "s": {},
            "f": {},
            "b": {},
            "branchMap": {},
            "statementMap": {},
            "fnMap": {},
        }
    }
    with open(
        os.path.join(str(tmp_path), COVERAGE_JSON_FILENAME), "w", encoding="utf-8"
    ) as f:
        json.dump(coverage_data, f)

    result = parse_coverage_json(str(tmp_path), "src/index.ts")
    assert result.error != ""


def test_parse_coverage_json_empty_file(tmp_path):
    """coverage-final.json is empty object -> returns error."""
    with open(
        os.path.join(str(tmp_path), COVERAGE_JSON_FILENAME), "w", encoding="utf-8"
    ) as f:
        json.dump({}, f)

    result = parse_coverage_json(str(tmp_path), "src/index.ts")
    assert result.error != ""


def test_parse_coverage_json_branch_fallback_to_loc(tmp_path):
    """When locations array is shorter than branch alternatives, use branch-level loc."""
    coverage_data = {
        "/tmp/clone/src/utils.ts": {
            "s": {"0": 1},
            "f": {"0": 1},
            "b": {"0": [1, 0]},
            "branchMap": {
                "0": {
                    "type": "binary-expr",
                    "loc": {"start": {"line": 55, "column": 0}},
                    "locations": [
                        {"start": {"line": 55, "column": 0}},
                    ],
                }
            },
            "statementMap": {"0": {"start": {"line": 55, "column": 0}}},
            "fnMap": {
                "0": {"name": "util", "loc": {"start": {"line": 55, "column": 0}}}
            },
        }
    }
    with open(
        os.path.join(str(tmp_path), COVERAGE_JSON_FILENAME), "w", encoding="utf-8"
    ) as f:
        json.dump(coverage_data, f)

    result = parse_coverage_json(str(tmp_path), "src/utils.ts")
    assert "line 55" in result.uncovered_branches


def test_parse_coverage_json_zero_totals(tmp_path):
    """File with no statements/functions/branches -> 100% (nothing to cover)."""
    coverage_data = {
        "/tmp/clone/src/empty.ts": {
            "s": {},
            "f": {},
            "b": {},
            "branchMap": {},
            "statementMap": {},
            "fnMap": {},
        }
    }
    with open(
        os.path.join(str(tmp_path), COVERAGE_JSON_FILENAME), "w", encoding="utf-8"
    ) as f:
        json.dump(coverage_data, f)

    result = parse_coverage_json(str(tmp_path), "src/empty.ts")
    assert result.statement_pct == 100.0
    assert result.branch_pct == 100.0
    assert result.function_pct == 100.0
    assert result.line_pct == 100.0
    assert result.error == ""


def test_parse_real_coverage_json(tmp_path):
    """Parse real coverage-final.json from website repo's is-test-file.ts."""
    shutil.copy(
        REAL_COVERAGE_PAYLOAD, os.path.join(str(tmp_path), COVERAGE_JSON_FILENAME)
    )
    result = parse_coverage_json(str(tmp_path), "utils/is-test-file.ts")
    assert result.error == ""
    assert result.statement_pct == 100.0
    assert result.branch_pct == 100.0
    assert result.function_pct == 100.0
    assert result.line_pct == 100.0
    assert result.uncovered_branches == ""
    assert result.uncovered_functions == ""
    assert result.uncovered_lines == ""


def test_coverage_data_defaults():
    """Coverage defaults to 100% and empty strings."""
    cov = Coverage()
    assert cov.statement_pct == 100.0
    assert cov.branch_pct == 100.0
    assert cov.function_pct == 100.0
    assert cov.line_pct == 100.0
    assert cov.uncovered_statements == ""
    assert cov.uncovered_branches == ""
    assert cov.uncovered_functions == ""
    assert cov.uncovered_lines == ""
    assert cov.error == ""
