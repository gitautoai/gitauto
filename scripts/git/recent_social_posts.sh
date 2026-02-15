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

gh pr list --state merged --limit 10 --json body --jq '.[].body' \
    | grep -A1 "$SECTION" \
    | grep -v "^--$" \
    | grep -v "## Social Media Post"
