#!/bin/bash
# Usage: scripts/supabase/describe.sh [-p|--prod] <table_name>
# Shows columns, types, and nullability for a table.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

source "$PROJECT_ROOT/.env"

ENV="dev"
TABLE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--prod) ENV="prod"; shift ;;
        *) TABLE="$1"; shift ;;
    esac
done

if [[ -z "$TABLE" ]]; then
    echo "Usage: $0 [-p|--prod] <table_name>"
    exit 1
fi

QUERY="SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '$TABLE' ORDER BY ordinal_position;"

if [[ "$ENV" == "prod" ]]; then
    psql "postgresql://postgres.awegqusxzsmlgxaxyyrq:$SUPABASE_DB_PASSWORD_PRD@aws-0-us-west-1.pooler.supabase.com:6543/postgres" -c "$QUERY"
else
    psql "postgresql://postgres.dkrxtcbaqzrodvsagwwn:$SUPABASE_DB_PASSWORD_DEV@aws-0-us-west-1.pooler.supabase.com:6543/postgres" -c "$QUERY"
fi
