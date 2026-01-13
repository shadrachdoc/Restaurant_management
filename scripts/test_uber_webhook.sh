#!/bin/bash
# Test script for Uber Eats webhook integration
# Tests the complete flow: Webhook → Database → RabbitMQ → WebSocket → Frontend

echo "🧪 Testing Uber Eats Webhook Integration"
echo "========================================="
echo ""

# Configuration
WEBHOOK_URL="https://restaurant.corpv3.com/api/v1/webhooks/uber-eats"
RESTAURANT_ID="6956017d-3aea-4ae2-9709-0ca0ac0a1a09"

echo "📡 Sending test Uber Eats order webhook..."
echo "Target: $WEBHOOK_URL"
echo ""

# Send fake Uber webhook
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "orders.notification",
    "order": {
      "id": "uber-test-'$(date +%s)'",
      "eater": {
        "first_name": "Test",
        "last_name": "Customer",
        "phone": "+1234567890",
        "email": "test@example.com"
      },
      "cart": {
        "items": [
          {
            "title": "Biriyani",
            "quantity": 2,
            "special_instructions": "Extra spicy please"
          },
          {
            "title": "Salad",
            "quantity": 1
          },
          {
            "title": "Coke Zero",
            "quantity": 2
          }
        ]
      },
      "delivery": {
        "location": {
          "address_1": "123 Test Street",
          "address_2": "Apt 4B",
          "city": "New York",
          "state": "NY",
          "postal_code": "10001"
        }
      },
      "special_instructions": "Ring doorbell twice, leave at door"
    }
  }')

# Extract response body and status code
HTTP_BODY=$(echo "$RESPONSE" | head -n -1)
HTTP_STATUS=$(echo "$RESPONSE" | tail -n 1)

echo "Response Status: $HTTP_STATUS"
echo "Response Body:"
echo "$HTTP_BODY" | jq '.' 2>/dev/null || echo "$HTTP_BODY"
echo ""

# Check if successful
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "201" ]; then
    echo "✅ Webhook received successfully!"
    echo ""
    echo "Expected results:"
    echo "  1. ✅ Order created in database"
    echo "  2. ✅ Notification published to RabbitMQ"
    echo "  3. ✅ WebSocket broadcast to connected clients"
    echo "  4. ⏳ Chef Display should show:"
    echo "     - Popup notification banner"
    echo "     - Audio alert (3-tone beep)"
    echo "     - Green ring around order card"
    echo "     - 'NEW!' badge"
    echo "     - Countdown timer"
    echo "     - Delivery address"
    echo "  5. ⏳ Admin Dashboard should show:"
    echo "     - Incremented 'New Order' counter"
    echo "     - Order in Online Orders panel"
    echo ""
    echo "🔍 Verify by checking:"
    echo "   - Chef Display: Open kitchen dashboard"
    echo "   - Admin Panel: Check Online Orders widget"
    echo "   - Database: kubectl exec -n restaurant-system statefulset/postgres -- psql -U restaurant_admin -d restaurant_db -c \"SELECT * FROM orders WHERE order_type='UBER' ORDER BY created_at DESC LIMIT 1;\""
    echo ""
else
    echo "❌ Webhook failed with status $HTTP_STATUS"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check integration-service logs:"
    echo "     kubectl logs -n restaurant-system deployment/integration-service --tail=50"
    echo ""
    echo "  2. Check order-service logs:"
    echo "     kubectl logs -n restaurant-system deployment/order-service --tail=50"
    echo ""
    echo "  3. Check RabbitMQ:"
    echo "     kubectl logs -n restaurant-system statefulset/rabbitmq --tail=50"
    echo ""
fi

# Additional verification
echo "📊 Additional Checks:"
echo ""

echo "1️⃣  Checking RabbitMQ consumer status..."
RABBITMQ_STATUS=$(kubectl logs -n restaurant-system deployment/order-service --tail=20 | grep -i "Connected to RabbitMQ" | tail -1)
if [ -n "$RABBITMQ_STATUS" ]; then
    echo "   ✅ RabbitMQ consumer is connected"
else
    echo "   ❌ RabbitMQ consumer not connected"
fi
echo ""

echo "2️⃣  Checking WebSocket server..."
WS_LOGS=$(kubectl logs -n restaurant-system deployment/order-service --tail=20 | grep -i "websocket\|ws" | tail -3)
if [ -n "$WS_LOGS" ]; then
    echo "   ✅ WebSocket server is active"
    echo "$WS_LOGS" | sed 's/^/      /'
else
    echo "   ⚠️  No recent WebSocket activity"
fi
echo ""

echo "3️⃣  Recent Uber orders in database:"
kubectl exec -n restaurant-system statefulset/postgres -- psql -U restaurant_admin -d restaurant_db -c \
  "SELECT order_number, customer_name, status, order_type, total, created_at FROM orders WHERE order_type='UBER' ORDER BY created_at DESC LIMIT 3;" 2>/dev/null
echo ""

echo "========================================="
echo "Test complete! 🎉"
echo ""
echo "Next steps:"
echo "  - Open Chef Display at: https://restaurant.corpv3.com/kitchen"
echo "  - Open Admin Dashboard at: https://restaurant.corpv3.com/admin"
echo "  - Watch for real-time notifications!"
