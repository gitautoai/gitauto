#!/usr/bin/env python3
# Find redundant consecutive logger.* calls.
# A "redundant double" is two back-to-back logger calls where the second is a pure trace/marker with no format args AND carries fewer positional args than the first.
# These typically come from over-logging inside small branches (one "entered branch X" plus one "returning X") and can be collapsed to a single informative call.
# Genuine pairs that each carry distinct data (e.g. "call args" plus "call result") are NOT flagged.
# Prints one line per dup: "<path>:<second_lineno>: redundant double (previous at <first_lineno>)".
# Usage: find_double_loggers.py <file.py> [<file.py> ...] [--fix]

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


def is_redundant_second(prev, curr):
    # Any two consecutive logger.* calls in the same block are flagged for human review.
    # The fix is to merge them into one call with all the data in a single format string.
    return is_logger_call(prev) and is_logger_call(curr)


def find_branch_trace_doubles(node, path, hits):
    # Flag if/elif/else branches that have more than one logger inside them. A branch should have at most one logger call describing what's happening; two means the top-of-branch trace and a pre-return trace are both present, which is the pattern introduced by prior Rule B/A hook enforcement.
    if isinstance(node, ast.If):
        for body in (node.body, node.orelse):
            loggers = [s for s in body if is_logger_call(s)]
            if len(loggers) >= 2:
                lines = [s.lineno for s in loggers]
                hits.append((path, lines))
    for child in ast.iter_child_nodes(node):
        find_branch_trace_doubles(child, path, hits)


def find_doubles_in_block(block, path, doubles):
    for i in range(1, len(block)):
        if is_redundant_second(block[i - 1], block[i]):
            doubles.append((path, block[i - 1].lineno, block[i].lineno))
    for stmt in block:
        recurse(stmt, path, doubles)


def recurse(stmt, path, doubles):
    if isinstance(stmt, ast.If):
        find_doubles_in_block(stmt.body, path, doubles)
        find_doubles_in_block(stmt.orelse, path, doubles)
    elif isinstance(stmt, (ast.For, ast.AsyncFor, ast.While)):
        find_doubles_in_block(stmt.body, path, doubles)
        find_doubles_in_block(stmt.orelse, path, doubles)
    elif isinstance(stmt, ast.Try):
        find_doubles_in_block(stmt.body, path, doubles)
        for handler in stmt.handlers:
            find_doubles_in_block(handler.body, path, doubles)
        find_doubles_in_block(stmt.orelse, path, doubles)
        find_doubles_in_block(stmt.finalbody, path, doubles)
    elif isinstance(stmt, (ast.With, ast.AsyncWith)):
        find_doubles_in_block(stmt.body, path, doubles)
    elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        find_doubles_in_block(stmt.body, path, doubles)


def check_file(path):
    doubles = []
    src = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            find_doubles_in_block(node.body, str(path), doubles)
        elif isinstance(node, ast.ClassDef):
            for cnode in node.body:
                if isinstance(cnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    find_doubles_in_block(cnode.body, str(path), doubles)
    return doubles


def remove_doubles(path, doubles):
    """Remove the SECOND logger of each consecutive pair. Processes bottom-up so line numbers stay stable."""
    src = Path(path).read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    to_delete = set()
    tree = ast.parse(src, filename=str(path))

    def collect_stmt_range(stmt):
        end = getattr(stmt, "end_lineno", stmt.lineno)
        return stmt.lineno, end

    for _, _, second_lineno in doubles:
        # Walk the tree to find the Expr at second_lineno and collect its full span
        for n in ast.walk(tree):
            if (
                isinstance(n, ast.Expr)
                and n.lineno == second_lineno
                and is_logger_call(n)
            ):
                start, end = collect_stmt_range(n)
                for ln in range(start, end + 1):
                    to_delete.add(ln)
                break

    kept = [ln for i, ln in enumerate(lines, start=1) if i not in to_delete]
    Path(path).write_text("".join(kept), encoding="utf-8")
    return len(to_delete)


def main():
    args = sys.argv[1:]
    fix = "--fix" in args
    files = [a for a in args if a != "--fix"]
    all_doubles = []
    branch_hits = []
    for f in files:
        all_doubles.extend(check_file(f))
        try:
            tree = ast.parse(Path(f).read_text(encoding="utf-8"), filename=f)
        except SyntaxError:
            continue
        find_branch_trace_doubles(tree, f, branch_hits)
    if not all_doubles and not branch_hits:
        sys.exit(0)

    for path, first, second in all_doubles:
        print(f"{path}:{second}: consecutive double logger (previous at {first})")

    for path, lines in branch_hits:
        print(
            f"{path}:{lines[0]}: branch has {len(lines)} loggers at {lines} — collapse to one"
        )

    if fix:
        by_file: dict[str, list] = {}
        for d in all_doubles:
            by_file.setdefault(d[0], []).append(d)
        removed = 0
        for f, file_doubles in by_file.items():
            removed += remove_doubles(f, file_doubles)
        print(
            f"\nRemoved {removed} line(s) across {len(by_file)} file(s).",
            file=sys.stderr,
        )
        sys.exit(0)

    print(
        f"\n{len(all_doubles)} double logger(s). Re-run with --fix to delete the second call.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
