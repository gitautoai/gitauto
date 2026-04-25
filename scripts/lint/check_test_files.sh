#!/bin/bash
# Check 1: Newly staged Python files must have a corresponding test file.
# Check 2: If an impl file is changed, its test file must also be staged.
set -uo pipefail

# Directories/files to exclude from the check
EXCLUDE_PATTERN='^(\.?venv/|schemas/|scripts/|infrastructure/|\.github/|services/types/)'
EXCLUDE_FILES='(conftest\.py|__init__\.py|main\.py)$'

# Get staged Python impl files (exclude test files and excluded dirs/files)
STAGED_IMPL_NEW=$(git diff --cached --name-only --diff-filter=A -- '*.py' \
    | grep -vE "$EXCLUDE_PATTERN" \
    | grep -vE "$EXCLUDE_FILES" \
    | grep -v '/test_' \
    | grep -v '^test_' || true)

STAGED_IMPL_MODIFIED=$(git diff --cached --name-only --diff-filter=M -- '*.py' \
    | grep -vE "$EXCLUDE_PATTERN" \
    | grep -vE "$EXCLUDE_FILES" \
    | grep -v '/test_' \
    | grep -v '^test_' || true)

STAGED_ALL=$(git diff --cached --name-only || true)
FAIL=0

# Resolve the PR base. origin/main is the default target branch for this repo.
# If the branch hasn't been pushed or origin/main isn't present (fresh clone), fall back gracefully.
PR_BASE="origin/main"
if ! git rev-parse --verify --quiet "$PR_BASE" >/dev/null 2>&1; then
    PR_BASE=""
fi

# Check 1: New impl files must have a test file (staged or already existing)
if [ -n "$STAGED_IMPL_NEW" ]; then
    for file in $STAGED_IMPL_NEW; do
        dir=$(dirname "$file")
        base=$(basename "$file")
        test_file="$dir/test_$base"
        # Check if test file is staged or already exists on disk
        if ! echo "$STAGED_ALL" | grep -qF "$test_file" && [ ! -f "$test_file" ]; then
            echo "MISSING TEST FILE: $file -> expected $test_file"
            FAIL=1
        fi
    done
fi

# Check 2: Changed impl files with existing test files must have test also staged
# Skip if the staged diff is comment-only (lines starting with # after +/-) or logger-only.
if [ -n "$STAGED_IMPL_MODIFIED" ]; then
    for file in $STAGED_IMPL_MODIFIED; do
        # Skip comment-only diffs (all added/removed lines are comments or blank)
        if git diff --cached -- "$file" | grep -E '^[+-]' | grep -vE '^(\+\+\+|---)' \
            | grep -vE '^[+-]\s*#' | grep -vE '^[+-]\s*$' | grep -q .; then
            : # Has non-comment changes
        else
            continue
        fi
        # Skip logger-only diffs (statements that survive logger stripping are identical between HEAD and index).
        if python3 "$(dirname "$0")/is_logger_only_diff.py" "$file"; then
            continue
        fi
        dir=$(dirname "$file")
        base=$(basename "$file")
        test_file="$dir/test_$base"
        if [ -f "$test_file" ]; then
            if echo "$STAGED_ALL" | grep -qF "$test_file"; then
                : # test file is staged → OK
            elif [ -n "$PR_BASE" ] && ! git diff --quiet "$PR_BASE"..HEAD -- "$test_file" 2>/dev/null; then
                : # test file changed in earlier commits in this PR → OK
            elif ! git diff --quiet "$test_file" 2>/dev/null; then
                # Unstaged test changes exist — could be related (Claude wrote tests but didn't stage) or unrelated (other-session WIP). Script can't tell. Prompt Claude to verify and stage if related; do not FAIL automatically.
                echo "TEST FILE HAS UNSTAGED CHANGES: $test_file"
                echo "  Check if those unstaged changes are the tests for $file's staged changes."
                echo "  - If yes (you wrote them): ask the user to stage $test_file."
                echo "  - If no (unrelated WIP from another session): leave unstaged and add new tests for $file before committing."
            else
                echo "TEST NOT UPDATED: $file changed but $test_file has no test coverage for it in this PR"
                FAIL=1
            fi
        fi
    done
fi

if [ $FAIL -ne 0 ]; then
    echo "FAILED: Stage the missing test files or create them before committing."
    exit 1
fi
