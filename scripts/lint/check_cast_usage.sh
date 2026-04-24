#!/bin/bash
# Detect `cast` usage from typing module in staged Python implementation files.
# Rule: No cast in impl files — fix underlying types or use isinstance narrowing.
# Allowed in test files (test_*.py, conftest.py) for TypedDict fixtures.
# Allowed in utils/error/handle_exceptions.py: the generic decorator pattern with ParamSpec + TypeVar genuinely can't round-trip types without cast (async wrapper's Coroutine[...R] vs declared Callable[P, R]; helper returns typed Any).
# Allowed in main.py: AWS Lambda hands the handler an untyped dict and we dispatch on event["triggerType"] before narrowing to the matching TypedDict. isinstance can't narrow a TypedDict, and a fresh annotated variable violates the "no var: type = value" rule in CLAUDE.md, so a single cast is the cleanest narrowing path.
set -uo pipefail

STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=d -- '*.py' \
    | grep -v '^\.\?venv/' \
    | grep -v '^schemas/' \
    | grep -vE '(^|/)test_' \
    | grep -vE '(^|/)conftest\.py$' \
    | grep -v '^utils/error/handle_exceptions\.py$' \
    | grep -v '^main\.py$')

if [ -z "$STAGED_PY_FILES" ]; then
    exit 0
fi

FAILED=0
for file in $STAGED_PY_FILES; do
    # Match "from typing import ... cast ..." or standalone "cast(" usage
    import_match=$(grep -nE '^\s*from\s+typing\s+import\s+.*\bcast\b' "$file" || true)
    usage_match=$(grep -nE '\bcast\s*\(' "$file" | grep -vE '^\s*#' || true)
    if [ -n "$import_match" ] || [ -n "$usage_match" ]; then
        echo "CAST USAGE in $file:"
        [ -n "$import_match" ] && echo "$import_match"
        [ -n "$usage_match" ] && echo "$usage_match"
        FAILED=1
    fi
done

if [ "$FAILED" -ne 0 ]; then
    echo ""
    echo "FAILED: cast() is prohibited in implementation files."
    echo "Use isinstance narrowing or proper SDK types instead."
    exit 1
fi
