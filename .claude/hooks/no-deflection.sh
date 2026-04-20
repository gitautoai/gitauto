#!/bin/bash
# Stop hook: Scold Claude when it tries to dodge work by blaming pre-existing state, other sessions, scope creep, or offering "just skip this file" options.
INPUT=$(cat)
MSG=$(echo "$INPUT" | jq -r '.last_assistant_message // ""' | tr '[:upper:]' '[:lower:]')

if echo "$MSG" | grep -qE "pre-existing|preexisting|not my change|aren.t my change|these aren.t mine|another session|other session|scope creep|scope-creep|scope expansion|unrelated change|unrelated mechanical|out of scope|out-of-scope|grandfathered|papers? over|not scoped|exempt this file|skip this file|revert my (handler )?edit|follow-up pr|separate pr|\\bblast radius\\b"; then
  jq -n '{
    "decision": "block",
    "reason": "You are dodging work. ALL failing checks, pre-existing or not, are YOUR problem. Fix them. No excuses about scope, other sessions, or follow-up PRs."
  }'
  exit 2
fi

exit 0
