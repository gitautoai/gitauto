#!/bin/bash
# Usage: scripts/supabase/tables.sh <--dev|--prd>
# Lists all tables in the public schema. Requires explicit --dev or --prd.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

source "$PROJECT_ROOT/.env"

ENV=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dev) ENV="dev"; shift ;;
        -p|--prd) ENV="prd"; shift ;;
        *) echo "Usage: $0 <--dev|--prd>"; exit 1 ;;
    esac
done

if [[ -z "$ENV" ]]; then
    echo "Error: must specify --dev or --prd"
    echo "Usage: $0 <--dev|--prd>"
    exit 1
fi

QUERY="SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"

if [[ "$ENV" == "prd" ]]; then
    psql "postgresql://postgres.awegqusxzsmlgxaxyyrq:$SUPABASE_DB_PASSWORD_PRD@aws-0-us-west-1.pooler.supabase.com:6543/postgres" -c "$QUERY"
else
    psql "postgresql://postgres.dkrxtcbaqzrodvsagwwn:$SUPABASE_DB_PASSWORD_DEV@aws-0-us-west-1.pooler.supabase.com:6543/postgres" -c "$QUERY"
fi
