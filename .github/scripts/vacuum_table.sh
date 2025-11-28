#!/bin/sh
set -e

TABLE_NAME="${1:-llm_requests}"

echo "Running VACUUM FULL on $TABLE_NAME..."
PGPASSWORD="$SUPABASE_DB_PASSWORD_PRD" psql \
  -h "aws-0-us-west-1.pooler.supabase.com" \
  -U "postgres.awegqusxzsmlgxaxyyrq" \
  -d postgres \
  -p 6543 \
  -c "VACUUM FULL $TABLE_NAME"

echo "✓ Vacuum completed for $TABLE_NAME"
