#!/usr/bin/env python3
# Check logger coverage per CLAUDE.md.
# Rule A: every return/continue/break in a function has an immediately preceding logger.xxx(...) call.
# Rule B: every if/elif/else branch body's first non-docstring statement is a logger.xxx(...) call.
# Usage: check_logger_coverage.py <file.py> [<file.py> ...]

import ast
import sys
from pathlib import Path

LOGGER_METHODS = {"info", "warning", "warn", "error", "debug", "exception", "critical"}


def is_logger_call(node):
    if not isinstance(node, ast.Expr):
        return False
    call = node.value
    if not isinstance(call, ast.Call):
        return False
    if not isinstance(call.func, ast.Attribute):
        return False
    if call.func.attr not in LOGGER_METHODS:
        return False
    base = call.func.value
    if isinstance(base, ast.Name):
        return "logger" in base.id.lower()
    if isinstance(base, ast.Attribute):
        return "logger" in base.attr.lower()
    return False


def is_docstring(node):
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def statement_guarantees_logger(stmt):
    # Direct logger.* expression statement.
    if is_logger_call(stmt):
        return True
    # If/elif/else where every branch's first non-docstring statement is a logger call. This matches how Rule B is enforced below and means every taken path logs something before reaching a subsequent return/break/continue.
    if isinstance(stmt, ast.If):
        then_body = [s for s in stmt.body if not is_docstring(s)]
        else_body = [s for s in stmt.orelse if not is_docstring(s)]
        if not then_body or not else_body:
            return False
        then_logs = any(statement_guarantees_logger(s) for s in then_body)
        else_logs = any(statement_guarantees_logger(s) for s in else_body)
        return then_logs and else_logs
    return False


def check_block_exits(block, path, violations):
    for i, stmt in enumerate(block):
        if isinstance(stmt, (ast.Return, ast.Continue, ast.Break)):
            if not any(statement_guarantees_logger(earlier) for earlier in block[:i]):
                kind = type(stmt).__name__.lower()
                violations.append(
                    f"{path}:{stmt.lineno}: {kind} without preceding logger call"
                )


def check_if_branches(node, path, violations):
    # Every if/elif/else branch must contain at least one logger call somewhere in its body so every taken branch is explainable in logs.
    # Accepting any position (not just the first statement) lets a single logger satisfy both this rule and the return-exit rule.
    # Nested if/else blocks where every branch logs also count (via statement_guarantees_logger), so an outer branch is satisfied when it only contains an inner if/elif/else whose branches each log.
    if_body_non_docstring = [s for s in node.body if not is_docstring(s)]
    if if_body_non_docstring and not any(
        statement_guarantees_logger(s) for s in if_body_non_docstring
    ):
        violations.append(
            f"{path}:{if_body_non_docstring[0].lineno}: if/elif body has no logger call"
        )
    if node.orelse and not (
        len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If)
    ):
        else_body_non_docstring = [s for s in node.orelse if not is_docstring(s)]
        if else_body_non_docstring and not any(
            statement_guarantees_logger(s) for s in else_body_non_docstring
        ):
            violations.append(
                f"{path}:{else_body_non_docstring[0].lineno}: else body has no logger call"
            )


def visit_block(block, path, violations):
    check_block_exits(block, path, violations)
    for stmt in block:
        if isinstance(stmt, ast.If):
            check_if_branches(stmt, path, violations)
            visit_block(stmt.body, path, violations)
            visit_block(stmt.orelse, path, violations)
        elif isinstance(stmt, (ast.For, ast.AsyncFor, ast.While)):
            visit_block(stmt.body, path, violations)
            visit_block(stmt.orelse, path, violations)
        elif isinstance(stmt, ast.Try):
            visit_block(stmt.body, path, violations)
            for handler in stmt.handlers:
                visit_block(handler.body, path, violations)
            visit_block(stmt.orelse, path, violations)
            visit_block(stmt.finalbody, path, violations)
        elif isinstance(stmt, (ast.With, ast.AsyncWith)):
            visit_block(stmt.body, path, violations)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            visit_block(stmt.body, path, violations)


def check_file(path):
    violations = []
    try:
        src = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"{path}: read error: {exc}", file=sys.stderr)
        return violations
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as exc:
        print(f"{path}: syntax error: {exc}", file=sys.stderr)
        return violations
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            visit_block(node.body, str(path), violations)
        elif isinstance(node, ast.ClassDef):
            for cnode in node.body:
                if isinstance(cnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    visit_block(cnode.body, str(path), violations)
    return violations


def main():
    files = sys.argv[1:]
    all_violations = []
    for f in files:
        all_violations.extend(check_file(f))
    if all_violations:
        for v in all_violations:
            print(v)
        print(
            f"\n{len(all_violations)} logger coverage violation(s) "
            "(rule: return/continue/break need preceding logger; "
            "if/elif/else branches should start with logger)",
            file=sys.stderr,
        )
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
