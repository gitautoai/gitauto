#!/bin/bash
# Stop hook: Scold Claude when it says "pre-existing"
INPUT=$(cat)
MSG=$(echo "$INPUT" | jq -r '.last_assistant_message // ""' | tr '[:upper:]' '[:lower:]')

if echo "$MSG" | grep -qE "pre-existing (issue|bug|problem|failure|error|test)|preexisting (issue|bug|problem|failure|error|test)"; then
  jq -n '{
    "decision": "block",
    "reason": "You just said pre-existing. ALL failing tests are YOUR problem. Fix them. No excuses."
  }'
  exit 2
fi

exit 0
