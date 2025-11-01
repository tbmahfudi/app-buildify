#!/bin/bash

# Frontend Development Server Startup Script
# This script ensures the frontend server starts from the correct directory

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Frontend Development Server  ${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${YELLOW}Error: Frontend directory not found at: $FRONTEND_DIR${NC}"
    exit 1
fi

# Check if index.html exists
if [ ! -f "$FRONTEND_DIR/index.html" ]; then
    echo -e "${YELLOW}Error: index.html not found in frontend directory${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Frontend directory found${NC}"
echo -e "${GREEN}✓ Starting server from: $FRONTEND_DIR${NC}"
echo ""
echo -e "${YELLOW}Server will be available at: http://localhost:8080${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Change to frontend directory and start server
cd "$FRONTEND_DIR"
python3 -m http.server 8080
