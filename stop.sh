#!/bin/bash

# DataMind NL2SQL - Stop Script
# Stops both backend and frontend servers

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping DataMind services...${NC}"
echo ""

# Stop backend
if [ -f "$PROJECT_ROOT/logs/backend.pid" ]; then
    BACKEND_PID=$(cat "$PROJECT_ROOT/logs/backend.pid")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID 2>/dev/null || kill -9 $BACKEND_PID 2>/dev/null
        echo -e "${GREEN}✓ Backend stopped (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${YELLOW}⚠ Backend process not found${NC}"
    fi
    rm "$PROJECT_ROOT/logs/backend.pid"
else
    # Try to kill by port
    BACKEND_PID=$(lsof -ti:8000)
    if [ ! -z "$BACKEND_PID" ]; then
        kill -9 $BACKEND_PID 2>/dev/null
        echo -e "${GREEN}✓ Backend stopped (port 8000)${NC}"
    else
        echo -e "${YELLOW}⚠ No backend process on port 8000${NC}"
    fi
fi

# Stop frontend
if [ -f "$PROJECT_ROOT/logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$PROJECT_ROOT/logs/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID 2>/dev/null || kill -9 $FRONTEND_PID 2>/dev/null
        echo -e "${GREEN}✓ Frontend stopped (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend process not found${NC}"
    fi
    rm "$PROJECT_ROOT/logs/frontend.pid"
else
    # Try to kill by port
    FRONTEND_PID=$(lsof -ti:3000)
    if [ ! -z "$FRONTEND_PID" ]; then
        kill -9 $FRONTEND_PID 2>/dev/null
        echo -e "${GREEN}✓ Frontend stopped (port 3000)${NC}"
    else
        echo -e "${YELLOW}⚠ No frontend process on port 3000${NC}"
    fi
fi

echo ""
echo -e "${GREEN}All services stopped${NC}"
