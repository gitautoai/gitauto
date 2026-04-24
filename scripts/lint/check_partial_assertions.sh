#!/bin/bash
# Block partial assertions in test files: `assert X in Y`, `assert X not in Y`
# These accept infinite wrong answers. Use `assert result == expected` instead.
set -uo pipefail

STAGED_TEST_FILES=$(git diff --cached --name-only --diff-filter=d -- '*.py' \
    | grep -E '(^|/)test_' || true)

if [ -z "$STAGED_TEST_FILES" ]; then
    exit 0
fi

FAIL=0

for file in $STAGED_TEST_FILES; do
    # Match `assert X in Y` and `assert X not in Y` (partial assertions)
    # Allow: `assert X in {literals}` or `assert X in (literals)` — value validation, not partial
    # Allow: `for X in Y` comprehensions — iteration, not a partial assert.
    matches=$(grep -nE '^\s+assert\s+.+\s+(not\s+)?in\s+' "$file" \
        | grep -vE '^\s*#' \
        | grep -vE '\bin\s+\{' \
        | grep -vE '\bin\s+\(' \
        | grep -vE '\s+for\s+\S+\s+in\s+' || true)

    if [ -n "$matches" ]; then
        echo "PARTIAL ASSERTION in $file:"
        echo "$matches"
        echo "  Use 'assert result == expected' instead."
        echo ""
        FAIL=1
    fi
done

if [ $FAIL -ne 0 ]; then
    echo "FAILED: Replace partial assertions (in/not in) with exact == matches."
    exit 1
fi
