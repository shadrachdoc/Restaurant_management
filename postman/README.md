# Restaurant Load Testing with Postman

This directory contains Postman collections to simulate realistic restaurant order traffic.

## Files

1. **Restaurant_Load_Test.postman_collection.json** - Main collection with all API requests
2. **Restaurant_Local.postman_environment.json** - Environment variables for local testing

## What This Does

Simulates **250 orders** for "Chai Kadai" restaurant:
- **150 Online Orders** - Registered customers ordering for delivery
- **100 Table Orders** - Walk-in guests ordering at tables

## Prerequisites

1. **Postman Desktop App** installed (https://www.postman.com/downloads/)
2. **Restaurant system running** locally at `http://localhost:8000`
3. **Database accessible** with menu items loaded

## Setup Instructions

### Step 1: Import Collection and Environment

1. Open Postman Desktop App
2. Click **Import** button (top left)
3. Drag and drop both JSON files:
   - `Restaurant_Load_Test.postman_collection.json`
   - `Restaurant_Local.postman_environment.json`
4. Select **"Restaurant Local Environment"** from environment dropdown (top right)

### Step 2: Run Setup

Before running load tests, fetch menu items:

1. In the collection, run **"Setup - Get Menu Items"** request once
2. Check the Postman Console to verify menu items are stored
3. This populates the `menu_items` variable used by all orders

### Step 3: Generate 150 Online Orders

Online orders require user registration and login for each customer.

**Using Collection Runner:**

1. Click on **"Restaurant Load Test - 250 Orders"** collection
2. Click **"Run"** button (or Runner icon)
3. In the Runner, configure:
   - **Iterations:** `150`
   - **Delay:** `100ms` (between requests)
   - **Select Requests:** ✓ Only check these 3:
     - ✓ 1. Register Online Customer
     - ✓ 2. Login Online Customer
     - ✓ 3. Create Online Order
   - **Save responses:** Optional (takes more time)
4. Click **"Run Restaurant Load Test - 250 Orders"**
5. Wait for completion (~5-10 minutes for 150 iterations)

**What happens per iteration:**
1. Creates unique customer account (`customer{timestamp}@test.com`)
2. Logs in and gets JWT token
3. Places online order with 1-5 random menu items
4. Includes delivery address and customer details

### Step 4: Generate 100 Table Orders

Table orders are for walk-in guests (no registration needed).

**Using Collection Runner:**

1. Click on collection again
2. Click **"Run"** button
3. Configure:
   - **Iterations:** `100`
   - **Delay:** `50ms`
   - **Select Requests:** ✓ Only check:
     - ✓ 4. Create Table Order (Walk-in)
4. Click **"Run Restaurant Load Test - 250 Orders"**
5. Wait for completion (~2-3 minutes)

**What happens per iteration:**
1. Generates random guest name and phone
2. Assigns random table number (Table-1 to Table-50)
3. Places order with 1-4 random menu items
4. No login required (guest checkout)

## Expected Results

After both runs complete, you should have:

### In Database:
- **250 orders total** in `orders` table
- **150 customer accounts** in `users` table (role: CUSTOMER)
- **Order items** distributed across menu items
- Mix of `PENDING`, `CONFIRMED` statuses

### Order Distribution:
- **150 ONLINE orders** with:
  - `order_type = 'ONLINE'`
  - `customer_email` populated
  - `delivery_address` populated
  - Registered customer accounts

- **100 TABLE orders** with:
  - `order_type = 'TABLE'`
  - `table_id` populated
  - `customer_name` and `customer_phone` (guests)
  - No customer account (anonymous)

### Analytics Impact:
This data is perfect for testing your analytics dashboards:
- Revenue trends over time
- Popular menu items analysis
- Order type breakdown (Table vs Online)
- Customer preference tracking
- Demand forecasting (ML predictions need 90+ days)

## Verify Results

### Check Database:

```bash
# SSH into postgres pod
kubectl exec -n restaurant-system postgres-0 -- psql -U restaurant_admin -d restaurant_db

# Count total orders
SELECT order_type, COUNT(*) FROM orders GROUP BY order_type;

# Count customers created
SELECT COUNT(*) FROM users WHERE role = 'CUSTOMER';

# Top selling items
SELECT mi.name, COUNT(*) as order_count
FROM order_items oi
JOIN menu_items mi ON oi.menu_item_id = mi.id
GROUP BY mi.name
ORDER BY order_count DESC
LIMIT 10;
```

### Check Analytics Dashboard:

1. Login as restaurant admin: `adminres@restaurant.com`
2. Navigate to **Analytics Dashboard**
3. You should see:
   - Revenue spike
   - 250 orders in order volume
   - Popular items with high counts
   - Order type breakdown (60% online, 40% table)

## Customization

### Change Restaurant

Edit in environment:
```json
{
  "key": "restaurant_id",
  "value": "YOUR-RESTAURANT-UUID-HERE"
}
```

### Adjust Order Quantities

Edit Pre-request Scripts in requests:
- **Online orders**: `const itemCount = Math.floor(Math.random() * 4) + 1;` (1-5 items)
- **Table orders**: `const itemCount = Math.floor(Math.random() * 3) + 1;` (1-4 items)

### Add More Variety

Edit Pre-request Scripts to include:
- More special instructions
- Different delivery addresses
- Varied order times (add delays)
- Different payment methods

## Tips for Large-Scale Testing

### For 1000+ Orders:

1. **Increase iterations** in Collection Runner
2. **Reduce delay** to 10ms for faster execution
3. **Disable "Save Responses"** to save memory
4. **Monitor database** performance during load

### For Time-Series Data:

To test ML predictions and trends, spread orders over time:

1. Create multiple runs with different dates
2. Manually update `created_at` in database:
   ```sql
   UPDATE orders
   SET created_at = created_at - INTERVAL '30 days'
   WHERE id IN (SELECT id FROM orders ORDER BY RANDOM() LIMIT 50);
   ```
3. This simulates historical data for forecasting

## Troubleshooting

### "Menu items not found"
- Run **"Setup - Get Menu Items"** first
- Verify restaurant has menu items in database

### "Registration failed"
- Email already exists (very rare with timestamp)
- Check auth-service logs: `kubectl logs -n restaurant-system -l app=auth-service`

### "Order creation failed"
- Invalid menu_item_id (menu changed during run)
- Re-run Setup to refresh menu items
- Check order-service logs: `kubectl logs -n restaurant-system -l app=order-service`

### Runner stuck/slow
- Reduce iterations
- Increase delay between requests
- Close other Postman tabs
- Check API server is responsive

## Advanced: Newman CLI

Run collections from command line (CI/CD):

```bash
# Install Newman
npm install -g newman

# Run online orders
newman run Restaurant_Load_Test.postman_collection.json \
  -e Restaurant_Local.postman_environment.json \
  -n 150 \
  --folder "1. Register Online Customer" \
  --folder "2. Login Online Customer" \
  --folder "3. Create Online Order"

# Run table orders
newman run Restaurant_Load_Test.postman_collection.json \
  -e Restaurant_Local.postman_environment.json \
  -n 100 \
  --folder "4. Create Table Order (Walk-in)"
```

## What's Next?

After generating load test data:

1. **Test Analytics Endpoints** - Verify all analytics queries return correct data
2. **Test ML Predictions** - Requires 90+ days of data (use time manipulation)
3. **Performance Testing** - Measure query response times with large dataset
4. **Dashboard Testing** - Ensure charts render with 250+ orders
5. **Chef Dashboard** - Verify orders appear in kitchen display

## Support

For issues or questions:
- Check Postman Console for detailed logs
- Review Pre-request Script outputs
- Check Test script assertions
- Verify environment variables are set correctly
