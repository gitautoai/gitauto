#!/bin/zsh

# Load environment variables
source .env

# Configuration
PORT=8000
LOG_LEVEL=${1:-warning}  # Default to warning, but allow override with first argument

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "Starting GitAuto development environment..."

# Create .venv if it doesn't exist (uv's default)
if [ ! -d ".venv" ]; then
    echo -e "Installing dependencies..."
    uv sync
fi
source .venv/bin/activate

echo -e "${GREEN}Virtual environment ready${NC}"

# Generate TypedDict schemas directly from PostgreSQL
python3 schemas/supabase/generate_types.py

# Function to cleanup background processes
cleanup() {
    echo -e "\nShutting down services..."
    # Kill smee-client (background job)
    if [ ! -z "$SMEE_PID" ] && kill -0 "$SMEE_PID" 2>/dev/null; then
        echo -e "Stopping smee-client..."
        kill "$SMEE_PID"
    fi
    deactivate 2>/dev/null || true
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Check SMEE_URL is set
if [ -z "$SMEE_URL" ]; then
    echo -e "Error: SMEE_URL is not set in .env"
    echo -e "Go to https://smee.io and click 'Start a new channel' to get a URL"
    exit 1
fi

# Start smee-client in background (forwards GitHub webhooks to localhost)
echo -e "Starting smee-client..."
npx smee-client --url ${SMEE_URL} --target http://localhost:${PORT}/webhook > /dev/null 2>&1 &
SMEE_PID=$!

# Wait for smee-client to start
sleep 2

echo -e "${GREEN}smee-client started!${NC}"
echo -e "Smee: ${SMEE_URL}"
echo -e "FastAPI: http://localhost:${PORT}"
echo -e "\n${GREEN}Starting FastAPI server (logs below)...${NC}"
echo -e "Press Ctrl+C to stop both services\n"

# Configure Python logging level to match uvicorn
if [ "${LOG_LEVEL}" = "info" ]; then
    python3 -c "import logging; logging.basicConfig(level=logging.INFO)" &
fi

# Start uvicorn in foreground (logs visible)
uvicorn main:app --reload --port ${PORT} --log-level ${LOG_LEVEL}
