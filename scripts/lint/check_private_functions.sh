#!/bin/bash
# Detect _-prefixed private function definitions in staged Python files.
# Rule: No private functions — inline or create a dedicated file.
# Excludes test files (test_*.py, conftest.py) and __init__.py.
set -uo pipefail

STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=d -- '*.py' \
    | grep -v '^\.\?venv/' \
    | grep -v '^schemas/' \
    | grep -vE '(^|/)test_' \
    | grep -vE '(^|/)conftest\.py$' \
    | grep -vE '__init__\.py$')

if [ -z "$STAGED_PY_FILES" ]; then
    exit 0
fi

FAILED=0
for file in $STAGED_PY_FILES; do
    # Match "def _name(" but exclude dunder methods "def __name__("
    matches=$(grep -nE '^\s*def\s+_[a-zA-Z]' "$file" \
        | grep -vE 'def\s+__[a-zA-Z_]+__\s*\(' || true)
    if [ -n "$matches" ]; then
        echo "PRIVATE FUNCTION in $file:"
        echo "$matches"
        FAILED=1
    fi
done

if [ "$FAILED" -ne 0 ]; then
    echo ""
    echo "FAILED: Private functions (_-prefixed) are prohibited."
    echo "Either inline the logic or create a dedicated file with a public function."
    exit 1
fi
