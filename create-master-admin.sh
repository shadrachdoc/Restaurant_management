#!/bin/bash

# Script to create Master Admin user

echo "🔐 Creating Master Admin User..."
echo ""

# Create master admin via auth service
RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@restaurant.com",
    "password": "Admin@123456",
    "role": "master_admin",
    "full_name": "System Administrator"
  }')

# Check if successful
if echo "$RESPONSE" | grep -q '"id"'; then
    echo "✅ Master Admin created successfully!"
    echo ""
    echo "Login credentials:"
    echo "  Username: admin"
    echo "  Password: Admin@123456"
    echo ""
    echo "Access the application at: http://localhost:5173/login"
    echo "After login, you'll be redirected to: http://localhost:5173/master-admin"
else
    echo "❌ Failed to create Master Admin"
    echo ""
    echo "Response:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    echo ""

    # Check if user already exists
    if echo "$RESPONSE" | grep -q "already registered"; then
        echo "ℹ️  Master Admin already exists!"
        echo ""
        echo "Login credentials:"
        echo "  Username: admin"
        echo "  Password: Admin@123456"
        echo ""
        echo "If you've forgotten the password, you'll need to reset it in the database."
    fi
fi
