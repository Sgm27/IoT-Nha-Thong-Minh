#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  🏠 IoT Smart Home Project - Starting...${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Start Backend (Uvicorn)
echo -e "${GREEN}[1/2] Starting Backend Server (Uvicorn)...${NC}"
echo -e "${YELLOW}Running: uvicorn app.main:create_app --reload --host 0.0.0.0 --port 8000${NC}"
echo ""
cd backend
uvicorn app.main:create_app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started with PID: $BACKEND_PID${NC}"
echo ""

# Give backend a moment to start
sleep 2

# Start Frontend (Vite)
echo -e "${GREEN}[2/2] Starting Frontend Dev Server (Vite)...${NC}"
echo -e "${YELLOW}Running: npm run dev${NC}"
echo ""
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started with PID: $FRONTEND_PID${NC}"
echo ""

# Print summary
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✓ All services started successfully!${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${YELLOW}Backend API:${NC}  http://localhost:8000"
echo -e "${YELLOW}Frontend:${NC}     http://localhost:5173"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Handle script termination
trap "echo -e '\n${YELLOW}Stopping services...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo -e '${GREEN}✓ All services stopped${NC}'; exit 0" SIGINT SIGTERM

# Wait for both processes
wait
