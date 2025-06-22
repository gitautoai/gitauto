#!/bin/zsh

# Configuration
PORT=8000
NGROK_DOMAIN="gitauto.ngrok.dev"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
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
