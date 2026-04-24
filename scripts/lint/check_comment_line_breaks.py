#!/usr/bin/env python3
# Check for hard-wrapped comments per CLAUDE.md.
# Rule: don't break a single sentence across multiple # lines. If the first line has no sentence terminator AND the next same-indent # line starts with a lowercase letter, flag it.
# Usage: check_comment_line_breaks.py <file.py> [<file.py> ...]

import re
import sys
from pathlib import Path

COMMENT_LINE = re.compile(r"^(\s*)#\s?(.*)$")
PRAGMA = re.compile(r"^\s*#\s*(pylint:|type:|ruff:|noqa:|pyright:|coding:|!)")
SENTENCE_END = re.compile(r"""[.!?:;](\s*["')\]]*)\s*$""")
URL_END = re.compile(r"https?://\S+$")
BULLET_LINE = re.compile(r"^\s*[-*\d]+[.)\s]")
# Decorative divider lines (===, ---, ***, ###, etc.) with no prose. Allowed as the caller's visual separator, not a wrapped sentence.
DIVIDER_LINE = re.compile(r"^[\s\-=*#~_]+$")


def violations(path: Path):
    out = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for i in range(len(lines) - 1):
        m1 = COMMENT_LINE.match(lines[i])
        m2 = COMMENT_LINE.match(lines[i + 1])
        if not m1 or not m2:
            continue
        if PRAGMA.match(lines[i]) or PRAGMA.match(lines[i + 1]):
            continue
        if m1.group(1) != m2.group(1):
            continue
        first = m1.group(2).rstrip()
        second = m2.group(2).lstrip()
        if not first or not second:
            continue
        if BULLET_LINE.match(first) or BULLET_LINE.match(second):
            continue
        if DIVIDER_LINE.match(first) or DIVIDER_LINE.match(second):
            continue
        if SENTENCE_END.search(first):
            continue
        if URL_END.search(first):
            continue
        if not second[0].isalpha() or not second[0].islower():
            continue
        out.append(
            f"{path}:{i + 1}: hard-wrapped comment (line {i + 1} continues into {i + 2})"
        )
    return out


def main():
    if len(sys.argv) < 2:
        return 0
    all_violations = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        if not p.is_file():
            continue
        all_violations.extend(violations(p))
    if all_violations:
        print("\n".join(all_violations), file=sys.stderr)
        print(
            f"\n{len(all_violations)} hard-wrapped comment(s). Rewrite as one line per sentence.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
