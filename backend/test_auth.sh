#!/bin/bash
# Test authentication endpoints

BASE_URL="http://localhost:5000"

echo "========================================="
echo "Testing Authentication Endpoints"
echo "========================================="
echo ""

# Test 1: Signup
echo "1. Testing Signup (POST /api/auth/signup)"
echo "Request: {username: 'testuser123', password: 'testpass123'}"
echo ""
SIGNUP_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/signup" \
  -H 'Content-Type: application/json' \
  -d '{"username":"testuser123","password":"testpass123"}')

echo "Response:"
echo "$SIGNUP_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SIGNUP_RESPONSE"
echo ""
echo "========================================="
echo ""

# Extract token from signup response
SIGNUP_TOKEN=$(echo "$SIGNUP_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['session']['access_token'])" 2>/dev/null)

if [ -n "$SIGNUP_TOKEN" ]; then
    echo "✅ Signup successful! Token received."
    echo "Token (first 50 chars): ${SIGNUP_TOKEN:0:50}..."
else
    echo "❌ Signup failed or no token received."
    echo ""
    echo "Possible issues:"
    echo "  - Backend server not running (run: cd backend && python run.py)"
    echo "  - Database missing password_hash column"
    echo "  - Username already taken (try a different one)"
    echo ""
    echo "Next step: Run the SQL from SETUP_AUTH.md in your Supabase dashboard"
    exit 1
fi

echo ""
echo "========================================="
echo ""

# Test 2: Login
echo "2. Testing Login (POST /api/auth/login)"
echo "Request: {username: 'testuser123', password: 'testpass123'}"
echo ""
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"testuser123","password":"testpass123"}')

echo "Response:"
echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"
echo ""

LOGIN_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['session']['access_token'])" 2>/dev/null)

if [ -n "$LOGIN_TOKEN" ]; then
    echo "✅ Login successful! Token received."
else
    echo "❌ Login failed."
fi

echo ""
echo "========================================="
echo ""

# Test 3: Admin Login
echo "3. Testing Admin Login (POST /api/auth/admin-login)"
ADMIN_USERNAME="${ADMIN_USERNAME:-admin-erase-sure}"
: "${ADMIN_PASSWORD:?Set ADMIN_PASSWORD to the backend's admin password}"
echo "Request: {username: '$ADMIN_USERNAME', password: '***'}"
echo ""
ADMIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/admin-login" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$ADMIN_USERNAME\",\"password\":\"$ADMIN_PASSWORD\"}")

echo "Response:"
echo "$ADMIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ADMIN_RESPONSE"
echo ""

ADMIN_TOKEN=$(echo "$ADMIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['session']['access_token'])" 2>/dev/null)

if [ -n "$ADMIN_TOKEN" ]; then
    echo "✅ Admin login successful! Token received."
else
    echo "❌ Admin login failed."
fi

echo ""
echo "========================================="
echo ""
echo "Summary:"
echo "--------"
echo "Signup:       $([ -n \"$SIGNUP_TOKEN\" ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Login:        $([ -n \"$LOGIN_TOKEN\" ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Admin Login:  $([ -n \"$ADMIN_TOKEN\" ] && echo '✅ PASS' || echo '❌ FAIL')"
echo ""
echo "Next steps:"
echo "  - If signup failed: Run SQL from SETUP_AUTH.md"
echo "  - If all tests pass: Test frontend at http://localhost:8081/signup"
echo ""
