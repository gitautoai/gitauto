#!/bin/zsh

# Load environment variables
source .env

# Configuration
PORT=8000
NGROK_DOMAIN="gitauto.ngrok.dev"

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "Starting GitAuto development environment..."

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "Creating virtual environment..."
    python3 -m venv --upgrade-deps venv
    echo -e "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    # Activate existing virtual environment
    source venv/bin/activate
fi

echo -e "${GREEN}Virtual environment ready${NC}"

# Generate TypedDict schemas directly from PostgreSQL
echo -e "Generating TypedDict schemas..."
PGPASSWORD="$SUPABASE_DB_PASSWORD_DEV" psql -h "aws-0-us-west-1.pooler.supabase.com" -U postgres.dkrxtcbaqzrodvsagwwn -d postgres -p 6543 -t -c "
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' AND table_name NOT LIKE 'pg_%'
ORDER BY table_name, ordinal_position;
" | python3 -c "
import sys
import datetime
from collections import defaultdict

# Read schema data from stdin
tables = defaultdict(list)
for line in sys.stdin:
    if line.strip():
        parts = [p.strip() for p in line.split('|')]
        if len(parts) == 4:
            table_name, column_name, data_type, is_nullable = parts
            
            # Convert PostgreSQL types to Python types
            type_mapping = {
                'integer': 'int',
                'bigint': 'int',
                'text': 'str', 
                'character varying': 'str',
                'boolean': 'bool',
                'timestamp with time zone': 'datetime.datetime',
                'timestamp without time zone': 'datetime.datetime',
                'time without time zone': 'datetime.time',
                'uuid': 'str',
                'json': 'dict[str, Any]',
                'jsonb': 'dict[str, Any]',
                'real': 'float',
                'double precision': 'float',
                'numeric': 'float'
            }
            
            python_type = type_mapping.get(data_type, 'Any')
            if is_nullable == 'YES':
                python_type = f'{python_type} | None'
                
            tables[table_name].append(f'    {column_name}: {python_type}')

# Generate TypedDict file
with open('schemas/supabase/types.py', 'w') as f:
    f.write('import datetime\\n')
    f.write('from typing import Any\\n')
    f.write('from typing_extensions import TypedDict, NotRequired\\n')
    f.write('\\n\\n')
    
    # Auto-generated fields to exclude from Insert types
    auto_fields = {'id', 'created_at', 'updated_at'}
    
    for table_name in sorted(tables.keys()):
        class_name = ''.join(word.capitalize() for word in table_name.split('_'))
        
        # Generate base TypedDict
        f.write(f'class {class_name}(TypedDict):\\n')
        if tables[table_name]:
            f.write('\\n'.join(tables[table_name]) + '\\n')
        else:
            f.write('    pass\\n')
        f.write('\\n\\n')  # Two blank lines after base class
        
        # Generate Insert TypedDict (exclude auto-generated fields)
        insert_fields = []
        for field in tables[table_name]:
            field_name = field.strip().split(':')[0].strip()
            if field_name not in auto_fields:
                # Make all fields in Insert type NotRequired for flexibility
                field_type = ':'.join(field.strip().split(':')[1:]).strip()
                insert_fields.append(f'    {field_name}: NotRequired[{field_type}]')
        
        if insert_fields:
            f.write(f'class {class_name}Insert(TypedDict):\\n')
            f.write('\\n'.join(insert_fields) + '\\n')
            # Only add two blank lines if not the last table
            if table_name != sorted(tables.keys())[-1]:
                f.write('\\n\\n')

print(f'Generated {len(tables)*2} TypedDict classes (base + Insert) directly from PostgreSQL')
"

# Function to cleanup background processes
cleanup() {
    echo -e "\nShutting down services..."
    # Kill ngrok (background job)
    if [ ! -z "$NGROK_PID" ] && kill -0 "$NGROK_PID" 2>/dev/null; then
        echo -e "Stopping ngrok..."
        kill "$NGROK_PID"
    fi
    deactivate 2>/dev/null || true
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start ngrok in background (logs hidden)
echo -e "Starting ngrok tunnel..."
ngrok http --config=ngrok.yml --domain=${NGROK_DOMAIN} ${PORT} > /dev/null 2>&1 &
NGROK_PID=$!

# Wait for ngrok to be ready (check API endpoint)
echo -e "Waiting for ngrok to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

echo -e "${GREEN}ngrok started!${NC}"
echo -e "ngrok: https://${NGROK_DOMAIN}"
echo -e "FastAPI: http://localhost:${PORT}"
echo -e "\n${GREEN}Starting FastAPI server (logs below)...${NC}"
echo -e "Press Ctrl+C to stop both services\n"

# Start uvicorn in foreground (logs visible)
uvicorn main:app --reload --port ${PORT} --log-level warning
