#!/bin/bash
# PostToolUse on Edit|Write|MultiEdit: reject hard-wrapped comments per CLAUDE.md.
# Blocks Claude (decision:block) when a single sentence is broken across multiple # lines so Claude rewrites before continuing.

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')

case "$FILE" in
    "$REPO_ROOT"/*.py) ;;
    *) exit 0 ;;
esac

case "$FILE" in
    */.venv/*|*/venv/*) exit 0 ;;
esac

OUTPUT=$(python3 "$REPO_ROOT/scripts/lint/check_comment_line_breaks.py" "$FILE" 2>&1)
STATUS=$?
if [ $STATUS -eq 0 ]; then
    exit 0
fi

jq -n --arg reason "BLOCKED: Hard-wrapped comments per CLAUDE.md. Rewrite as one line per sentence (let the editor wrap visually):
$OUTPUT" '{decision: "block", reason: $reason}'
exit 2
