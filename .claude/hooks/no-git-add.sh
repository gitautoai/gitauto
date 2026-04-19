#!/bin/bash
# Bash hook: Block git add — ask user to stage files instead
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

if echo "$CMD" | grep -qE '(^|\s|&&|;)\s*git add\b'; then
  jq -n '{
    "decision": "block",
    "reason": "BLOCKED: Do not run git add. Ask the user to stage files. Other sessions may have unstaged changes that would pollute the PR."
  }'
  exit 2
fi

exit 0
