#!/bin/bash

# DataMind NL2SQL - Startup Script
# Starts both backend and frontend servers

set -e

BACKEND_PORT=8000
FRONTEND_PORT=3000
DB_EXPLORER_PORT=3001
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$PROJECT_ROOT/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   DataMind NL2SQL Startup Script      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Function to kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}⚠ Port $port is in use by PID $pid${NC}"
        echo -e "${YELLOW}  Killing process...${NC}"
        kill -9 $pid 2>/dev/null || true
        sleep 1
        echo -e "${GREEN}✓ Process killed${NC}"
    else
        echo -e "${GREEN}✓ Port $port is available${NC}"
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}[1/7] Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}✗ Node.js/npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites satisfied${NC}"
echo ""

# Kill existing processes on ports
echo -e "${BLUE}[2/7] Checking ports...${NC}"
kill_port $BACKEND_PORT
kill_port $FRONTEND_PORT
kill_port $DB_EXPLORER_PORT
echo ""

# Activate virtual environment and start backend
echo -e "${BLUE}[3/7] Starting Backend API...${NC}"
cd "$PROJECT_ROOT"

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠ Virtual environment not found, creating...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start backend in background
# Use the venv's python directly instead of relying on PATH
nohup "$PROJECT_ROOT/venv/bin/uvicorn" app.main:app --reload --port $BACKEND_PORT > logs/backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Check if backend started successfully
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Backend started on http://localhost:$BACKEND_PORT (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}✗ Failed to start backend${NC}"
    cat logs/backend.log
    exit 1
fi
echo ""

# Start frontend
echo -e "${BLUE}[4/7] Starting Frontend...${NC}"
cd "$PROJECT_ROOT/frontend"

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠ node_modules not found, installing dependencies...${NC}"
    npm install
fi

# Start frontend in background
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
echo -e "${YELLOW}  Waiting for frontend to compile...${NC}"
sleep 5

# Check if frontend started successfully
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Frontend started on http://localhost:$FRONTEND_PORT (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${RED}✗ Failed to start frontend${NC}"
    cat ../logs/frontend.log
    exit 1
fi
echo ""

# Start DB Explorer demo (standalone read-only UI under db-explorer/)
echo -e "${BLUE}[5/7] Starting DB Explorer demo...${NC}"
DBE_DIR="$PROJECT_ROOT/db-explorer"
DBE_VENV="$DBE_DIR/.venv"
if [ -d "$DBE_DIR" ]; then
    if [ ! -d "$DBE_VENV" ]; then
        echo -e "${YELLOW}⚠ DB Explorer venv not found, creating...${NC}"
        python3 -m venv "$DBE_VENV"
    fi
    # shellcheck disable=SC1091
    source "$DBE_VENV/bin/activate"
    pip install -q -r "$DBE_DIR/requirements.txt"
    cd "$DBE_DIR"
    nohup "$DBE_VENV/bin/uvicorn" main:app --host 0.0.0.0 --port "$DB_EXPLORER_PORT" > "$PROJECT_ROOT/logs/db-explorer.log" 2>&1 &
    DB_EXPLORER_PID=$!
    sleep 1
    if ps -p $DB_EXPLORER_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✓ DB Explorer on http://localhost:$DB_EXPLORER_PORT (PID: $DB_EXPLORER_PID)${NC}"
        echo $DB_EXPLORER_PID > "$PROJECT_ROOT/logs/db-explorer.pid"
    else
        echo -e "${YELLOW}⚠ DB Explorer failed to start. See logs/db-explorer.log${NC}"
        DB_EXPLORER_PID=""
    fi
    cd "$PROJECT_ROOT"
else
    echo -e "${YELLOW}⚠ db-explorer/ not found, skipping demo${NC}"
    DB_EXPLORER_PID=""
    cd "$PROJECT_ROOT"
fi
echo ""

# Save PIDs for later
echo $BACKEND_PID > "$PROJECT_ROOT/logs/backend.pid"
echo $FRONTEND_PID > "$PROJECT_ROOT/logs/frontend.pid"

# Display status
echo -e "${BLUE}[6/7] Services Status:${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  Backend API:   ${GREEN}http://localhost:$BACKEND_PORT${NC}"
echo -e "  API Docs:      ${GREEN}http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "  Frontend:      ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
if [ -n "$DB_EXPLORER_PID" ]; then
    echo -e "  DB Explorer:   ${GREEN}http://localhost:$DB_EXPLORER_PORT${NC}"
fi
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${BLUE}[7/7] Logs:${NC}"
echo -e "  Backend:     ${YELLOW}tail -f logs/backend.log${NC}"
echo -e "  Frontend:    ${YELLOW}tail -f logs/frontend.log${NC}"
if [ -n "$DB_EXPLORER_PID" ]; then
    echo -e "  DB Explorer: ${YELLOW}tail -f logs/db-explorer.log${NC}"
fi
echo ""

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         DataMind is ready!             ║${NC}"
echo -e "${GREEN}║                                        ║${NC}"
echo -e "${GREEN}║  App:        http://localhost:3000    ║${NC}"
if [ -n "$DB_EXPLORER_PID" ]; then
    echo -e "${GREEN}║  DB Explorer: http://localhost:$DB_EXPLORER_PORT    ║${NC}"
fi
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}Press Ctrl+C to stop all services...${NC}"
echo ""

# Trap Ctrl+C to cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    
    if [ -f "$PROJECT_ROOT/logs/backend.pid" ]; then
        BACKEND_PID=$(cat "$PROJECT_ROOT/logs/backend.pid")
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            kill $BACKEND_PID 2>/dev/null || true
            echo -e "${GREEN}✓ Backend stopped${NC}"
        fi
        rm "$PROJECT_ROOT/logs/backend.pid"
    fi
    
    if [ -f "$PROJECT_ROOT/logs/frontend.pid" ]; then
        FRONTEND_PID=$(cat "$PROJECT_ROOT/logs/frontend.pid")
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            kill $FRONTEND_PID 2>/dev/null || true
            echo -e "${GREEN}✓ Frontend stopped${NC}"
        fi
        rm "$PROJECT_ROOT/logs/frontend.pid"
    fi

    if [ -f "$PROJECT_ROOT/logs/db-explorer.pid" ]; then
        DB_EXPLORER_PID=$(cat "$PROJECT_ROOT/logs/db-explorer.pid")
        if ps -p $DB_EXPLORER_PID > /dev/null 2>&1; then
            kill $DB_EXPLORER_PID 2>/dev/null || true
            echo -e "${GREEN}✓ DB Explorer stopped${NC}"
        fi
        rm "$PROJECT_ROOT/logs/db-explorer.pid"
    fi
    
    echo -e "${GREEN}Goodbye!${NC}"
    exit 0
}

trap cleanup INT TERM

# Keep script running
wait
