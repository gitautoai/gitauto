#!/bin/bash
# Git pre-commit hook. Does NOT auto-stage — user handles staging.
# Install: ln -sf ../../scripts/git/pre_commit_hook.sh .git/hooks/pre-commit
set -uo pipefail

# Activate .venv so tools (ruff, black, pylint, pyright, pytest) are on PATH
# shellcheck disable=SC1091
[ -f .venv/bin/activate ] && source .venv/bin/activate

echo "=== Pre-commit hook ==="

# Block commits directly to main
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "main" ]; then
    echo "FAILED: Cannot commit directly to main. Use a feature branch."
    exit 1
fi

# Keep local main in sync with remote (no checkout needed)
git fetch origin main:main 2>/dev/null || true

# Auto-increment version (major updated manually)
# New files → minor bump (1.X.0), modifications only → patch bump (1.0.X)
CURRENT=$(grep '^version' pyproject.toml | sed 's/.*"\(.*\)"/\1/')
MAJOR=$(echo "$CURRENT" | cut -d. -f1)
MINOR=$(echo "$CURRENT" | cut -d. -f2)
PATCH=$(echo "$CURRENT" | cut -d. -f3)
# Minor bump only for new impl .py files (not tests, scripts, schemas, infra)
if git diff --cached --diff-filter=A --name-only -- '*.py' | grep -Ev '(^|/)test_|conftest\.py$|^schemas/|^infrastructure/|^scripts/' | grep -q .; then
    NEW_VERSION="$MAJOR.$((MINOR + 1)).0"
else
    NEW_VERSION="$MAJOR.$MINOR.$((PATCH + 1))"
fi
sed -i '' "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml

# Lock dependencies (pyproject.toml → uv.lock)
uv lock --quiet && git add pyproject.toml uv.lock

# Generate TypedDict schemas
python3 schemas/supabase/generate_types.py && git add schemas/supabase/

# Get staged Python files (excluding deleted, .venv, schemas)
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=d -- '*.py' | grep -v '^\.\?venv/' | grep -v '^schemas/')

# Format staged Python files (user re-stages if needed)
if [ -n "$STAGED_PY_FILES" ]; then
    # shellcheck disable=SC2086
    black $STAGED_PY_FILES
    # shellcheck disable=SC2086
    ruff check --fix $STAGED_PY_FILES
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
ruff check --select=T201 . --exclude schemas/,.venv/,scripts/,**/test_*.py,**/conftest.py
if [ $? -ne 0 ]; then
    echo "FAILED: Remove print statements before committing."
    exit 1
fi

# Built-in logging check
echo "--- builtin logging check ---"
scripts/lint/check_builtin_logging.sh
if [ $? -ne 0 ]; then exit 1; fi

# Logger coverage check (staged Python files)
echo "--- logger coverage check ---"
if [ -n "$STAGED_PY_FILES" ]; then
    # shellcheck disable=SC2086
    scripts/lint/check_logger_coverage.sh $STAGED_PY_FILES
    if [ $? -ne 0 ]; then
        echo "FAILED: Add logger calls per CLAUDE.md (see violations above)."
        exit 1
    fi
fi

# Test file checks (new files need tests, changed impl needs changed test)
echo "--- test file check ---"
scripts/lint/check_test_files.sh
if [ $? -ne 0 ]; then exit 1; fi

# Partial assertion check (assert X in Y is prohibited, use assert X == Y)
echo "--- partial assertion check ---"
scripts/lint/check_partial_assertions.sh
if [ $? -ne 0 ]; then exit 1; fi

# Private function check (def _xxx is prohibited, inline or own file)
echo "--- private function check ---"
scripts/lint/check_private_functions.sh
if [ $? -ne 0 ]; then exit 1; fi

# Cast usage check (cast() is prohibited in impl files)
echo "--- cast usage check ---"
scripts/lint/check_cast_usage.sh
if [ $? -ne 0 ]; then exit 1; fi

# Comment line-break check (don't hard-wrap single sentences across # lines)
echo "--- comment line-break check ---"
if [ -n "$STAGED_PY_FILES" ]; then
    # shellcheck disable=SC2086
    python3 scripts/lint/check_comment_line_breaks.py $STAGED_PY_FILES
    if [ $? -ne 0 ]; then
        echo "FAILED: Rewrite hard-wrapped comments as one line per sentence."
        exit 1
    fi
fi

# Concurrent heavy checks (pylint, pyright, pytest)
echo "--- pylint + pyright + pytest (concurrent) ---"
scripts/lint/pre_commit_parallel_checks.sh
