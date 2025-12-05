#!/bin/bash
# =============================================================================
# Local Network Hosting Script for Chandojñānam
# =============================================================================
# This script starts both backend and frontend servers accessible on your
# local network, so other devices (phones, tablets, other computers) can
# access the application.
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the script's directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default ports
BACKEND_PORT="${BACKEND_PORT:-5000}"
FRONTEND_PORT="${FRONTEND_PORT:-8080}"

# Function to print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to get the local IP address
get_local_ip() {
    # Try different methods to get local IP
    local ip=""
    
    # Method 1: hostname -I (Linux)
    if command -v hostname &> /dev/null; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi
    
    # Method 2: ip route (Linux)
    if [ -z "$ip" ] && command -v ip &> /dev/null; then
        ip=$(ip route get 1 2>/dev/null | awk '{print $7; exit}')
    fi
    
    # Method 3: ifconfig (macOS/Linux fallback)
    if [ -z "$ip" ] && command -v ifconfig &> /dev/null; then
        ip=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1)
    fi
    
    # Fallback
    if [ -z "$ip" ]; then
        ip="localhost"
    fi
    
    echo "$ip"
}

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t &> /dev/null; then
        return 1  # Port is in use
    fi
    return 0  # Port is available
}

# Function to kill process on a port
kill_port() {
    local port=$1
    local pids=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null)
    if [ -n "$pids" ]; then
        print_warning "Killing existing process on port $port (PID: $pids)"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

# Function to cleanup on exit
cleanup() {
    print_info "Shutting down servers..."
    
    # Kill backend
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    # Kill frontend
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes on our ports
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT
    
    print_success "Servers stopped. Goodbye!"
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

# =============================================================================
# Main Script
# =============================================================================

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         ${GREEN}Chandojñānam - Local Network Server${CYAN}                  ║${NC}"
echo -e "${CYAN}║         ${YELLOW}Sanskrit Meter Identification System${CYAN}                ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get local IP
LOCAL_IP=$(get_local_ip)
print_info "Detected local IP: ${GREEN}$LOCAL_IP${NC}"

# Check and free ports if needed
print_info "Checking ports..."

if ! check_port $BACKEND_PORT; then
    print_warning "Port $BACKEND_PORT is in use"
    read -p "Kill existing process? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill_port $BACKEND_PORT
    else
        print_error "Cannot start backend. Port $BACKEND_PORT is in use."
        exit 1
    fi
fi

if ! check_port $FRONTEND_PORT; then
    print_warning "Port $FRONTEND_PORT is in use"
    read -p "Kill existing process? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill_port $FRONTEND_PORT
    else
        print_error "Cannot start frontend. Port $FRONTEND_PORT is in use."
        exit 1
    fi
fi

# =============================================================================
# Start Backend
# =============================================================================
print_info "Starting backend server..."

cd "$PROJECT_ROOT/backend"

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start backend in background
PYTHONPATH=. python run.py --host 0.0.0.0 --port $BACKEND_PORT > /tmp/chandas_backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
print_info "Waiting for backend to start..."
for i in {1..10}; do
    if curl -s "http://localhost:$BACKEND_PORT/api/info" > /dev/null 2>&1; then
        print_success "Backend started successfully!"
        break
    fi
    if [ $i -eq 10 ]; then
        print_error "Backend failed to start. Check /tmp/chandas_backend.log"
        cat /tmp/chandas_backend.log
        exit 1
    fi
    sleep 1
done

# =============================================================================
# Start Frontend
# =============================================================================
print_info "Starting frontend server..."

cd "$PROJECT_ROOT/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_warning "node_modules not found. Running npm install..."
    npm install
fi

# Start frontend with the correct API URL
export VITE_API_URL="http://${LOCAL_IP}:${BACKEND_PORT}/api"
npm run dev -- --host 0.0.0.0 --port $FRONTEND_PORT > /tmp/chandas_frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
print_info "Waiting for frontend to start..."
for i in {1..15}; do
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
        print_success "Frontend started successfully!"
        break
    fi
    if [ $i -eq 15 ]; then
        print_error "Frontend failed to start. Check /tmp/chandas_frontend.log"
        cat /tmp/chandas_frontend.log
        exit 1
    fi
    sleep 1
done

# =============================================================================
# Print Access Information
# =============================================================================
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ Servers are running!${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${YELLOW}📱 Access from any device on your network:${NC}"
echo ""
echo -e "     Frontend:  ${GREEN}http://${LOCAL_IP}:${FRONTEND_PORT}${NC}"
echo -e "     Backend:   ${GREEN}http://${LOCAL_IP}:${BACKEND_PORT}/api${NC}"
echo ""
echo -e "  ${YELLOW}💻 Local access:${NC}"
echo ""
echo -e "     Frontend:  ${BLUE}http://localhost:${FRONTEND_PORT}${NC}"
echo -e "     Backend:   ${BLUE}http://localhost:${BACKEND_PORT}/api${NC}"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${YELLOW}📋 QR Code for easy mobile access:${NC}"

# Generate simple ASCII QR indicator (actual QR would need qrencode)
if command -v qrencode &> /dev/null; then
    echo ""
    qrencode -t ANSIUTF8 "http://${LOCAL_IP}:${FRONTEND_PORT}" 2>/dev/null || true
else
    echo ""
    echo -e "     ${BLUE}http://${LOCAL_IP}:${FRONTEND_PORT}${NC}"
    echo ""
    echo -e "  ${CYAN}(Install 'qrencode' to show QR code: sudo apt install qrencode)${NC}"
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "  ${RED}Press Ctrl+C to stop all servers${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Keep script running and show logs
print_info "Showing live logs (Backend: blue, Frontend: green)..."
echo ""

# Tail both logs with color coding
tail -f /tmp/chandas_backend.log 2>/dev/null | sed "s/^/$(printf "${BLUE}[Backend]${NC} ")/" &
TAIL_BACKEND=$!

tail -f /tmp/chandas_frontend.log 2>/dev/null | sed "s/^/$(printf "${GREEN}[Frontend]${NC} ")/" &
TAIL_FRONTEND=$!

# Wait for user interrupt
wait
