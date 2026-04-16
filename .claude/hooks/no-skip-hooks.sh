#!/bin/bash
# Bash hook: Block --no-verify on git commit
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# Strip everything after -m to avoid matching flag text inside commit messages
CMD_FLAGS=$(echo "$CMD" | sed 's/ -m .*//; s/ -m".*//; s/ -m$//')
if echo "$CMD_FLAGS" | grep -qE "git commit.*--no-verify|--no-verify.*git commit"; then
  jq -n '{
    "decision": "block",
    "reason": "BLOCKED: --no-verify is not allowed. Commit without it."
  }'
  exit 2
fi

exit 0
