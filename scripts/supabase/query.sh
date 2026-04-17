#!/bin/bash
# Usage: scripts/supabase/query.sh <--dev|--prd> [-x] "SQL query"
# Requires explicit --dev or --prd. Use -x for vertical display.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

source "$PROJECT_ROOT/.env"

ENV=""
QUERY=""
PSQL_FLAGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dev) ENV="dev"; shift ;;
        -p|--prd) ENV="prd"; shift ;;
        -x) PSQL_FLAGS="-x"; shift ;;
        *) QUERY="$1"; shift ;;
    esac
done

if [[ -z "$ENV" ]]; then
    echo "Error: must specify --dev or --prd"
    echo "Usage: $0 <--dev|--prd> [-x] \"SQL query\""
    exit 1
fi

if [[ -z "$QUERY" ]]; then
    echo "Usage: $0 <--dev|--prd> [-x] \"SQL query\""
    echo "  -x  Vertical display (expanded output)"
    exit 1
fi

if [[ "$ENV" == "prd" ]]; then
    psql "postgresql://postgres.awegqusxzsmlgxaxyyrq:$SUPABASE_DB_PASSWORD_PRD@aws-0-us-west-1.pooler.supabase.com:6543/postgres" $PSQL_FLAGS -c "$QUERY"
else
    psql "postgresql://postgres.dkrxtcbaqzrodvsagwwn:$SUPABASE_DB_PASSWORD_DEV@aws-0-us-west-1.pooler.supabase.com:6543/postgres" $PSQL_FLAGS -c "$QUERY"
fi
