#!/bin/bash
# Usage: scripts/supabase/query.sh [-p|--prod] [-x] "SQL query"
# Defaults to development database. Use -x for vertical display.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

source "$PROJECT_ROOT/.env"

ENV="dev"
QUERY=""
PSQL_FLAGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--prod) ENV="prod"; shift ;;
        -x) PSQL_FLAGS="-x"; shift ;;
        *) QUERY="$1"; shift ;;
    esac
done

if [[ -z "$QUERY" ]]; then
    echo "Usage: $0 [-p|--prod] [-x] \"SQL query\""
    echo "  -x  Vertical display (expanded output)"
    exit 1
fi

if [[ "$ENV" == "prod" ]]; then
    psql "postgresql://postgres.awegqusxzsmlgxaxyyrq:$SUPABASE_DB_PASSWORD_PRD@aws-0-us-west-1.pooler.supabase.com:6543/postgres" $PSQL_FLAGS -c "$QUERY"
else
    psql "postgresql://postgres.dkrxtcbaqzrodvsagwwn:$SUPABASE_DB_PASSWORD_DEV@aws-0-us-west-1.pooler.supabase.com:6543/postgres" $PSQL_FLAGS -c "$QUERY"
fi
