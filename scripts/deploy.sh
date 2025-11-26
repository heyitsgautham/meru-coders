#!/bin/bash
#
# Deploy to Google Cloud Run
# Usage: ./scripts/deploy.sh [backend|frontend|both]
#

set -e

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load configuration
source "$SCRIPT_DIR/load_config.sh"

echo "================================"
echo "🚀 Deploying to Cloud Run"
echo "================================"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check prerequisites
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not installed"
    exit 1
fi

if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not logged in. Run: gcloud auth login"
    exit 1
fi

# Set project and enable APIs
echo "📋 Setting up GCP..."
gcloud config set project $PROJECT_ID --quiet
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --quiet

# Setup Artifact Registry
setup_artifact_registry() {
    echo ""
    echo "📦 Setting up Artifact Registry..."
    
    if ! gcloud artifacts repositories describe meru-coders --location=$REGION &>/dev/null; then
        gcloud artifacts repositories create meru-coders \
            --repository-format=docker \
            --location=$REGION \
            --description="Meru Coders" \
            --quiet
        echo "✅ Repository created"
    fi
    
    gcloud auth configure-docker $REGION-docker.pkg.dev --quiet
}

# Function to build and push backend
deploy_backend() {
    echo ""
    echo "================================"
    echo "🔨 Building Backend"
    echo "================================"
    
    cd "$PROJECT_ROOT"
    
    echo "📦 Building Docker image..."
    gcloud builds submit \
        --config backend/cloudbuild.yaml \
        --substitutions=_IMAGE_NAME=$BACKEND_IMAGE:latest \
        .
    
    echo ""
    echo "🚀 Deploying to Cloud Run..."
    gcloud run deploy $BACKEND_SERVICE_NAME \
        --image $BACKEND_IMAGE:latest \
        --region $REGION \
        --platform managed \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --max-instances 10 \
        --min-instances 0 \
        --timeout 300 \
        --concurrency 80 \
        --set-env-vars="DEBUG=False,LOG_LEVEL=INFO,CORS_ORIGINS=*" \
        --quiet
    
    BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE_NAME \
        --region=$REGION \
        --format='value(status.url)')
    
    echo ""
    echo "✅ Backend deployed!"
    echo "URL: $BACKEND_URL"
}

# Function to build and push frontend
deploy_frontend() {
    echo ""
    echo "================================"
    echo "🔨 Building Frontend"
    echo "================================"
    
    cd "$PROJECT_ROOT"
    
    # Get backend URL for frontend configuration
    BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE_NAME \
        --region=$REGION \
        --format='value(status.url)' 2>/dev/null || echo "")
    
    if [ -z "$BACKEND_URL" ]; then
        echo "⚠️  Warning: Backend not found. Frontend will use default config."
    else
        echo "📝 Creating runtime config with backend URL: $BACKEND_URL"

        # Create frontend/config.js which will be copied into the built image.
        cat > "$PROJECT_ROOT/frontend/config.js" <<EOF
window.CONFIG = { API_URL: '${BACKEND_URL}/api' };
EOF
    fi
    
    echo "📦 Building Docker image..."
    gcloud builds submit \
        --config frontend/cloudbuild.yaml \
        --substitutions=_IMAGE_NAME=$FRONTEND_IMAGE:latest \
        .
    
    echo ""
    echo "🚀 Deploying to Cloud Run..."
    gcloud run deploy $FRONTEND_SERVICE_NAME \
        --image $FRONTEND_IMAGE:latest \
        --region $REGION \
        --platform managed \
        --allow-unauthenticated \
        --memory 512Mi \
        --cpu 1 \
        --max-instances 5 \
        --min-instances 0 \
        --timeout 60 \
        --concurrency 80 \
        --port 8080 \
        --quiet
    
    FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE_NAME \
        --region=$REGION \
        --format='value(status.url)')
    
    echo ""
    echo "✅ Frontend deployed!"
    echo "URL: $FRONTEND_URL"
}

# Main deployment
DEPLOY_TARGET="${1:-both}"

case $DEPLOY_TARGET in
    backend)
        setup_artifact_registry
        deploy_backend
        ;;
    frontend)
        setup_artifact_registry
        deploy_frontend
        ;;
    both)
        setup_artifact_registry
        deploy_backend
        deploy_frontend
        ;;
    *)
        echo "❌ Usage: $0 [backend|frontend|both]"
        exit 1
        ;;
esac

echo ""
echo "================================"
echo "✅ Deployment Complete!"
echo "================================"

if gcloud run services describe $BACKEND_SERVICE_NAME --region=$REGION &>/dev/null; then
    BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE_NAME --region=$REGION --format='value(status.url)')
    echo "Backend:  $BACKEND_URL"
fi

if gcloud run services describe $FRONTEND_SERVICE_NAME --region=$REGION &>/dev/null; then
    FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE_NAME --region=$REGION --format='value(status.url)')
    echo "Frontend: $FRONTEND_URL"
fi
echo ""

# Cleanup: Remove generated config.js so local dev uses localhost:5000
if [ -f "$PROJECT_ROOT/frontend/config.js" ]; then
    rm -f "$PROJECT_ROOT/frontend/config.js"
    echo "🧹 Cleaned up frontend/config.js (local dev will use localhost:5000)"
fi