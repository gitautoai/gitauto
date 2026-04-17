#!/bin/bash
# Usage: scripts/supabase/daily_cost_report.sh [YYYY-MM-DD] [--dev|--prd]
# Defaults to today (PT timezone) and production database.
# Shows LLM cost breakdown grouped by repo/PR, with trigger/model detail.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

DATE=""
ENV_FLAG="--prd"

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev) ENV_FLAG="--dev"; shift ;;
        --prod|--prd) ENV_FLAG="--prd"; shift ;;
        *) DATE="$1"; shift ;;
    esac
done

# Default to today in PT
if [[ -z "$DATE" ]]; then
    DATE=$(TZ="America/Los_Angeles" date +%Y-%m-%d)
fi

NEXT_DATE=$(date -j -f "%Y-%m-%d" -v+1d "$DATE" +%Y-%m-%d 2>/dev/null || date -d "$DATE + 1 day" +%Y-%m-%d)

WHERE="u.created_at >= '${DATE}T00:00:00-07:00' AND u.created_at < '${NEXT_DATE}T00:00:00-07:00'"

echo "=== Daily LLM Cost Report: $DATE (PT) ==="
echo ""
echo "--- By PR (grouped) ---"

"$SCRIPT_DIR/query.sh" $ENV_FLAG "
SELECT
  u.owner_name || '/' || u.repo_name AS repo,
  u.pr_number AS pr,
  COUNT(lr.id) AS calls,
  SUM(lr.input_tokens) AS in_tok,
  SUM(lr.output_tokens) AS out_tok,
  ROUND(SUM(lr.input_cost_usd)::numeric, 2) AS in_cost,
  ROUND(SUM(lr.output_cost_usd)::numeric, 2) AS out_cost,
  ROUND(SUM(lr.total_cost_usd)::numeric, 2) AS total
FROM usage u
JOIN llm_requests lr ON lr.usage_id = u.id
WHERE $WHERE
GROUP BY u.owner_name, u.repo_name, u.pr_number
ORDER BY total DESC
"

echo ""
echo "--- Breakdown by trigger/model (within each PR) ---"

"$SCRIPT_DIR/query.sh" $ENV_FLAG "
SELECT
  u.owner_name || '/' || u.repo_name AS repo,
  u.pr_number AS pr,
  u.trigger,
  REPLACE(REPLACE(REPLACE(lr.model_id, 'claude-', ''), '-4-6', '46'), '-4-5', '45') AS model,
  COUNT(lr.id) AS calls,
  ROUND(SUM(lr.input_cost_usd)::numeric, 2) AS in_cost,
  ROUND(SUM(lr.output_cost_usd)::numeric, 2) AS out_cost,
  ROUND(SUM(lr.total_cost_usd)::numeric, 2) AS total
FROM usage u
JOIN llm_requests lr ON lr.usage_id = u.id
WHERE $WHERE
GROUP BY u.owner_name, u.repo_name, u.pr_number, u.trigger, lr.model_id
ORDER BY u.owner_name, u.repo_name, u.pr_number, total DESC
"

echo ""
echo "=== Totals ==="

"$SCRIPT_DIR/query.sh" $ENV_FLAG "
SELECT
  COUNT(DISTINCT u.id) AS runs,
  COUNT(DISTINCT u.owner_name || '/' || u.repo_name || '#' || u.pr_number) AS prs,
  COUNT(lr.id) AS calls,
  SUM(lr.input_tokens) AS in_tokens,
  SUM(lr.output_tokens) AS out_tokens,
  ROUND(SUM(lr.input_cost_usd)::numeric, 2) AS in_cost,
  ROUND(SUM(lr.output_cost_usd)::numeric, 2) AS out_cost,
  ROUND(SUM(lr.total_cost_usd)::numeric, 2) AS total
FROM usage u
JOIN llm_requests lr ON lr.usage_id = u.id
WHERE $WHERE
"

echo ""
echo "=== Top 5 Most Expensive PRs (input growth pattern) ==="

"$SCRIPT_DIR/query.sh" $ENV_FLAG "
SELECT
  u.owner_name || '/' || u.repo_name AS repo,
  u.pr_number AS pr,
  COUNT(lr.id) AS calls,
  MIN(lr.input_length) AS min_in_len,
  MAX(lr.input_length) AS max_in_len,
  ROUND(MAX(lr.input_length)::numeric / NULLIF(MIN(lr.input_length), 0), 1) AS growth_x,
  ROUND(SUM(lr.total_cost_usd)::numeric, 2) AS total
FROM usage u
JOIN llm_requests lr ON lr.usage_id = u.id
WHERE $WHERE
GROUP BY u.owner_name, u.repo_name, u.pr_number
ORDER BY total DESC
LIMIT 5
"
