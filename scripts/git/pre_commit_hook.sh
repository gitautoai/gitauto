#!/bin/bash
# Git pre-commit hook. No stashing - runs on the working directory as-is.
# Install: ln -sf ../../scripts/git/pre_commit_hook.sh .git/hooks/pre-commit
set -uo pipefail

echo "=== Pre-commit hook ==="

# pip freeze
pip freeze > requirements.txt && git add requirements.txt

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

# CloudFormation template validation for staged infrastructure files
STAGED_CFN_FILES=$(git diff --cached --name-only --diff-filter=d -- 'infrastructure/*.yml')
if [ -n "$STAGED_CFN_FILES" ]; then
    echo "--- CloudFormation validation ---"
    for cfn_file in $STAGED_CFN_FILES; do
        if aws cloudformation validate-template --template-body "file://$cfn_file" --region us-west-1 > /dev/null 2>&1; then
            echo "  $cfn_file: OK"
        else
            echo "FAILED: $cfn_file failed CloudFormation validation."
            aws cloudformation validate-template --template-body "file://$cfn_file" --region us-west-1
            exit 1
        fi
    done
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

# Concurrent heavy checks (flake8, pylint, pyright, pytest)
echo "--- flake8 + pylint + pyright + pytest (concurrent) ---"
scripts/lint/pre_commit_parallel_checks.sh
