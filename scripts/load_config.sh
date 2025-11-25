#!/bin/bash
#
# Load GCP Configuration
# This script loads configuration from gcp_config.py
#

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load configuration from gcp_config.py
export PROJECT_ID=$(python3 -c "import sys; sys.path.insert(0, '$PROJECT_ROOT'); from gcp_config import PROJECT_ID; print(PROJECT_ID)")
export REGION=$(python3 -c "import sys; sys.path.insert(0, '$PROJECT_ROOT'); from gcp_config import REGION; print(REGION)")
export BACKEND_SERVICE_NAME=$(python3 -c "import sys; sys.path.insert(0, '$PROJECT_ROOT'); from gcp_config import BACKEND_SERVICE_NAME; print(BACKEND_SERVICE_NAME)")
export FRONTEND_SERVICE_NAME=$(python3 -c "import sys; sys.path.insert(0, '$PROJECT_ROOT'); from gcp_config import FRONTEND_SERVICE_NAME; print(FRONTEND_SERVICE_NAME)")

# Backend image
export BACKEND_IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/meru-coders/backend"
export FRONTEND_IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/meru-coders/frontend"

# Verify configuration loaded
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: Failed to load GCP configuration"
    exit 1
fi
