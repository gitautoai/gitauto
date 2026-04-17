from services.jest.format_coverage_comment import format_coverage_comment
from services.jest.parse_coverage_json import Coverage


def test_full_coverage():
    cov = Coverage()
    result = format_coverage_comment(cov, "src/utils.ts")
    assert "## Coverage" in result
    assert "`src/utils.ts`" in result
    assert "| 100.0% | 100.0% | 100.0% | 100.0% |" in result
    assert "Uncovered" not in result


def test_partial_coverage_with_uncovered():
    cov = Coverage(
        statement_pct=90.0,
        branch_pct=75.0,
        function_pct=50.0,
        line_pct=85.0,
        uncovered_statements="line 10",
        uncovered_branches="line 25, line 30",
        uncovered_functions="unusedFn",
        uncovered_lines="line 10",
    )
    result = format_coverage_comment(cov, "src/auth.ts")
    assert "| 90.0% | 75.0% | 50.0% | 85.0% |" in result
    assert "- Uncovered statements: line 10" in result
    assert "- Uncovered branches: line 25, line 30" in result
    assert "- Uncovered functions: unusedFn" in result
    assert "- Uncovered lines: line 10" in result


def test_only_branches_uncovered():
    cov = Coverage(
        branch_pct=83.33,
        uncovered_branches="line 15",
    )
    result = format_coverage_comment(cov, "src/index.ts")
    assert "- Uncovered branches: line 15" in result
    assert "Uncovered statements" not in result
    assert "Uncovered functions" not in result
    assert "Uncovered lines" not in result


def test_blank_line_between_table_and_uncovered():
    cov = Coverage(branch_pct=50.0, uncovered_branches="line 5")
    result = format_coverage_comment(cov, "src/foo.ts")
    lines = result.split("\n")
    # Table row is followed by blank line, then uncovered details
    table_row_idx = next(
        i for i, line in enumerate(lines) if line.startswith("| ") and "%" in line
    )
    assert lines[table_row_idx + 1] == ""
    assert lines[table_row_idx + 2].startswith("- Uncovered")
