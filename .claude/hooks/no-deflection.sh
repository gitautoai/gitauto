#!/bin/bash
# Stop hook: Scold Claude when it says "pre-existing"
INPUT=$(cat)
MSG=$(echo "$INPUT" | jq -r '.last_assistant_message // ""' | tr '[:upper:]' '[:lower:]')

if echo "$MSG" | grep -qE "pre-existing|preexisting|not my change|aren.t my change|these aren.t mine|another session|other session"; then
  jq -n '{
    "decision": "block",
    "reason": "You just said pre-existing. ALL failing tests are YOUR problem. Fix them. No excuses."
  }'
  exit 2
fi

exit 0
