# ML Prediction Testing Guide

Complete workflow to test ML demand forecasting with realistic 2-month historical data.

## 🎯 Goal

Test how well ML predictions work by:
1. Creating realistic menu (50 items)
2. Generating 2 months of orders with weekend peaks (200 orders)
3. Processing all orders through chef workflow (10 cancellations)
4. Verifying revenue dashboard updates
5. Testing ML prediction accuracy

---

## 📋 Collections

### 1. Menu Setup (Run Once)
**File:** `1_Menu_Setup.postman_collection.json`

**What it does:**
- Creates 50 diverse menu items:
  - 10 Appetizers ($6-$13)
  - 15 Main Courses ($14-$32)
  - 10 Side Dishes ($4-$8)
  - 8 Desserts ($6-$9)
  - 7 Beverages ($3-$6)

**How to run:**
```
1. Import collection
2. Run "Setup - Login as Restaurant Admin" once
3. Collection Runner → 50 iterations
4. Check: kubectl exec postgres-0 -- psql ...
   SELECT category, COUNT(*) FROM menu_items GROUP BY category;
```

**Expected result:** 50 menu items created

---

### 2. Historical Orders - 2 Months (Single Run)
**File:** `2_Historical_Orders_2_Months.postman_collection.json`

**What it does:**
- Creates 200 orders spread over 60 days (2 months)
- **Friday/Saturday peak:** More orders on weekends
- **Mix:** 50% table orders, 50% online orders
- **Variety:** 1-5 items per order (weekends larger)
- **Different customers:** Random names, phones, emails

**Distribution:**
- **Weekdays:** 2-4 orders/day
- **Fridays:** 6-8 orders
- **Saturdays:** 8-10 orders
- **Sundays:** 4-6 orders

**How to run:**
```
1. Import collection
2. Run "Setup - Fetch Menu Items" ONCE (loads menu)
3. Collection Runner → 200 iterations
   - Delay: 50ms
   - Data: None (auto-generated)
4. Wait ~5 minutes
5. Note: Orders created with current timestamp (will fix dates next)
```

**Expected result:** ~200 orders created

---

### 3. Process Orders - Chef Workflow
**File:** `3_Process_Orders_Chef.postman_collection.json`

**What it does:**
- Chef logs in
- Fetches all pending orders
- Processes each order:
  - **190 orders:** PENDING → CONFIRMED → PREPARING → READY → SERVED
  - **10 orders:** CANCELLED (spread evenly)
- Updates revenue for completed orders

**How to run:**
```
1. Import collection
2. Run "Setup - Login as Chef" ONCE
3. Run "Get Pending Orders" ONCE (fetches all)
4. Collection Runner → 200+ iterations
   - Will auto-stop after processing all orders
   - Delay: 30ms
5. Check console for progress
```

**Expected result:**
- 190 SERVED orders
- 10 CANCELLED orders
- Revenue updated in analytics dashboard

---

## 🚀 Complete Workflow

### Step 1: Setup Menu (One Time)

```bash
# In Postman:
1. Import: 1_Menu_Setup.postman_collection.json
2. Select "Restaurant Local Environment"
3. Run request: "Setup - Login as Restaurant Admin"
4. Open Collection Runner
5. Select: "Create Menu Item"
6. Iterations: 50
7. Delay: 100ms
8. Run
```

**Verify:**
```sql
kubectl exec -n restaurant-system postgres-0 -- \
  psql -U restaurant_admin -d restaurant_db \
  -c "SELECT category, COUNT(*), AVG(price) FROM menu_items WHERE restaurant_id = '73332393-3c58-47c1-b58e-6d2ab59e96bb' GROUP BY category;"
```

Expected output:
```
   category   | count | avg
--------------+-------+------
 APPETIZER    |    10 | 9.50
 MAIN_COURSE  |    15 | 20.00
 SIDE_DISH    |    10 | 5.80
 DESSERT      |     8 | 7.75
 BEVERAGE     |     7 | 4.50
```

---

### Step 2: Generate 2 Months of Orders

```bash
# In Postman:
1. Import: 2_Historical_Orders_2_Months.postman_collection.json
2. Run request: "Setup - Fetch Menu Items" ONCE
   (Stores menu items in environment variable)
3. Open Collection Runner
4. Select: "Create Historical Order"
5. Iterations: 200
6. Delay: 50ms
7. Run
```

**Console output example:**
```
✓ Loaded 50 menu items
1/200: Fri 2025-10-27 🛒 Online - 3 items - Sarah Johnson
2/200: Thu 2025-10-26 🍽️ Table - 2 items - John Smith
3/200: Wed 2025-10-25 🛒 Online - 2 items - Mike Davis
...
150/200: Sat 2025-12-06 🛒 Online - 5 items - Emily Wilson (WEEKEND PEAK)
```

**Verify:**
```sql
kubectl exec -n restaurant-system postgres-0 -- \
  psql -U restaurant_admin -d restaurant_db \
  -c "SELECT DATE(created_at), COUNT(*) FROM orders GROUP BY DATE(created_at) ORDER BY DATE(created_at) DESC LIMIT 10;"
```

**⚠️ Important:** Orders are created with current timestamp. We need to backdate them.

---

### Step 3: Backdate Orders to Historical Dates

After creating orders, update their `created_at` timestamps to spread over 2 months:

```sql
# Connect to postgres
kubectl exec -it -n restaurant-system postgres-0 -- \
  psql -U restaurant_admin -d restaurant_db

# Backdate orders to create 2-month history
DO $$
DECLARE
    order_record RECORD;
    days_back INTEGER;
    counter INTEGER := 0;
    total_orders INTEGER;
BEGIN
    -- Get total orders
    SELECT COUNT(*) INTO total_orders FROM orders WHERE restaurant_id = '73332393-3c58-47c1-b58e-6d2ab59e96bb';

    -- Loop through orders and backdate
    FOR order_record IN
        SELECT id, created_at
        FROM orders
        WHERE restaurant_id = '73332393-3c58-47c1-b58e-6d2ab59e96bb'
        ORDER BY created_at ASC
    LOOP
        counter := counter + 1;

        -- Calculate days back (spread over 60 days)
        days_back := 60 - (counter * 60 / total_orders)::INTEGER;

        -- Update order timestamp
        UPDATE orders
        SET created_at = CURRENT_TIMESTAMP - (days_back || ' days')::INTERVAL
        WHERE id = order_record.id;

        -- Also update order items
        UPDATE order_items
        SET created_at = CURRENT_TIMESTAMP - (days_back || ' days')::INTERVAL
        WHERE order_id = order_record.id;
    END LOOP;

    RAISE NOTICE 'Updated % orders to span 60 days', total_orders;
END $$;
```

**Verify spread:**
```sql
SELECT
    DATE(created_at) as order_date,
    EXTRACT(DOW FROM created_at) as day_of_week, -- 0=Sun, 5=Fri, 6=Sat
    COUNT(*) as order_count
FROM orders
WHERE restaurant_id = '73332393-3c58-47c1-b58e-6d2ab59e96bb'
GROUP BY DATE(created_at), EXTRACT(DOW FROM created_at)
ORDER BY order_date DESC
LIMIT 30;
```

**Expected:** Fridays (5) and Saturdays (6) should have 2-3x more orders than weekdays.

---

### Step 4: Process Orders (Chef Workflow)

```bash
# In Postman:
1. Import: 3_Process_Orders_Chef.postman_collection.json
2. Run: "Setup - Login as Chef" ONCE
3. Run: "Get Pending Orders" ONCE
   (Check console: should show ~200 orders found)
4. Open Collection Runner
5. Select: "Process Order (Accept/Complete/Cancel)"
6. Iterations: 210 (buffer for processing)
7. Delay: 30ms
8. Run
```

**Console output:**
```
✓ Chef logged in successfully
✓ Found 200 pending orders to process
1/200: ✓ Completing order abc123...
  ✓ Order completed successfully
10/200: ❌ Cancelling order def456...
  ✓ Order cancelled (1/10 cancellations)
...
200/200: ✓ Completing order xyz789...
  ✓ Order completed successfully
All orders processed!
```

**Verify:**
```sql
kubectl exec -n restaurant-system postgres-0 -- \
  psql -U restaurant_admin -d restaurant_db \
  -c "SELECT status, COUNT(*) FROM orders WHERE restaurant_id = '73332393-3c58-47c1-b58e-6d2ab59e96bb' GROUP BY status;"
```

Expected:
```
  status   | count
-----------+-------
 SERVED    |   190
 CANCELLED |    10
```

---

### Step 5: Verify Analytics Dashboard

**Login to dashboard:**
```
URL: http://restaurant.corpv3.com/admin/analytics
User: adminres@restaurant.com
Password: admin123
```

**What you should see:**

1. **Revenue Overview:**
   - Total revenue from 190 completed orders
   - Average order value
   - Order count by date (with Friday/Saturday peaks)

2. **Order Volume Trends:**
   - Graph showing 2-month history
   - Clear weekend spikes

3. **Popular Items:**
   - Top 10 items by revenue
   - Top 10 by quantity sold

4. **Category Performance:**
   - Main courses should have highest revenue
   - Beverages highest order frequency

5. **Order Type Breakdown:**
   - ~50% TABLE
   - ~50% ONLINE

**SQL Verification:**
```sql
-- Total revenue (SERVED orders only)
SELECT
    SUM(total) as total_revenue,
    COUNT(*) as completed_orders,
    AVG(total) as avg_order_value
FROM orders
WHERE restaurant_id = '73332393-3c58-47c1-b58e-6d2ab59e96bb'
AND status = 'SERVED';

-- Weekend vs Weekday revenue
SELECT
    CASE
        WHEN EXTRACT(DOW FROM created_at) IN (5, 6) THEN 'Weekend'
        ELSE 'Weekday'
    END as period,
    COUNT(*) as orders,
    SUM(total) as revenue
FROM orders
WHERE restaurant_id = '73332393-3c58-47c1-b58e-6d2ab59e96bb'
AND status = 'SERVED'
GROUP BY period;

-- Top selling items
SELECT
    mi.name,
    mi.category,
    SUM(oi.quantity) as total_quantity,
    COUNT(DISTINCT oi.order_id) as order_count,
    SUM(oi.quantity * oi.item_price) as revenue
FROM order_items oi
JOIN menu_items mi ON oi.menu_item_id = mi.id
JOIN orders o ON oi.order_id = o.id
WHERE o.restaurant_id = '73332393-3c58-47c1-b58e-6d2ab59e96bb'
AND o.status = 'SERVED'
GROUP BY mi.id, mi.name, mi.category
ORDER BY revenue DESC
LIMIT 10;
```

---

### Step 6: Test ML Predictions

Now with 2 months of historical data, test the prediction endpoints:

**Navigate to Predictions Dashboard:**
```
URL: http://restaurant.corpv3.com/admin/predictions
User: adminres@restaurant.com
```

**Test different prediction periods:**

1. **1 Week Prediction:**
   - Select: "1 Week"
   - Click: Fetch predictions
   - Wait: 10-30 seconds (first time training)
   - Result: 7 days of predictions with confidence intervals

2. **2 Weeks Prediction:**
   - Select: "2 Weeks"
   - Fetch predictions
   - Result: 14 days forecast (instant from cache)

3. **1 Month Prediction:**
   - Select: "1 Month"
   - Fetch predictions
   - Result: 30 days forecast

**What to validate:**

✅ **Predictions show weekend peaks**
- Friday predictions should be higher than Monday-Thursday
- Saturday predictions should be highest
- Confidence intervals should be reasonable (±20-30%)

✅ **Popular items have higher predictions**
- Items ordered frequently in history get higher predictions
- Seasonal patterns detected

✅ **Performance**
- First request: 10-30 seconds (model training)
- Cached requests: <100ms
- No errors in console

**API Testing (Postman):**
```
GET {{base_url}}/api/v1/restaurants/{{restaurant_id}}/analytics/predictions/demand?period=2_weeks

Response:
{
  "restaurant_id": "...",
  "period": "2_weeks",
  "days_ahead": 14,
  "predictions": [
    {
      "date": "2025-12-28",
      "menu_item_id": "...",
      "item_name": "Grilled Salmon",
      "predicted_quantity": 12,
      "confidence_lower": 8,
      "confidence_upper": 16,
      "confidence_level": 0.8
    },
    ...
  ],
  "cached": false,
  "model_training_time": 15.3
}
```

---

## 🧪 Expected ML Behavior

### ✅ Good Predictions (What Should Happen)

1. **Weekend Peaks Detected:**
   - Friday predictions 50-100% higher than weekdays
   - Saturday predictions 100-150% higher
   - Model learns this from 8 weekends of data

2. **Item Popularity:**
   - Popular items (ordered 30+ times) get higher predictions
   - Rare items (ordered <5 times) get lower predictions
   - Main courses predicted more than desserts

3. **Trend Detection:**
   - If an item's popularity grew over 2 months, prediction trend up
   - If declining, prediction trend down

4. **Confidence Intervals:**
   - High-volume items: Narrow intervals (±15%)
   - Low-volume items: Wide intervals (±40%)
   - Weekday predictions: More confident
   - Weekend predictions: Less confident (higher variance)

### ⚠️ What Might Not Work (Expected Limitations)

1. **Short History:**
   - 2 months is minimum for Prophet
   - Longer history (6+ months) would be more accurate
   - Yearly seasonality requires 2+ years

2. **Small Sample Size:**
   - 200 orders total = ~3 orders/day average
   - Prophet works better with 10+ orders/day
   - Low-volume items may have poor predictions

3. **No External Factors:**
   - Weather, holidays, events not included
   - Model only knows historical patterns

4. **First Month Accuracy:**
   - First 30 days may have less accurate predictions
   - Model needs to "warm up" with more data

---

## 📊 Validation Checklist

### Menu Setup ✓
- [ ] 50 menu items created
- [ ] 5 categories represented
- [ ] Price range $3-$32
- [ ] All items available

### Historical Orders ✓
- [ ] ~200 orders created
- [ ] Spread over 60 days
- [ ] Weekend peaks visible
- [ ] 50/50 table/online split
- [ ] Multiple items per order

### Order Processing ✓
- [ ] 190 orders SERVED
- [ ] 10 orders CANCELLED
- [ ] Revenue calculated
- [ ] All items accounted

### Analytics Dashboard ✓
- [ ] Revenue chart shows 2-month trend
- [ ] Weekend spikes visible
- [ ] Popular items ranked correctly
- [ ] Category breakdown accurate
- [ ] Order type split ~50/50

### ML Predictions ✓
- [ ] 1-week prediction works
- [ ] 2-week prediction works
- [ ] Weekend peaks in predictions
- [ ] Confidence intervals reasonable
- [ ] Cache works (fast 2nd request)
- [ ] No errors in browser console

---

## 🐛 Troubleshooting

### "No menu items found"
**Fix:** Run Collection 1 (Menu Setup) first

### "Insufficient data for predictions"
**Fix:**
1. Check you have 60+ days of data
2. Run SQL to verify: `SELECT MIN(created_at), MAX(created_at) FROM orders;`
3. Re-run backdating SQL script

### "Predictions all the same"
**Fix:**
1. Ensure weekend peaks exist in data
2. Check: `SELECT EXTRACT(DOW FROM created_at), COUNT(*) FROM orders GROUP BY 1;`
3. Day 5 (Fri) and 6 (Sat) should have more orders

### "Model training too slow (>60 seconds)"
**Fix:**
1. Check order-service pod resources
2. Increase CPU: `kubectl set resources deployment order-service --limits=cpu=2`
3. Check logs: `kubectl logs -n restaurant-system -l app=order-service`

### "Analytics dashboard shows wrong dates"
**Fix:**
1. Hard refresh browser: Ctrl+Shift+F5
2. Check timezone: Browser should match server
3. Verify order dates in database

---

## 🎯 Success Metrics

After completing all steps, you should achieve:

- ✅ **200 orders** spanning 2 months
- ✅ **Friday/Saturday peaks** 2-3x higher than weekdays
- ✅ **190 completed, 10 cancelled** orders
- ✅ **Revenue dashboard** showing accurate trends
- ✅ **ML predictions** completing in <30 seconds
- ✅ **Weekend predictions** higher than weekday
- ✅ **Popular items** predicted with 70-85% accuracy
- ✅ **Confidence intervals** within reasonable range

---

## 📝 Notes

- Collections are designed to run in sequence (1 → 2 → 3)
- Total time: ~15-20 minutes for all steps
- Database backdating required for realistic time-series
- ML training time depends on CPU (10-30 seconds typical)
- Cache makes subsequent predictions instant (<100ms)
- Perfect for testing Prophet ML algorithm effectiveness

---

**Next Steps:**
- Generate more historical data (400+ orders)
- Extend to 6 months for better accuracy
- Test different prediction periods (3 months, 6 months)
- Compare predictions vs actual new orders
- Fine-tune Prophet parameters for your data
