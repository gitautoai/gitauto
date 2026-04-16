#!/bin/bash
# Bash hook: Block --no-verify on git commit
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# Extract only the git commit portion (before any && or ; chain), then strip the message
COMMIT_CMD=$(echo "$CMD" | grep -oE '(^|&&|;)\s*git commit[^&;]*' | head -1)
if [ -n "$COMMIT_CMD" ]; then
  # Strip commit message to avoid false positives
  FLAGS=$(echo "$COMMIT_CMD" | sed 's/ -m .*//; s/ -m".*//; s/ -m$//')
  if echo "$FLAGS" | grep -q -- "--no-verify"; then
    jq -n '{
      "decision": "block",
      "reason": "BLOCKED: --no-verify is not allowed. Commit without it."
    }'
    exit 2
  fi
fi

exit 0
