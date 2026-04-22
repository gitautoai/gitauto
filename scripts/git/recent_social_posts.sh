#!/bin/bash
# Usage: ./recent_social_posts.sh [section-key]
# Shows recent social media posts from merged PRs, grouped by section.
#
# Section keys: gitauto-x, gitauto-linkedin, wes-x, wes-linkedin, hn
# Without argument: shows all five sections sequentially.

FILTER="${1:-}"

case "$FILTER" in
    "")
        "$0" gitauto-x
        echo ""; echo "==="; echo ""
        "$0" gitauto-linkedin
        echo ""; echo "==="; echo ""
        "$0" wes-x
        echo ""; echo "==="; echo ""
        "$0" wes-linkedin
        echo ""; echo "==="; echo ""
        "$0" hn
        exit 0
        ;;
    gitauto-x)       SECTION="## Social Media Post (GitAuto on X)" ;;
    gitauto-linkedin) SECTION="## Social Media Post (GitAuto on LinkedIn)" ;;
    wes-x)           SECTION="## Social Media Post (Wes on X)" ;;
    wes-linkedin)    SECTION="## Social Media Post (Wes on LinkedIn)" ;;
    hn)              SECTION="## Social Media Post (HN Title)" ;;
    *)
        echo "Unknown section key: $FILTER" >&2
        echo "Valid keys: gitauto-x, gitauto-linkedin, wes-x, wes-linkedin, hn" >&2
        exit 1
        ;;
esac

echo "[$FILTER]"

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

if count == 0:
    print("No recent posts found. This is not a problem - just proceed.")
'
