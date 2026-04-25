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

# Pyright on staged files only — pyright still resolves cross-file types via imports, but errors are reported only for the files we pass. Avoids failing the commit on unrelated WIP elsewhere in the working tree.
# shellcheck disable=SC2086
pyright $STAGED_PY_FILES > "$PYRIGHT_OUT" 2>&1 &
PIDS+=($!); NAMES+=("pyright"); OUTPUTS+=("$PYRIGHT_OUT")

# Pytest target list: any staged test_*.py runs directly; any staged impl file runs its sibling test_<name>.py (if present). Both kinds get tested. Avoids slow whole-suite runs and unrelated failures from other WIP.
PYTEST_TARGETS=()
for f in $STAGED_PY_FILES; do
    base=$(basename "$f")
    if [[ "$base" == test_* ]]; then
        PYTEST_TARGETS+=("$f")
    else
        dir=$(dirname "$f")
        sibling_test="$dir/test_$base"
        if [ -f "$sibling_test" ]; then
            PYTEST_TARGETS+=("$sibling_test")
        fi
    fi
done
# Dedup
if [ ${#PYTEST_TARGETS[@]} -gt 0 ]; then
    UNIQUE_TARGETS=$(printf '%s\n' "${PYTEST_TARGETS[@]}" | sort -u)
    # shellcheck disable=SC2086
    python -m pytest $UNIQUE_TARGETS > "$PYTEST_OUT" 2>&1 &
    PIDS+=($!); NAMES+=("pytest"); OUTPUTS+=("$PYTEST_OUT")
else
    echo "No test targets for staged files, skipping pytest"
fi

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

# Auto-update pyright when its output reports a newer version is available.
# pyright-python wraps a downloaded binary; the warning means our pinned version is behind.
if grep -q "there is a new pyright version available" "$PYRIGHT_OUT"; then
    NEW_VERSION=$(grep "there is a new pyright version available" "$PYRIGHT_OUT" | sed -E 's/.*-> v([0-9.]+).*/\1/' | head -1)
    if [ -n "$NEW_VERSION" ]; then
        echo "--- auto-updating pyright to v$NEW_VERSION ---"
        if uv add --group dev "pyright==$NEW_VERSION" --quiet; then
            git add pyproject.toml uv.lock
        else
            echo "(failed to auto-update pyright)"
        fi
    fi
fi

exit $FAILED
