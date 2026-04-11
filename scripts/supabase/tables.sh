#!/bin/bash
# Usage: scripts/supabase/tables.sh [-p|--prod]
# Lists all tables in the public schema.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

source "$PROJECT_ROOT/.env"

ENV="dev"

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--prod) ENV="prod"; shift ;;
        *) echo "Usage: $0 [-p|--prod]"; exit 1 ;;
    esac
done

QUERY="SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"

if [[ "$ENV" == "prod" ]]; then
    psql "postgresql://postgres.awegqusxzsmlgxaxyyrq:$SUPABASE_DB_PASSWORD_PRD@aws-0-us-west-1.pooler.supabase.com:6543/postgres" -c "$QUERY"
else
    psql "postgresql://postgres.dkrxtcbaqzrodvsagwwn:$SUPABASE_DB_PASSWORD_DEV@aws-0-us-west-1.pooler.supabase.com:6543/postgres" -c "$QUERY"
fi
