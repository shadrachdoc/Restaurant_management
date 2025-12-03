# Testing Restaurant Service - Step by Step Guide

This guide will walk you through testing all features of the Restaurant Service.

## Prerequisites

Before testing, ensure you have:
- ✅ Python 3.11+ installed
- ✅ PostgreSQL running (or use Docker Compose)
- ✅ Redis running (or use Docker Compose)

## Quick Start - 3 Options

### Option 1: Start Just Infrastructure (Recommended for Testing)

```bash
# Start only PostgreSQL and Redis
./scripts/start-infrastructure.sh

# Wait for services to be ready (about 10 seconds)
```

### Option 2: Start Everything with Docker Compose

```bash
# Start all services
./scripts/start-all-services.sh

# Restaurant service will be at: http://localhost:8003
```

### Option 3: Run Service Manually (Best for Development)

```bash
# 1. Start infrastructure
./scripts/start-infrastructure.sh

# 2. Activate Python environment
source venv/bin/activate

# 3. Start Restaurant Service
cd services/restaurant-service
uvicorn app.main:app --reload --port 8003
```

## Testing Steps

### Step 1: Verify Service is Running

Open your browser or use curl:

```bash
# Health check
curl http://localhost:8003/health

# Expected response:
# {"status":"healthy","service":"restaurant-service"}
```

### Step 2: Access API Documentation

Open in browser:
- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc

You should see all API endpoints organized by tags:
- Restaurants
- Menu Items
- Tables
- Feedback

### Step 3: Test Restaurant Creation

```bash
# Create a restaurant
curl -X POST http://localhost:8003/api/v1/restaurants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "The Golden Fork",
    "description": "Fine dining experience with international cuisine",
    "email": "contact@goldenfork.com",
    "phone": "+1-555-0123",
    "address": "123 Culinary Street, Food City, FC 12345",
    "website": "https://goldenfork.com",
    "theme_color": "#FFD700",
    "pricing_plan": "premium",
    "max_tables": 30
  }'
```

**Expected Response**:
```json
{
  "id": "some-uuid",
  "name": "The Golden Fork",
  "subscription_status": "trial",
  "pricing_plan": "premium",
  "is_active": true,
  "created_at": "2025-12-03T...",
  ...
}
```

**Save the `id` value - you'll need it for next steps!**

### Step 4: List Restaurants

```bash
# Get all restaurants
curl http://localhost:8003/api/v1/restaurants

# Get only active restaurants
curl http://localhost:8003/api/v1/restaurants?is_active=true
```

### Step 5: Create Menu Items

Replace `{restaurant_id}` with your restaurant's ID:

```bash
# Create an appetizer
curl -X POST http://localhost:8003/api/v1/restaurants/{restaurant_id}/menu-items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Caesar Salad",
    "description": "Classic Caesar with romaine lettuce and parmesan",
    "category": "appetizer",
    "price": 8.99,
    "is_vegetarian": true,
    "is_vegan": false,
    "is_gluten_free": false,
    "preparation_time": 10,
    "calories": 350,
    "ingredients": ["romaine lettuce", "parmesan", "croutons", "caesar dressing"],
    "allergens": ["dairy", "gluten"],
    "display_order": 1
  }'

# Create a main course
curl -X POST http://localhost:8003/api/v1/restaurants/{restaurant_id}/menu-items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Grilled Salmon",
    "description": "Fresh Atlantic salmon with herbs",
    "category": "main_course",
    "price": 24.99,
    "is_vegetarian": false,
    "is_vegan": false,
    "is_gluten_free": true,
    "preparation_time": 20,
    "calories": 450,
    "ingredients": ["salmon", "lemon", "herbs", "olive oil"],
    "allergens": ["fish"],
    "display_order": 1
  }'

# Create a dessert
curl -X POST http://localhost:8003/api/v1/restaurants/{restaurant_id}/menu-items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Chocolate Lava Cake",
    "description": "Warm chocolate cake with molten center",
    "category": "dessert",
    "price": 9.99,
    "is_vegetarian": true,
    "is_vegan": false,
    "is_gluten_free": false,
    "preparation_time": 15,
    "calories": 520,
    "ingredients": ["chocolate", "butter", "eggs", "sugar", "flour"],
    "allergens": ["dairy", "eggs", "gluten"],
    "display_order": 1
  }'

# Create a beverage
curl -X POST http://localhost:8003/api/v1/restaurants/{restaurant_id}/menu-items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fresh Orange Juice",
    "description": "Freshly squeezed orange juice",
    "category": "beverage",
    "price": 4.99,
    "is_vegetarian": true,
    "is_vegan": true,
    "is_gluten_free": true,
    "preparation_time": 5,
    "calories": 110,
    "ingredients": ["oranges"],
    "allergens": [],
    "display_order": 1
  }'
```

### Step 6: List Menu Items

```bash
# Get all menu items
curl http://localhost:8003/api/v1/restaurants/{restaurant_id}/menu-items

# Get only main courses
curl "http://localhost:8003/api/v1/restaurants/{restaurant_id}/menu-items?category=main_course"

# Get only vegetarian items
curl "http://localhost:8003/api/v1/restaurants/{restaurant_id}/menu-items?is_vegetarian=true"

# Get gluten-free items
curl "http://localhost:8003/api/v1/restaurants/{restaurant_id}/menu-items?is_gluten_free=true"
```

### Step 7: Create Tables (with QR Codes!)

```bash
# Create Table 1
curl -X POST http://localhost:8003/api/v1/restaurants/{restaurant_id}/tables \
  -H "Content-Type: application/json" \
  -d '{
    "table_number": "T-01",
    "seat_count": 4,
    "floor": "Ground Floor",
    "section": "Window Side"
  }'

# Create Table 2
curl -X POST http://localhost:8003/api/v1/restaurants/{restaurant_id}/tables \
  -H "Content-Type: application/json" \
  -d '{
    "table_number": "T-02",
    "seat_count": 2,
    "floor": "Ground Floor",
    "section": "Center"
  }'

# Create Table 3
curl -X POST http://localhost:8003/api/v1/restaurants/{restaurant_id}/tables \
  -H "Content-Type: application/json" \
  -d '{
    "table_number": "T-03",
    "seat_count": 6,
    "floor": "First Floor",
    "section": "VIP"
  }'
```

**Note**: Each table will have a QR code automatically generated!

### Step 8: Get Table QR Code

```bash
# Get QR code for a specific table
curl http://localhost:8003/api/v1/restaurants/{restaurant_id}/tables/{table_id}/qr-code
```

You'll receive:
```json
{
  "table_id": "uuid",
  "table_number": "T-01",
  "qr_code_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "qr_code_data": "unique-token"
}
```

**The `qr_code_url` can be directly used in an `<img>` tag!**

### Step 9: Update Table Status

```bash
# Mark table as occupied
curl -X PATCH "http://localhost:8003/api/v1/restaurants/{restaurant_id}/tables/{table_id}/status?new_status=occupied"

# Mark as available
curl -X PATCH "http://localhost:8003/api/v1/restaurants/{restaurant_id}/tables/{table_id}/status?new_status=available"

# Mark as reserved
curl -X PATCH "http://localhost:8003/api/v1/restaurants/{restaurant_id}/tables/{table_id}/status?new_status=reserved"

# Mark as cleaning
curl -X PATCH "http://localhost:8003/api/v1/restaurants/{restaurant_id}/tables/{table_id}/status?new_status=cleaning"
```

### Step 10: Submit Customer Feedback

```bash
# Submit 5-star feedback
curl -X POST http://localhost:8003/api/v1/restaurants/{restaurant_id}/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 5,
    "comment": "Absolutely amazing! The food was delicious and service was exceptional.",
    "customer_name": "John Doe",
    "customer_email": "john@example.com"
  }'

# Submit 4-star feedback
curl -X POST http://localhost:8003/api/v1/restaurants/{restaurant_id}/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 4,
    "comment": "Great food, good service. Would come again!",
    "customer_name": "Jane Smith"
  }'

# Submit 3-star feedback
curl -X POST http://localhost:8003/api/v1/restaurants/{restaurant_id}/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 3,
    "comment": "Food was okay, but service was slow."
  }'
```

### Step 11: Get Feedback Statistics

```bash
# Get feedback summary for last 30 days
curl http://localhost:8003/api/v1/restaurants/{restaurant_id}/feedback/stats/summary?days=30
```

**Expected Response**:
```json
{
  "total_feedback": 3,
  "average_rating": 4.0,
  "rating_distribution": {
    "1": 0,
    "2": 0,
    "3": 1,
    "4": 1,
    "5": 1
  },
  "period_days": 30,
  "five_star_percentage": 33.3,
  "four_plus_percentage": 66.7
}
```

### Step 12: Get Restaurant Analytics

```bash
# Get complete analytics
curl http://localhost:8003/api/v1/restaurants/{restaurant_id}/analytics
```

**Expected Response**:
```json
{
  "total_menu_items": 4,
  "total_tables": 3,
  "available_tables": 2,
  "occupied_tables": 1,
  "total_feedback": 3,
  "average_rating": 4.0,
  "menu_items_by_category": {
    "appetizer": 1,
    "main_course": 1,
    "dessert": 1,
    "beverage": 1
  }
}
```

### Step 13: Update Restaurant Branding

```bash
# Update branding with events and ads
curl -X PATCH http://localhost:8003/api/v1/restaurants/{restaurant_id}/branding \
  -H "Content-Type: application/json" \
  -d '{
    "theme_color": "#FF5733",
    "upcoming_events": [
      {
        "title": "Live Jazz Night",
        "date": "2025-12-15",
        "time": "7:00 PM - 10:00 PM",
        "description": "Enjoy live jazz music while you dine"
      },
      {
        "title": "Wine Tasting Event",
        "date": "2025-12-20",
        "time": "6:00 PM - 9:00 PM",
        "description": "Sample our finest wines"
      }
    ],
    "advertisements": [
      {
        "title": "Happy Hour Special",
        "content": "50% off all drinks from 5-7 PM!",
        "valid_until": "2025-12-31"
      },
      {
        "title": "Weekend Brunch",
        "content": "New brunch menu every Saturday & Sunday",
        "valid_until": "2025-12-31"
      }
    ]
  }'
```

## Testing with Swagger UI (Easiest Method)

1. Open http://localhost:8003/docs in your browser

2. **Test Restaurant Creation**:
   - Find "POST /restaurants" under "Restaurants"
   - Click "Try it out"
   - Fill in the request body
   - Click "Execute"
   - See the response below

3. **Test Menu Items**:
   - Copy the `restaurant_id` from step 2
   - Find "POST /restaurants/{restaurant_id}/menu-items"
   - Click "Try it out"
   - Paste the restaurant_id
   - Fill in menu item details
   - Click "Execute"

4. **View QR Codes**:
   - Create a table using "POST /restaurants/{restaurant_id}/tables"
   - Copy the `table_id` from response
   - Use "GET /restaurants/{restaurant_id}/tables/{table_id}/qr-code"
   - Copy the `qr_code_url` from response
   - Create an HTML file with: `<img src="PASTE_QR_CODE_URL_HERE">`
   - Open in browser to see the QR code!

## Verification Checklist

- [ ] Service starts without errors
- [ ] Health endpoint returns healthy status
- [ ] Can create a restaurant
- [ ] Can list restaurants
- [ ] Can create menu items in all categories
- [ ] Can filter menu items by category
- [ ] Can filter menu items by dietary restrictions
- [ ] Can create tables
- [ ] QR codes are automatically generated for tables
- [ ] Can view QR code as base64 image
- [ ] Can update table status
- [ ] Can submit customer feedback
- [ ] Can view feedback statistics
- [ ] Can get restaurant analytics
- [ ] Can update restaurant branding
- [ ] All CRUD operations work

## Common Issues & Solutions

### Issue: Connection refused
```bash
# Check if service is running
lsof -i :8003

# Check if PostgreSQL is running
docker-compose ps postgres

# Restart infrastructure
./scripts/start-infrastructure.sh
```

### Issue: Database connection error
```bash
# Check database URL in .env
cat .env | grep DATABASE_URL

# Should be: postgresql://restaurant_admin:restaurant_pass_2024@localhost:5432/restaurant_db

# Test database connection
docker-compose exec postgres psql -U restaurant_admin -d restaurant_db -c "SELECT 1;"
```

### Issue: Import errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: QR code not displaying
The QR code is returned as a base64 data URL. To view it:
1. Copy the entire `qr_code_url` value
2. Create an HTML file with: `<img src="data:image/png;base64,YOUR_BASE64_HERE">`
3. Open in browser

Or use an online base64 image viewer.

## Next Steps

After successful testing:

1. **Test with Postman/Insomnia**: Import the API collection
2. **Test Authentication**: Integrate with Auth Service
3. **Test QR Code Scanning**: Build a simple frontend to scan QR codes
4. **Load Testing**: Use tools like Apache Bench or Locust
5. **Integration Testing**: Test with Order Service (when ready)

## Automated Test Script

See `scripts/test-restaurant-service.sh` for automated testing.

---

**Need Help?**
- Check logs: `docker-compose logs restaurant-service`
- View API docs: http://localhost:8003/docs
- Check database: `docker-compose exec postgres psql -U restaurant_admin -d restaurant_db`
