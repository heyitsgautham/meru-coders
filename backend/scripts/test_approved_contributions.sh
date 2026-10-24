#!/bin/bash
# Test script for approved contributions functionality

echo "============================================"
echo "Testing Approved Contributions Setup"
echo "============================================"
echo ""

# Step 1: Create the table in Supabase
echo "📝 Step 1: Create approved_contributions table"
echo "   Please run the SQL in backend/scripts/create_approved_contributions_table.sql"
echo "   in Supabase SQL Editor:"
echo "   https://app.supabase.com/project/_/sql/new"
echo ""
read -p "   Press Enter after running the SQL..."
echo ""

# Step 2: Verify table exists
echo "📊 Step 2: Verify table creation"
cd /home/kinux/projects/meru-coders/backend
python scripts/supabase_manager.py list
echo ""

# Step 3: Test API endpoint
echo "🧪 Step 3: Test API endpoint"
echo "   Starting Flask server..."
echo ""

# Check if server is running
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✓ Server is already running"
else
    echo "⚠️  Server not running. Please start it with:"
    echo "   cd backend && python run.py"
    exit 1
fi

echo ""
echo "   Testing GET /api/contributions/approved..."
response=$(curl -s http://localhost:5000/api/contributions/approved?limit=10)
echo "$response" | python -m json.tool
echo ""

# Step 4: Instructions for frontend
echo "✅ Step 4: Frontend integration"
echo ""
echo "   The following has been added:"
echo "   • API service: getApprovedContributions()"
echo "   • Backend endpoint: GET /api/contributions/approved"
echo "   • SQL table: approved_contributions"
echo ""
echo "   To display in Datasets page, you can either:"
echo "   A) Add a new dataset card in DatasetsView.tsx"
echo "   B) Create a separate 'User Contributions' tab"
echo ""

echo "============================================"
echo "Setup Complete! 🎉"
echo "============================================"
