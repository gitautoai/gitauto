#!/bin/bash
# Bash hook: Block "Spent X" / "Spent the morning" / "Spent yesterday" openers in social-media posts inside gh pr bodies. Wes hates this opener pattern; vary it instead.
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# Only check gh pr edit / gh pr create
if ! echo "$CMD" | grep -qE 'gh pr (edit|create)\b'; then
  exit 0
fi

# Match "Spent " at the start of a line or after a paragraph break, followed by a word (duration or noun).
# Examples that trip: "Spent three hours", "Spent the morning", "Spent yesterday", "Spent days".
if echo "$CMD" | grep -qE '(^|\\n|\n)Spent [A-Za-z0-9]'; then
  jq -n '{
    "decision": "block",
    "reason": "BLOCKED: \"Spent X\" opener in PR body social post. Wes hates this pattern. Rewrite the opener to lead with the finding, the customer impact, or a question. Run scripts/git/recent_social_posts.sh to see varied openers used recently."
  }'
  exit 2
fi

exit 0
