#!/bin/bash
# Runs pylint, pyright, and pytest concurrently during pre-commit.
# All three only run when Python files are staged.
set -uo pipefail

STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=d -- '*.py' | grep -v '^\.\?venv/' | grep -v '^schemas/')

PYLINT_OUT=$(mktemp)
PYRIGHT_OUT=$(mktemp)
PYTEST_OUT=$(mktemp)
cleanup() { rm -f "$PYLINT_OUT" "$PYRIGHT_OUT" "$PYTEST_OUT"; }
trap cleanup EXIT

PIDS=()
NAMES=()
OUTPUTS=()

if [ -z "$STAGED_PY_FILES" ]; then
    echo "No Python files staged, skipping pylint/pyright/pytest"
    exit 0
fi

# shellcheck disable=SC2086
pylint $STAGED_PY_FILES > "$PYLINT_OUT" 2>&1 &
PIDS+=($!); NAMES+=("pylint"); OUTPUTS+=("$PYLINT_OUT")

pyright > "$PYRIGHT_OUT" 2>&1 &
PIDS+=($!); NAMES+=("pyright"); OUTPUTS+=("$PYRIGHT_OUT")

python -m pytest > "$PYTEST_OUT" 2>&1 &
PIDS+=($!); NAMES+=("pytest"); OUTPUTS+=("$PYTEST_OUT")

FAILED=0
for i in "${!PIDS[@]}"; do
    wait "${PIDS[$i]}"
    EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
        echo ""
        echo "=== ${NAMES[$i]} FAILED (exit $EXIT_CODE) ==="
        cat "${OUTPUTS[$i]}"
        FAILED=1
    else
        echo "=== ${NAMES[$i]} PASSED ==="
    fi
done

exit $FAILED
