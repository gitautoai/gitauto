#!/usr/bin/env python3
# Exits 0 if the cached diff for <file> contains only logger/comment/whitespace changes, 1 otherwise.
# A "logger-only" diff is one where every parsable Python statement that was added or removed is a logger.*(...) call.
# The staged/unstaged-test check can safely skip files that pass this filter because they have no behaviour change to test.

import ast
import subprocess
import sys


LOGGER_METHODS = {"info", "warning", "warn", "error", "debug", "exception", "critical"}


def is_logger_call(node):
    if not isinstance(node, ast.Expr):
        return False
    call = node.value
    if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
        return False
    if call.func.attr not in LOGGER_METHODS:
        return False
    base = call.func.value
    if isinstance(base, ast.Name):
        return "logger" in base.id.lower()
    if isinstance(base, ast.Attribute):
        return "logger" in base.attr.lower()
    return False


class LoggerStripper(ast.NodeTransformer):
    def visit(self, node):
        # Recurse first so nested logger calls are removed.
        node = self.generic_visit(node)
        if is_logger_call(node):
            return None
        return node


def get_file_content(rev, path):
    res = subprocess.run(
        ["git", "show", f"{rev}:{path}"], capture_output=True, text=True, check=False
    )
    if res.returncode != 0:
        return ""
    return res.stdout


def strip_loggers(source):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    LoggerStripper().visit(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def statements_differ_only_in_loggers(old_src, new_src):
    old_stripped = strip_loggers(old_src)
    new_stripped = strip_loggers(new_src)
    if old_stripped is None or new_stripped is None:
        return False
    return old_stripped == new_stripped


def main():
    if len(sys.argv) != 2:
        print("usage: is_logger_only_diff.py <file>", file=sys.stderr)
        sys.exit(2)
    path = sys.argv[1]
    old_src = get_file_content("HEAD", path)
    new_src = get_file_content(":0", path)  # staged index
    if not new_src:
        sys.exit(1)
    sys.exit(0 if statements_differ_only_in_loggers(old_src, new_src) else 1)


if __name__ == "__main__":
    main()
