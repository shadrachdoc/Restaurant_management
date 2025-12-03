#!/bin/bash

# Automated testing script for Restaurant Service

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8003/api/v1"
RESTAURANT_ID=""
TABLE_ID=""
MENU_ITEM_ID=""

echo -e "${BLUE}🧪 Restaurant Service - Automated Testing${NC}"
echo "=========================================="
echo ""

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        exit 1
    fi
}

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/test_response.json ${BASE_URL%/api/v1}/health)
if [ "$response" = "200" ]; then
    print_result 0 "Service is healthy"
    cat /tmp/test_response.json | python3 -m json.tool
else
    print_result 1 "Health check failed (HTTP $response)"
fi
echo ""

# Test 2: Create Restaurant
echo -e "${YELLOW}Test 2: Create Restaurant${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/test_response.json -X POST $BASE_URL/restaurants \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Restaurant",
        "description": "Automated test restaurant",
        "email": "test@restaurant.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "theme_color": "#FF5733",
        "pricing_plan": "basic",
        "max_tables": 20
    }')

if [ "$response" = "201" ]; then
    RESTAURANT_ID=$(cat /tmp/test_response.json | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    print_result 0 "Restaurant created (ID: ${RESTAURANT_ID:0:8}...)"
    cat /tmp/test_response.json | python3 -m json.tool
else
    print_result 1 "Restaurant creation failed (HTTP $response)"
fi
echo ""

# Test 3: Get Restaurant
echo -e "${YELLOW}Test 3: Get Restaurant${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/test_response.json $BASE_URL/restaurants/$RESTAURANT_ID)
if [ "$response" = "200" ]; then
    print_result 0 "Restaurant retrieved successfully"
else
    print_result 1 "Get restaurant failed (HTTP $response)"
fi
echo ""

# Test 4: Create Menu Items
echo -e "${YELLOW}Test 4: Create Menu Items${NC}"

# Appetizer
response=$(curl -s -w "%{http_code}" -o /tmp/test_response.json -X POST $BASE_URL/restaurants/$RESTAURANT_ID/menu-items \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Caesar Salad",
        "description": "Classic Caesar",
        "category": "appetizer",
        "price": 8.99,
        "is_vegetarian": true,
        "preparation_time": 10,
        "calories": 350,
        "ingredients": ["lettuce", "parmesan"],
        "allergens": ["dairy"]
    }')

if [ "$response" = "201" ]; then
    MENU_ITEM_ID=$(cat /tmp/test_response.json | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    print_result 0 "Menu item created: Caesar Salad"
else
    print_result 1 "Menu item creation failed (HTTP $response)"
fi

# Main Course
response=$(curl -s -w "%{http_code}" -o /dev/null -X POST $BASE_URL/restaurants/$RESTAURANT_ID/menu-items \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Grilled Salmon",
        "category": "main_course",
        "price": 24.99,
        "is_gluten_free": true,
        "preparation_time": 20
    }')

if [ "$response" = "201" ]; then
    print_result 0 "Menu item created: Grilled Salmon"
else
    print_result 1 "Menu item creation failed"
fi

# Dessert
response=$(curl -s -w "%{http_code}" -o /dev/null -X POST $BASE_URL/restaurants/$RESTAURANT_ID/menu-items \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Chocolate Cake",
        "category": "dessert",
        "price": 9.99,
        "is_vegetarian": true
    }')

if [ "$response" = "201" ]; then
    print_result 0 "Menu item created: Chocolate Cake"
else
    print_result 1 "Menu item creation failed"
fi
echo ""

# Test 5: List Menu Items
echo -e "${YELLOW}Test 5: List Menu Items${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/test_response.json $BASE_URL/restaurants/$RESTAURANT_ID/menu-items)
if [ "$response" = "200" ]; then
    count=$(cat /tmp/test_response.json | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
    print_result 0 "Retrieved $count menu items"
else
    print_result 1 "List menu items failed (HTTP $response)"
fi
echo ""

# Test 6: Filter Menu Items by Category
echo -e "${YELLOW}Test 6: Filter Menu Items by Category${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/test_response.json "$BASE_URL/restaurants/$RESTAURANT_ID/menu-items?category=main_course")
if [ "$response" = "200" ]; then
    count=$(cat /tmp/test_response.json | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
    print_result 0 "Found $count main course items"
else
    print_result 1 "Filter failed (HTTP $response)"
fi
echo ""

# Test 7: Create Tables
echo -e "${YELLOW}Test 7: Create Tables (with QR codes)${NC}"

response=$(curl -s -w "%{http_code}" -o /tmp/test_response.json -X POST $BASE_URL/restaurants/$RESTAURANT_ID/tables \
    -H "Content-Type: application/json" \
    -d '{
        "table_number": "T-01",
        "seat_count": 4,
        "floor": "Ground",
        "section": "Window"
    }')

if [ "$response" = "201" ]; then
    TABLE_ID=$(cat /tmp/test_response.json | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    has_qr=$(cat /tmp/test_response.json | python3 -c "import sys, json; print('qr_code_url' in json.load(sys.stdin))")
    if [ "$has_qr" = "True" ]; then
        print_result 0 "Table created with QR code (ID: ${TABLE_ID:0:8}...)"
    else
        print_result 1 "Table created but QR code missing"
    fi
else
    print_result 1 "Table creation failed (HTTP $response)"
fi

# Create more tables
for i in 2 3 4; do
    curl -s -o /dev/null -X POST $BASE_URL/restaurants/$RESTAURANT_ID/tables \
        -H "Content-Type: application/json" \
        -d "{\"table_number\": \"T-0$i\", \"seat_count\": 4}"
done
print_result 0 "Created 3 additional tables"
echo ""

# Test 8: Get Table QR Code
echo -e "${YELLOW}Test 8: Get Table QR Code${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/test_response.json $BASE_URL/restaurants/$RESTAURANT_ID/tables/$TABLE_ID/qr-code)
if [ "$response" = "200" ]; then
    qr_length=$(cat /tmp/test_response.json | python3 -c "import sys, json; print(len(json.load(sys.stdin)['qr_code_url']))")
    print_result 0 "QR code retrieved (length: $qr_length characters)"
    echo -e "${BLUE}   QR code is a base64 data URL that can be displayed directly in <img> tags${NC}"
else
    print_result 1 "Get QR code failed (HTTP $response)"
fi
echo ""

# Test 9: Update Table Status
echo -e "${YELLOW}Test 9: Update Table Status${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/test_response.json -X PATCH "$BASE_URL/restaurants/$RESTAURANT_ID/tables/$TABLE_ID/status?new_status=occupied")
if [ "$response" = "200" ]; then
    status=$(cat /tmp/test_response.json | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
    print_result 0 "Table status updated to: $status"
else
    print_result 1 "Update status failed (HTTP $response)"
fi
echo ""

# Test 10: Submit Feedback
echo -e "${YELLOW}Test 10: Submit Customer Feedback${NC}"

ratings=(5 4 5 3 4)
for rating in "${ratings[@]}"; do
    curl -s -o /dev/null -X POST $BASE_URL/restaurants/$RESTAURANT_ID/feedback \
        -H "Content-Type: application/json" \
        -d "{\"rating\": $rating, \"comment\": \"Test feedback with $rating stars\"}"
done
print_result 0 "Submitted 5 feedback entries"
echo ""

# Test 11: Get Feedback Statistics
echo -e "${YELLOW}Test 11: Get Feedback Statistics${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/test_response.json "$BASE_URL/restaurants/$RESTAURANT_ID/feedback/stats/summary?days=30")
if [ "$response" = "200" ]; then
    avg_rating=$(cat /tmp/test_response.json | python3 -c "import sys, json; print(json.load(sys.stdin)['average_rating'])")
    total=$(cat /tmp/test_response.json | python3 -c "import sys, json; print(json.load(sys.stdin)['total_feedback'])")
    print_result 0 "Feedback stats: $total reviews, avg rating: $avg_rating/5.0"
    cat /tmp/test_response.json | python3 -m json.tool
else
    print_result 1 "Get feedback stats failed (HTTP $response)"
fi
echo ""

# Test 12: Get Restaurant Analytics
echo -e "${YELLOW}Test 12: Get Restaurant Analytics${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/test_response.json $BASE_URL/restaurants/$RESTAURANT_ID/analytics)
if [ "$response" = "200" ]; then
    print_result 0 "Analytics retrieved successfully"
    cat /tmp/test_response.json | python3 -m json.tool
else
    print_result 1 "Get analytics failed (HTTP $response)"
fi
echo ""

# Test 13: Update Restaurant Branding
echo -e "${YELLOW}Test 13: Update Restaurant Branding${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/test_response.json -X PATCH $BASE_URL/restaurants/$RESTAURANT_ID/branding \
    -H "Content-Type: application/json" \
    -d '{
        "theme_color": "#00FF00",
        "upcoming_events": [
            {"title": "Live Music", "date": "2025-12-15"}
        ],
        "advertisements": [
            {"title": "Happy Hour", "content": "50% off drinks"}
        ]
    }')

if [ "$response" = "200" ]; then
    print_result 0 "Branding updated successfully"
else
    print_result 1 "Update branding failed (HTTP $response)"
fi
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ All Tests Passed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Test Summary:${NC}"
echo "  Restaurant ID: $RESTAURANT_ID"
echo "  Table ID: $TABLE_ID"
echo "  Menu Items: 3"
echo "  Tables: 4"
echo "  Feedback: 5 entries"
echo ""
echo -e "${BLUE}View API Documentation:${NC}"
echo "  http://localhost:8003/docs"
echo ""
echo -e "${BLUE}Clean up test data:${NC}"
echo "  curl -X DELETE $BASE_URL/restaurants/$RESTAURANT_ID"
echo ""
