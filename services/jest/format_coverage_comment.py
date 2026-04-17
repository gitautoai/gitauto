from services.jest.parse_coverage_json import Coverage
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def format_coverage_comment(coverage: Coverage, impl_file: str):
    # Column order matches jest/vitest coverage table: Stmts, Branch, Funcs, Lines
    lines = [
        "## Coverage",
        "",
        f"`{impl_file}`",
        "",
        "| Stmts | Branch | Funcs | Lines |",
        "|-------|--------|-------|-------|",
        f"| {coverage.statement_pct}% | {coverage.branch_pct}% | {coverage.function_pct}% | {coverage.line_pct}% |",
    ]
    uncovered_parts = []
    if coverage.uncovered_statements:
        uncovered_parts.append(
            f"- Uncovered statements: {coverage.uncovered_statements}"
        )
    if coverage.uncovered_branches:
        uncovered_parts.append(f"- Uncovered branches: {coverage.uncovered_branches}")
    if coverage.uncovered_functions:
        uncovered_parts.append(f"- Uncovered functions: {coverage.uncovered_functions}")
    if coverage.uncovered_lines:
        uncovered_parts.append(f"- Uncovered lines: {coverage.uncovered_lines}")
    if uncovered_parts:
        lines.append("")
        lines.extend(uncovered_parts)
    return "\n".join(lines)
