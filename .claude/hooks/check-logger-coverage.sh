#!/bin/bash
# PostToolUse on Edit|Write|MultiEdit: check logger coverage per CLAUDE.md.
# Blocks Claude (decision:block) when violations are found in the edited .py file
# so Claude fixes before continuing.

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')

# Only check .py files inside this project.
case "$FILE" in
    /Users/rwest/Repositories/gitauto/*.py) ;;
    *) exit 0 ;;
esac

# Skip tests, scripts, schemas, virtualenvs.
case "$FILE" in
    */test_*.py|*/conftest.py) exit 0 ;;
    /Users/rwest/Repositories/gitauto/scripts/*) exit 0 ;;
    /Users/rwest/Repositories/gitauto/schemas/*) exit 0 ;;
    */.venv/*|*/venv/*) exit 0 ;;
esac

OUTPUT=$(python3 /Users/rwest/Repositories/gitauto/scripts/lint/check_logger_coverage.py "$FILE" 2>&1)
STATUS=$?
if [ $STATUS -eq 0 ]; then
    exit 0
fi

jq -n --arg reason "BLOCKED: Logger coverage violations per CLAUDE.md. Fix these before continuing:
$OUTPUT" '{decision: "block", reason: $reason}'
exit 2
