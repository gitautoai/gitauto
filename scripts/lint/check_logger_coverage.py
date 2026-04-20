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


def check_block_exits(block, path, violations):
    for i, stmt in enumerate(block):
        if isinstance(stmt, (ast.Return, ast.Continue, ast.Break)):
            if i == 0 or not is_logger_call(block[i - 1]):
                kind = type(stmt).__name__.lower()
                violations.append(
                    f"{path}:{stmt.lineno}: {kind} without preceding logger call"
                )


def check_if_branches(node, path, violations):
    first_body = next((s for s in node.body if not is_docstring(s)), None)
    if first_body is not None and not is_logger_call(first_body):
        violations.append(
            f"{path}:{first_body.lineno}: if/elif body does not start with logger call"
        )
    if node.orelse and not (
        len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If)
    ):
        first_else = next((s for s in node.orelse if not is_docstring(s)), None)
        if first_else is not None and not is_logger_call(first_else):
            violations.append(
                f"{path}:{first_else.lineno}: else body does not start with logger call"
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
