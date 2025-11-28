#!/bin/sh
set -e

TABLE_NAME="${1:-llm_requests}"

SIZE_MB=$(PGPASSWORD="$SUPABASE_DB_PASSWORD_PRD" psql \
  -h "aws-0-us-west-1.pooler.supabase.com" \
  -U "postgres.awegqusxzsmlgxaxyyrq" \
  -d postgres \
  -p 6543 \
  -t \
  -c "SELECT pg_total_relation_size('$TABLE_NAME') / (1024 * 1024)")

echo "$SIZE_MB" | xargs
