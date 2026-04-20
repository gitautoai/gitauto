#!/bin/bash
# Filter then run logger coverage check.
# Usage: check_logger_coverage.sh <file.py> [<file.py> ...]

set -uo pipefail

if [ $# -eq 0 ]; then
    exit 0
fi

FILES=()
for f in "$@"; do
    case "$f" in
        */test_*.py|*/conftest.py|scripts/*|*/scripts/*|schemas/*|*/schemas/*|.venv/*|*/.venv/*|venv/*|*/venv/*)
            continue
            ;;
        *.py)
            FILES+=("$f")
            ;;
    esac
done

if [ ${#FILES[@]} -eq 0 ]; then
    exit 0
fi

python3 "$(dirname "$0")/check_logger_coverage.py" "${FILES[@]}"
