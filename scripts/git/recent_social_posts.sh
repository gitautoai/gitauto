#!/bin/bash
# Usage: ./recent_social_posts.sh [gitauto|wes]
# Shows recent social media posts from merged PRs.
# Without argument: shows all posts.
# With "gitauto": shows only GitAuto posts.
# With "wes": shows only Wes posts.

FILTER="${1:-}"

if [ "$FILTER" = "gitauto" ]; then
    SECTION="## Social Media Post (GitAuto)"
elif [ "$FILTER" = "wes" ]; then
    SECTION="## Social Media Post (Wes)"
else
    SECTION="## Social Media Post"
fi

# Fetch PR bodies as JSON array, then extract posts with separators using Python
export SECTION
gh pr list --state merged --limit 10 --json body --jq '.[].body' \
    | python3 -c '
import os, sys

section = os.environ["SECTION"]
text = sys.stdin.read()

bodies = []
current = []
for line in text.split("\n"):
    if line.startswith("## Summary") and current:
        bodies.append("\n".join(current))
        current = [line]
    else:
        current.append(line)
if current:
    bodies.append("\n".join(current))

count = 0
for body in bodies:
    lines = body.split("\n")
    in_section = False
    post_lines = []
    for line in lines:
        if line.startswith(section):
            in_section = True
            continue
        elif in_section and line.startswith("## "):
            in_section = False
            continue
        elif in_section:
            stripped = line.strip()
            if stripped:
                post_lines.append(stripped)
    if post_lines:
        count += 1
        if count > 1:
            print("")
            print("---")
            print("")
        print("[" + str(count) + "] " + post_lines[0])
        for pl in post_lines[1:]:
            print(pl)
'
