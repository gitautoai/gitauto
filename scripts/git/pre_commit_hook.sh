#!/bin/bash
# Git pre-commit hook. No stashing - runs on the working directory as-is.
# Install: ln -sf ../../scripts/git/pre_commit_hook.sh .git/hooks/pre-commit
set -uo pipefail

echo "=== Pre-commit hook ==="

# Auto-increment patch version (major version updated manually)
CURRENT=$(grep '^version' pyproject.toml | sed 's/.*"\(.*\)"/\1/')
MAJOR=$(echo "$CURRENT" | cut -d. -f1)
MINOR=$(echo "$CURRENT" | cut -d. -f2)
PATCH=$(echo "$CURRENT" | cut -d. -f3)
NEW_VERSION="$MAJOR.$MINOR.$((PATCH + 1))"
sed -i '' "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml

# Lock dependencies (pyproject.toml → uv.lock)
uv lock --quiet && git add pyproject.toml uv.lock

# Generate TypedDict schemas
python3 schemas/supabase/generate_types.py && git add schemas/supabase/

# Get staged Python files (excluding deleted, venv, schemas)
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=d -- '*.py' | grep -v '^venv/' | grep -v '^schemas/')

# Format and auto-fix staged Python files
if [ -n "$STAGED_PY_FILES" ]; then
    # shellcheck disable=SC2086
    black $STAGED_PY_FILES
    # shellcheck disable=SC2086
    git add $STAGED_PY_FILES

    # shellcheck disable=SC2086
    ruff check --fix $STAGED_PY_FILES
    # shellcheck disable=SC2086
    git add $STAGED_PY_FILES
fi

# Markdownlint for staged .md files
STAGED_MD_FILES=$(git diff --cached --name-only --diff-filter=d -- '*.md')
if [ -n "$STAGED_MD_FILES" ]; then
    echo "--- markdownlint ---"
    # shellcheck disable=SC2086
    npx --yes markdownlint-cli $STAGED_MD_FILES
    if [ $? -ne 0 ]; then
        echo "FAILED: Fix markdownlint violations before committing."
        exit 1
    fi
fi

# CloudFormation (CFN) template validation for staged infrastructure files (errors only, ignore warnings)
STAGED_CFN_FILES=$(git diff --cached --name-only --diff-filter=d -- 'infrastructure/*.yml')
if [ -n "$STAGED_CFN_FILES" ]; then
    echo "--- cfn-lint (CloudFormation) ---"
    # shellcheck disable=SC2086
    if ! cfn-lint -- $STAGED_CFN_FILES; then
        echo "FAILED: Fix cfn-lint errors before committing."
        exit 1
    fi
fi

# Print statement check (whole repo, excluding dirs)
echo "--- ruff T201 print check ---"
ruff check --select=T201 . --exclude schemas/,venv/,scripts/
if [ $? -ne 0 ]; then
    echo "FAILED: Remove print statements before committing."
    exit 1
fi

# Built-in logging check
echo "--- builtin logging check ---"
scripts/lint/check_builtin_logging.sh
if [ $? -ne 0 ]; then exit 1; fi

# Test file checks (new files need tests, changed impl needs changed test)
echo "--- test file check ---"
scripts/lint/check_test_files.sh
if [ $? -ne 0 ]; then exit 1; fi

# Concurrent heavy checks (pylint, pyright, pytest)
echo "--- pylint + pyright + pytest (concurrent) ---"
scripts/lint/pre_commit_parallel_checks.sh
