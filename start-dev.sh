#!/bin/bash
# Meru Coders - Development Startup Script
# Starts both backend and frontend for local development

echo "========================================"
echo "  Meru Coders - Development Server"
echo "========================================"
echo ""

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Get local IP address early
get_local_ip() {
    local ip=""
    if command -v hostname &> /dev/null; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi
    if [ -z "$ip" ] && command -v ip &> /dev/null; then
        ip=$(ip route get 1 2>/dev/null | awk '{print $7; exit}')
    fi
    if [ -z "$ip" ]; then
        ip="localhost"
    fi
    echo "$ip"
}

LOCAL_IP=$(get_local_ip)
echo "Detected Local IP: $LOCAL_IP"
echo ""

# Check if directories exist
if [ ! -d "$BACKEND_DIR" ]; then
    echo "ERROR: Backend directory not found at $BACKEND_DIR"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "ERROR: Frontend directory not found at $FRONTEND_DIR"
    exit 1
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Backend
echo "[1/2] Starting Backend API server..."
cd "$BACKEND_DIR"

# Activate virtual environment and start backend
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "WARNING: No virtual environment found. Using system Python."
fi

export PYTHONPATH="$SCRIPT_DIR"
python run.py &
BACKEND_PID=$!

# Wait for backend to start
echo "      Waiting for backend to initialize..."
sleep 4

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "ERROR: Backend failed to start"
    exit 1
fi

# Start Frontend
echo "[2/2] Starting Frontend dev server..."
cd "$FRONTEND_DIR"

# Set VITE_API_URL so frontend knows where the backend is
export VITE_API_URL="http://${LOCAL_IP}:5000/api"
npm run dev -- --host &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

echo ""
echo "========================================"
echo "  Servers Started Successfully!"
echo "========================================"
echo ""
echo "  Local Access:"
echo "    Frontend:  http://localhost:8080"
echo "    Backend:   http://localhost:5000/api"
echo ""
echo "  Network Access (for other devices):"
echo "    Frontend:  http://$LOCAL_IP:8080"
echo "    Backend:   http://$LOCAL_IP:5000/api"
echo ""
echo "  Press Ctrl+C to stop both servers..."
echo ""

# Wait for either process to exit
wait $BACKEND_PID $FRONTEND_PID
