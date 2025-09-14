#!/bin/bash

# LGTM Script - Automated workflow with clear logging
# Exit on any failure to avoid false positives

set -e

echo "=== LGTM WORKFLOW STARTING ==="
echo "$(date): Starting LGTM workflow"

echo ""
echo "=== STEP 1: Activate virtual environment ==="
source venv/bin/activate
echo "✓ Virtual environment activated"

echo ""
echo "=== STEP 2: Black formatting ==="
black .
echo "✓ Black formatting completed"

echo ""
echo "=== STEP 3: Ruff linting ==="
ruff check . --fix
echo "✓ Ruff linting completed"

echo ""
echo "=== STEP 4: Get modified files ==="
MODIFIED_FILES=$(git diff --name-only HEAD)
echo "Modified files:"
echo "$MODIFIED_FILES"

echo ""
echo "=== STEP 5: Pylint on modified Python files ==="
PYTHON_FILES=$(echo "$MODIFIED_FILES" | grep "\.py$" | while read f; do [ -f "$f" ] && echo "$f"; done | xargs echo)
if [ -n "$PYTHON_FILES" ]; then
    echo "Running pylint on: $PYTHON_FILES"
    pylint --fail-under=10.0 $PYTHON_FILES
    echo "✓ Pylint PASSED (score >= 10.0)"
else
    echo "No modified Python files to check"
fi

echo ""
echo "=== STEP 6: Pyright on modified Python files ==="
if [ -n "$PYTHON_FILES" ]; then
    echo "Running pyright on: $PYTHON_FILES"
    pyright $PYTHON_FILES
    echo "✓ Pyright PASSED (0 errors)"
else
    echo "No modified Python files to check"
fi

echo ""
echo "=== STEP 7: Pytest ==="
python -m pytest -r fE -x
echo "✓ Pytest PASSED"

echo ""
echo "=== STEP 8: Check current branch ==="
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"
if [ "$CURRENT_BRANCH" = "main" ]; then
    echo "❌ Cannot run on main branch"
    exit 1
fi
echo "✓ Not on main branch"

echo ""
echo "=== STEP 9: Merge latest main ==="
git fetch origin main && git merge origin/main
echo "✓ Merged latest main"

echo ""
echo "=== STEP 10: Add changes ==="
git add .
echo "✓ Changes added"

echo ""
echo "=== STEP 11: Commit ==="
echo "Enter commit message:"
read -r COMMIT_MESSAGE
git commit -m "$COMMIT_MESSAGE"
echo "✓ Changes committed"

echo ""
echo "=== STEP 12: Push ==="
git push
echo "✓ Changes pushed"

echo ""
echo "=== LGTM WORKFLOW COMPLETED SUCCESSFULLY ==="
echo "$(date): All steps passed"
